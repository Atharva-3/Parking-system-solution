"""ORM models. Three tables: Slot (a physical parking space), Ticket (one
visit of one vehicle), PricingRule (tiered fee config, editable without a
code change so any garage can set its own rates)."""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base


class SlotType(str, enum.Enum):
    compact = "compact"
    standard = "standard"
    ev = "ev"


class TicketStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g. "C-04"
    level = Column(Integer, nullable=False, default=1)
    type = Column(Enum(SlotType), nullable=False, index=True)
    is_occupied = Column(Boolean, default=False, index=True)

    tickets = relationship("Ticket", back_populates="slot")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String, index=True, nullable=False)
    vehicle_type = Column(Enum(SlotType), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    amount_charged = Column(Float, nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.active, index=True)

    slot = relationship("Slot", back_populates="tickets")


class PricingRule(Base):
    """Single-row config table. Kept in the DB (not hardcoded) so a garage
    owner can change rates without redeploying code."""
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, default=1)
    first_hour_rate = Column(Float, default=50.0)
    additional_hour_rate = Column(Float, default=10.0)
    daily_cap = Column(Float, default=300.0)
