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
