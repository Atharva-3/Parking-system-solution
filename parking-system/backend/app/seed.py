"""Populate an empty DB with a sample garage layout. Adjust the counts
below (or write your own script) to match a real garage's slot map —
nothing else in the app is hardcoded to these numbers."""
from .database import SessionLocal, engine, Base
from . import models


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Slot).count() > 0:
            print("Slots already seeded, skipping.")
            return

        layout = [
            (1, models.SlotType.compact, 8),
            (1, models.SlotType.standard, 8),
            (1, models.SlotType.ev, 4),
            (2, models.SlotType.compact, 6),
            (2, models.SlotType.standard, 6),
            (2, models.SlotType.ev, 2),
        ]
        prefix = {models.SlotType.compact: "C", models.SlotType.standard: "S", models.SlotType.ev: "E"}
        for level, slot_type, count in layout:
            for i in range(1, count + 1):
                code = f"{prefix[slot_type]}{level}-{i:02d}"
                db.add(models.Slot(code=code, level=level, type=slot_type, is_occupied=False))

        db.add(models.PricingRule())  # defaults: 50 / +10 / cap 300
        db.commit()
        print("Seeded garage layout.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
