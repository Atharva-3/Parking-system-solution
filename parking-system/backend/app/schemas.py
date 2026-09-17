"""Pydantic request/response schemas — the API's public contract,
kept separate from the ORM models so internal DB shape can change
without breaking clients."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from .models import SlotType, TicketStatus


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plate: str
    vehicle_type: SlotType
    slot_id: int
    slot_code: Optional[str] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    amount_charged: Optional[float] = None
    status: TicketStatus


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    level: int
    type: SlotType
    is_occupied: bool
    active_ticket: Optional[TicketOut] = None


class CheckInRequest(BaseModel):
    plate: str
    vehicle_type: SlotType
    slot_id: Optional[int] = None  # attendant clicked this tile; omit to auto-allocate

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, v: str) -> str:
        v = v.strip().upper().replace(" ", "")
        if not v:
            raise ValueError("plate must not be empty")
        return v


class CheckOutResponse(BaseModel):
    ticket: TicketOut
    hours_charged: int
    amount: float


class DashboardCategory(BaseModel):
    type: SlotType
    total: int
    free: int
    occupied: int


class DashboardOut(BaseModel):
    categories: List[DashboardCategory]
    total_active_tickets: int
    profit_earned: float


class PricingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    first_hour_rate: float
    additional_hour_rate: float
    daily_cap: float


class PricingUpdate(BaseModel):
    first_hour_rate: Optional[float] = None
    additional_hour_rate: Optional[float] = None
    daily_cap: Optional[float] = None


class SensorEvent(BaseModel):
    """Simulated IR/ultrasonic: a slot became occupied or vacant."""
    slot_id: int
    occupied: bool
    plate: Optional[str] = None
    vehicle_type: Optional[SlotType] = None

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper().replace(" ", "")
        return v or None


class AnprEvent(BaseModel):
    """Simulated camera read. Omit plate to generate a fake OCR result."""
    plate: Optional[str] = None
    vehicle_type: SlotType
    slot_id: Optional[int] = None

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper().replace(" ", "")
        return v or None
