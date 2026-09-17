"""Sanity tests for allocation, fee calc, and the check-in/out flow.
Run with: pytest -q"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_parking.db")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.database import Base, engine, SessionLocal
from app import models, crud
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Slot(code="C-01", level=1, type=models.SlotType.compact))
    db.add(models.Slot(code="S-01", level=1, type=models.SlotType.standard))
    db.add(models.Slot(code="E-01", level=1, type=models.SlotType.ev))
    db.add(models.PricingRule())
    db.commit()
    db.close()
    yield


def test_fee_calculation_tiers_and_cap():
    pricing = models.PricingRule(first_hour_rate=50, additional_hour_rate=10, daily_cap=300)
    entry = datetime(2026, 1, 1, 10, 0, 0)

    # exactly 1 hour -> just the flat fee
    hours, fee = crud.calculate_fee(entry, entry + timedelta(minutes=59), pricing)
    assert hours == 1 and fee == 50

    # 61 minutes rounds up to 2 hours
    hours, fee = crud.calculate_fee(entry, entry + timedelta(minutes=61), pricing)
    assert hours == 2 and fee == 60

    # long stay hits the cap
    hours, fee = crud.calculate_fee(entry, entry + timedelta(hours=40), pricing)
    assert fee == 300


def test_ev_must_get_ev_slot():
    r = client.post("/checkin", json={"plate": "rj14ab1234", "vehicle_type": "ev"})
    assert r.status_code == 201
    assert r.json()["slot_code"] == "E-01"


def test_compact_overflows_to_standard_when_compact_full():
    client.post("/checkin", json={"plate": "AA01", "vehicle_type": "compact"})  # fills C-01
    r = client.post("/checkin", json={"plate": "AA02", "vehicle_type": "compact"})
    assert r.status_code == 201
    assert r.json()["slot_code"] == "S-01"  # overflowed


def test_standard_never_overflows_into_compact():
    client.post("/checkin", json={"plate": "BB01", "vehicle_type": "standard"})  # fills S-01
    r = client.post("/checkin", json={"plate": "BB02", "vehicle_type": "standard"})
    assert r.status_code == 409


def test_full_checkin_checkout_flow():
    client.post("/checkin", json={"plate": "MH12XY9999", "vehicle_type": "compact"})
    r = client.get("/search", params={"plate": "MH12XY9999"})
    assert r.status_code == 200

    r = client.post("/checkout", params={"plate": "MH12XY9999"})
    assert r.status_code == 200
    assert r.json()["amount"] >= 50

    # slot should be free again
    r = client.get("/slots", params={"type": "compact"})
    assert r.json()[0]["is_occupied"] is False
    assert r.json()[0]["active_ticket"] is None


def test_double_checkin_rejected():
    client.post("/checkin", json={"plate": "DUPLICATE1", "vehicle_type": "ev"})
    r = client.post("/checkin", json={"plate": "DUPLICATE1", "vehicle_type": "ev"})
    assert r.status_code == 409


def test_checkin_uses_clicked_slot():
    slots = client.get("/slots").json()
    standard = next(s for s in slots if s["type"] == "standard")
    r = client.post(
        "/checkin",
        json={"plate": "CLICK01", "vehicle_type": "compact", "slot_id": standard["id"]},
    )
    assert r.status_code == 201
    assert r.json()["slot_code"] == "S-01"


def test_ev_cannot_take_clicked_compact_slot():
    compact = next(s for s in client.get("/slots").json() if s["type"] == "compact")
    r = client.post(
        "/checkin",
        json={"plate": "EVBAD1", "vehicle_type": "ev", "slot_id": compact["id"]},
    )
    assert r.status_code == 409


def test_occupied_slot_includes_ticket():
    client.post("/checkin", json={"plate": "SEEN01", "vehicle_type": "ev"})
    ev = next(s for s in client.get("/slots").json() if s["type"] == "ev")
    assert ev["is_occupied"] is True
    assert ev["active_ticket"]["plate"] == "SEEN01"


def test_simulate_anpr_invents_plate_and_parks():
    r = client.post("/simulate/anpr", json={"vehicle_type": "standard"})
    assert r.status_code == 201
    assert r.json()["plate"]
    assert r.json()["slot_code"] == "S-01"


def test_simulate_sensor_exit_checks_out():
    client.post("/checkin", json={"plate": "SENS01", "vehicle_type": "compact"})
    compact = next(s for s in client.get("/slots").json() if s["code"] == "C-01")
    r = client.post("/simulate/sensor", json={"slot_id": compact["id"], "occupied": False})
    assert r.status_code == 200
    assert r.json()["amount"] >= 50
    compact = next(s for s in client.get("/slots").json() if s["code"] == "C-01")
    assert compact["is_occupied"] is False


def test_daily_log_summary_lists_vehicle_types_and_profit_for_a_day():
    day = datetime(2026, 9, 17)
    db = SessionLocal()
    db.add(models.Ticket(
        plate="CAR1",
        vehicle_type=models.SlotType.compact,
        slot_id=1,
        entry_time=day.replace(hour=9),
        exit_time=day.replace(hour=10),
        amount_charged=80,
        status=models.TicketStatus.closed,
    ))
    db.add(models.Ticket(
        plate="CAR2",
        vehicle_type=models.SlotType.standard,
        slot_id=2,
        entry_time=day.replace(hour=11),
        exit_time=day.replace(hour=12),
        amount_charged=100,
        status=models.TicketStatus.closed,
    ))
    db.add(models.Ticket(
        plate="CAR3",
        vehicle_type=models.SlotType.ev,
        slot_id=3,
        entry_time=day.replace(hour=13),
        exit_time=day.replace(hour=14),
        amount_charged=140,
        status=models.TicketStatus.closed,
    ))
    db.commit()
    summary = crud.get_day_report(db, day.date())
    db.close()

    assert summary["total_cars"] == 3
    assert summary["cars_by_type"]["compact"] == 1
    assert summary["cars_by_type"]["standard"] == 1
    assert summary["cars_by_type"]["ev"] == 1
    assert summary["total_profit"] == 320
    assert summary["per_car"]["CAR1"]["amount_charged"] == 80
    assert summary["per_car"]["CAR2"]["amount_charged"] == 100
    assert summary["per_car"]["CAR3"]["amount_charged"] == 140


def test_daily_report_and_alerts_endpoint():
    day = datetime(2026, 9, 17)
    db = SessionLocal()
    db.add(models.Ticket(
        plate="REPORT1",
        vehicle_type=models.SlotType.compact,
        slot_id=1,
        entry_time=day.replace(hour=9),
        exit_time=day.replace(hour=10),
        amount_charged=80,
        status=models.TicketStatus.closed,
    ))
    db.add(models.Ticket(
        plate="REPORT2",
        vehicle_type=models.SlotType.standard,
        slot_id=2,
        entry_time=day.replace(hour=11),
        exit_time=day.replace(hour=12),
        amount_charged=100,
        status=models.TicketStatus.closed,
    ))
    db.commit(); db.close()

    r = client.get("/daily-report", params={"date": day.date().isoformat()})
    assert r.status_code == 200
    payload = r.json()
    assert payload["total_cars"] == 2
    assert payload["total_profit"] == 180

    r = client.get("/alerts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_dirty_rate_card_is_normalized_and_bad_rows_skipped():
    raw = [
        {"spot_type": " Compact ", "first_hour": "$12.00", "extra_hour": "1200", "daily_cap": "300"},
        {"spot_type": "COMPACT", "first_hour": "12", "extra_hour": "4", "daily_cap": "250"},
        {"spot_type": "EV", "first_hour": "$14.00", "extra_hour": "700", "daily_cap": "420"},
        {"spot_type": "invalid", "first_hour": "NaN", "extra_hour": "9", "daily_cap": "180"},
        {"spot_type": "standard", "first_hour": "15", "extra_hour": "7.5", "daily_cap": "250"},
    ]

    cleaned, warnings = crud.normalize_rate_card(raw)
    assert models.SlotType.compact in cleaned
    assert cleaned[models.SlotType.compact]["first_hour_rate"] == 12.0
    assert cleaned[models.SlotType.compact]["additional_hour_rate"] == 12.0
    assert cleaned[models.SlotType.standard]["first_hour_rate"] == 15.0
    assert cleaned[models.SlotType.ev]["first_hour_rate"] == 14.0
    assert any("invalid" in str(w).lower() for w in warnings)


def test_clock_advance_auto_closes_sessions_over_24_hours():
    client.post("/checkin", json={"plate": "LATE1", "vehicle_type": "compact"})
    db = SessionLocal()
    ticket = db.query(models.Ticket).filter(models.Ticket.plate == "LATE1").first()
    ticket.entry_time = datetime.utcnow() - timedelta(hours=25)
    db.commit()
    db.close()

    r = client.post("/clock", json={"now": (datetime.utcnow() + timedelta(hours=1)).isoformat()})
    assert r.status_code == 200
    assert r.json()["closed_count"] >= 1
    assert client.get("/search", params={"plate": "LATE1"}).status_code == 404


def test_plate_transfer_keeps_session_alive_with_same_entry_time():
    r = client.post("/checkin", json={"plate": "ORIG1", "vehicle_type": "standard"})
    assert r.status_code == 201
    before = client.get("/search", params={"plate": "ORIG1"}).json()

    r = client.post("/transfer", json={"current_plate": "ORIG1", "new_plate": "NEW1"})
    assert r.status_code == 200
    assert r.json()["plate"] == "NEW1"
    assert r.json()["entry_time"] == before["entry_time"]

    assert client.get("/search", params={"plate": "ORIG1"}).status_code == 404
    assert client.get("/search", params={"plate": "NEW1"}).status_code == 200
    slot = next(s for s in client.get("/slots").json() if s["active_ticket"] is not None)
    assert slot["active_ticket"]["plate"] == "NEW1"
