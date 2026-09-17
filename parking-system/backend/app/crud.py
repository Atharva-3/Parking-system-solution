"""Business logic: slot allocation, fee calculation, check-in/out.
Kept separate from the API layer (main.py) so it's independently
unit-testable and so the rules are all in one place."""
import math
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models

from . import models


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
        entry_time=datetime.now(timezone.utc).replace(tzinfo=None),
        status=models.TicketStatus.active,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def check_out(db: Session, plate: str) -> tuple[models.Ticket, int, float]:
    plate = normalize_plate(plate)
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )
    if ticket is None:
        raise TicketNotFound(f"No active ticket found for plate '{plate}'")

    pricing = get_pricing(db)
    exit_time = datetime.now(timezone.utc).replace(tzinfo=None)
    hours, fee = calculate_fee(ticket.entry_time, exit_time, pricing)

    ticket.exit_time = exit_time
    ticket.amount_charged = fee
    ticket.status = models.TicketStatus.closed

    slot = db.get(models.Slot, ticket.slot_id)
    slot.is_occupied = False

    db.commit()
    db.refresh(ticket)
    return ticket, hours, fee


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
    return check_out(db, ticket.plate)


def search_by_plate(db: Session, plate: str) -> Optional[models.Ticket]:
    plate = normalize_plate(plate)
    return (
        db.query(models.Ticket)
        .filter(models.Ticket.plate == plate, models.Ticket.status == models.TicketStatus.active)
        .first()
    )


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
