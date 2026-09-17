"""Business logic: slot allocation, fee calculation, check-in/out.
Kept separate from the API layer (main.py) so it's independently
unit-testable and so the rules are all in one place."""
import math
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models

CURRENT_CLOCK = None


class NoSlotAvailable(Exception):
    pass


class PlateAlreadyParked(Exception):
    pass


class TicketNotFound(Exception):
    pass


class SlotNotFound(Exception):
    pass


class SlotOccupied(Exception):
    pass


class SlotTypeMismatch(Exception):
    pass


# Overflow rule: a vehicle may use its own type, or any type listed after
# it here (never a stricter one). EV vehicles are never allowed to overflow
# into non-EV slots (they need the charger), and non-EV slots never accept
# an EV. Compact cars may overflow into Standard if Compact is full.
OVERFLOW_ORDER = {
    models.SlotType.compact: [models.SlotType.compact, models.SlotType.standard],
    models.SlotType.standard: [models.SlotType.standard],
    models.SlotType.ev: [models.SlotType.ev],
}


def set_current_time(value=None):
    global CURRENT_CLOCK
    if value is None:
        CURRENT_CLOCK = None
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    CURRENT_CLOCK = value
    return value


def get_current_time() -> datetime:
    if CURRENT_CLOCK is not None:
        return CURRENT_CLOCK
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_pricing(db: Session) -> models.PricingRule:
    rule = db.query(models.PricingRule).first()
    if rule is None:
        rule = models.PricingRule()
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return rule


def calculate_fee(entry_time: datetime, exit_time: datetime, pricing: models.PricingRule) -> tuple[int, float]:
    """Part-hours round up. First hour flat, each extra hour a smaller add-on,
    never exceeding the daily cap."""
    seconds = max((exit_time - entry_time).total_seconds(), 0)
    hours = max(1, math.ceil(seconds / 3600))
    fee = pricing.first_hour_rate + max(0, hours - 1) * pricing.additional_hour_rate
    fee = min(fee, pricing.daily_cap)
    return hours, round(fee, 2)


def _parse_money(raw) -> float:
    if raw is None:
        raise ValueError("missing value")
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        text = str(raw).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            raise ValueError("empty value")
        if text.startswith("(") and text.endswith(")"):
            text = f"-{text[1:-1]}"
        text = text.replace("$", "").replace(",", "").replace(" ", "")
        try:
            value = float(text)
        except ValueError as exc:
            raise ValueError(f"invalid numeric value: {raw!r}") from exc
    if abs(value) > 1000:
        value = value / 100.0
    return float(value)


def normalize_rate_card(raw_rows) -> tuple[dict[models.SlotType, dict[str, float]], list[str]]:
    """Normalize dirty input into a consistent per-slot-type rate map."""
    cleaned: dict[models.SlotType, dict[str, float]] = {}
    warnings: list[str] = []
    alias_map = {
        "compact": models.SlotType.compact,
        "standard": models.SlotType.standard,
        "ev": models.SlotType.ev,
    }

    for index, row in enumerate(raw_rows or []):
        if not isinstance(row, dict):
            warnings.append(f"Row {index}: skipped non-dictionary payload")
            continue

        type_token = (
            row.get("spot_type")
            or row.get("slot_type")
            or row.get("type")
            or row.get("vehicle_type")
            or ""
        )
        normalized_key = str(type_token).strip().lower()
        slot_type = alias_map.get(normalized_key)
        if slot_type is None:
            warnings.append(f"Row {index}: unknown spot type '{type_token}' skipped")
            continue
        if slot_type in cleaned:
            warnings.append(f"Row {index}: duplicate rate for {slot_type.value}; keeping first valid row")
            continue

        try:
            first_hour = _parse_money(row.get("first_hour") or row.get("first_hour_rate") or row.get("first_hour_price"))
            extra_hour = _parse_money(row.get("extra_hour") or row.get("additional_hour") or row.get("extra_hour_rate") or row.get("additional_hour_rate"))
            daily_cap = _parse_money(row.get("daily_cap") or row.get("cap") or row.get("daily_limit"))
            if first_hour <= 0 or extra_hour < 0 or daily_cap <= 0:
                raise ValueError("rates must be positive")
        except ValueError as exc:
            warnings.append(f"Row {index}: invalid rate values for {slot_type.value}: {exc}")
            continue

        cleaned[slot_type] = {
            "first_hour_rate": round(first_hour, 2),
            "additional_hour_rate": round(extra_hour, 2),
            "daily_cap": round(daily_cap, 2),
        }

    return cleaned, warnings


def apply_cleaned_rates(db: Session, raw_rows) -> tuple[dict[models.SlotType, dict[str, float]], list[str]]:
    cleaned, warnings = normalize_rate_card(raw_rows)
    if not cleaned:
        raise ValueError("No valid rate rows were provided")
    first = next(iter(cleaned.values()))
    rule = get_pricing(db)
    rule.first_hour_rate = first["first_hour_rate"]
    rule.additional_hour_rate = first["additional_hour_rate"]
    rule.daily_cap = first["daily_cap"]
    db.commit()
    db.refresh(rule)
    return cleaned, warnings


def slot_accepts_vehicle(slot_type: models.SlotType, vehicle_type: models.SlotType) -> bool:
    return slot_type in OVERFLOW_ORDER[vehicle_type]


def find_available_slot(db: Session, vehicle_type: models.SlotType) -> Optional[models.Slot]:
    for candidate_type in OVERFLOW_ORDER[vehicle_type]:
        slot = (
            db.query(models.Slot)
            .filter(models.Slot.type == candidate_type, models.Slot.is_occupied.is_(False))
            .order_by(models.Slot.level, models.Slot.code)
            .first()
        )
        if slot:
            return slot
    return None


def resolve_slot(db: Session, vehicle_type: models.SlotType, slot_id: Optional[int] = None) -> models.Slot:
    if slot_id is None:
        slot = find_available_slot(db, vehicle_type)
        if slot is None:
            raise NoSlotAvailable(f"No free slot available for vehicle type '{vehicle_type.value}'")
        return slot

    slot = db.get(models.Slot, slot_id)
    if slot is None:
        raise SlotNotFound(f"Slot {slot_id} does not exist")
    if slot.is_occupied:
        raise SlotOccupied(f"Slot {slot.code} is already occupied")
    if not slot_accepts_vehicle(slot.type, vehicle_type):
        raise SlotTypeMismatch(
            f"A {vehicle_type.value} vehicle cannot park in {slot.type.value} slot {slot.code}"
        )
    return slot


def normalize_plate(plate: str) -> str:
    return plate.strip().upper().replace(" ", "")


def check_in(
    db: Session,
    plate: str,
    vehicle_type: models.SlotType,
    slot_id: Optional[int] = None,
) -> models.Ticket:
    plate = normalize_plate(plate)
    existing = (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )
    if existing:
        raise PlateAlreadyParked(f"{plate} is already checked in (ticket #{existing.id})")

    slot = resolve_slot(db, vehicle_type, slot_id)

    slot.is_occupied = True
    ticket = models.Ticket(
        plate=plate,
        vehicle_type=vehicle_type,
        slot_id=slot.id,
        entry_time=get_current_time(),
        status=models.TicketStatus.active,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def close_ticket(db: Session, ticket: models.Ticket, exit_time: Optional[datetime] = None) -> tuple[models.Ticket, int, float]:
    if exit_time is None:
        exit_time = get_current_time()
    pricing = get_pricing(db)
    hours, fee = calculate_fee(ticket.entry_time, exit_time, pricing)

    ticket.exit_time = exit_time
    ticket.amount_charged = fee
    ticket.status = models.TicketStatus.closed

    slot = db.get(models.Slot, ticket.slot_id)
    if slot is not None:
        slot.is_occupied = False

    db.commit()
    db.refresh(ticket)
    return ticket, hours, fee


def check_out(db: Session, plate: str) -> tuple[models.Ticket, int, float]:
    plate = normalize_plate(plate)
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )
    if ticket is None:
        raise TicketNotFound(f"No active ticket found for plate '{plate}'")

    return close_ticket(db, ticket, get_current_time())


def active_ticket_for_slot(db: Session, slot_id: int) -> Optional[models.Ticket]:
    return (
        db.query(models.Ticket)
        .filter(models.Ticket.slot_id == slot_id, models.Ticket.status == models.TicketStatus.active)
        .first()
    )


def check_out_slot(db: Session, slot_id: int) -> tuple[models.Ticket, int, float]:
    """Sensor-style exit: the slot went vacant, so close the ticket parked there."""
    slot = db.get(models.Slot, slot_id)
    if slot is None:
        raise SlotNotFound(f"Slot {slot_id} does not exist")
    ticket = active_ticket_for_slot(db, slot_id)
    if ticket is None:
        raise TicketNotFound(f"No active ticket in slot {slot.code}")
    return close_ticket(db, ticket, get_current_time())


def search_by_plate(db: Session, plate: str) -> Optional[models.Ticket]:
    plate = normalize_plate(plate)
    return (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )


def transfer_plate(db: Session, current_plate: str, new_plate: str) -> models.Ticket:
    current_plate = normalize_plate(current_plate)
    new_plate = normalize_plate(new_plate)
    if not current_plate or not new_plate:
        raise ValueError("Both plate values are required")
    if current_plate == new_plate:
        ticket = search_by_plate(db, current_plate)
        if ticket is None:
            raise TicketNotFound(f"No active ticket found for plate '{current_plate}'")
        return ticket

    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == current_plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )
    if ticket is None:
        raise TicketNotFound(f"No active ticket found for plate '{current_plate}'")

    conflict = (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == new_plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )
    if conflict is not None and conflict.id != ticket.id:
        raise PlateAlreadyParked(f"{new_plate} is already checked in")

    ticket.plate = new_plate
    db.commit()
    db.refresh(ticket)
    return ticket


def auto_close_overdue_sessions(db: Session, now: Optional[datetime] = None) -> list[models.Ticket]:
    if now is None:
        now = get_current_time()

    overdue = [
        ticket
        for ticket in db.query(models.Ticket)
        .filter(models.Ticket.status == models.TicketStatus.active)
        .all()
        if now - ticket.entry_time >= timedelta(hours=24)
    ]
    for ticket in overdue:
        close_ticket(db, ticket, now)
    return overdue


def get_day_report(db: Session, day: Optional[datetime.date] = None) -> dict:
    if day is None:
        day = get_current_time().date()

    tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.status == models.TicketStatus.closed)
        .all()
    )
    selected = []
    for ticket in tickets:
        if ticket.exit_time is None:
            continue
        if ticket.exit_time.date() == day:
            selected.append(ticket)

    cars_by_type = {slot_type.value: 0 for slot_type in models.SlotType}
    per_car = {}
    total_profit = 0.0

    for ticket in selected:
        cars_by_type[ticket.vehicle_type.value] = cars_by_type.get(ticket.vehicle_type.value, 0) + 1
        amount = float(ticket.amount_charged or 0)
        per_car[ticket.plate] = {
            "plate": ticket.plate,
            "vehicle_type": ticket.vehicle_type.value,
            "entry_time": ticket.entry_time.isoformat(),
            "exit_time": ticket.exit_time.isoformat() if ticket.exit_time else None,
            "amount_charged": round(amount, 2),
        }
        total_profit += amount

    return {
        "date": day.isoformat(),
        "total_cars": len(selected),
        "cars_by_type": cars_by_type,
        "per_car": per_car,
        "total_profit": round(total_profit, 2),
    }


def get_dashboard(db: Session) -> dict:
    categories = []
    for slot_type in models.SlotType:
        total = db.query(models.Slot).filter(models.Slot.type == slot_type).count()
        occupied = (
            db.query(models.Slot)
            .filter(models.Slot.type == slot_type, models.Slot.is_occupied.is_(True))
            .count()
        )
        categories.append(
            {"type": slot_type, "total": total, "free": total - occupied, "occupied": occupied}
        )
    active_tickets = db.query(models.Ticket).filter(models.Ticket.status == models.TicketStatus.active).count()
    profit_earned = (
        db.query(func.sum(models.Ticket.amount_charged))
        .filter(models.Ticket.status == models.TicketStatus.closed)
        .scalar()
    ) or 0.0
    return {
        "categories": categories,
        "total_active_tickets": active_tickets,
        "profit_earned": profit_earned
    }
