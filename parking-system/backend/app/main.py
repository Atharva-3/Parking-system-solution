"""API layer. Thin routes that call crud.py for logic and broadcast
slot-state changes to connected dashboards over WebSocket so the
occupancy grid updates live without polling."""
import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, crud, anpr
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Parking Garage API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend's origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # client doesn't need to send anything; keeps connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def ticket_out(ticket: models.Ticket) -> schemas.TicketOut:
    data = schemas.TicketOut.model_validate(ticket)
    data.slot_code = ticket.slot.code if ticket.slot else None
    return data


def slot_out(slot: models.Slot, ticket: models.Ticket | None = None) -> schemas.SlotOut:
    data = schemas.SlotOut.model_validate(slot)
    if ticket is not None:
        data.active_ticket = ticket_out(ticket)
    return data


CHECKIN_CONFLICTS = (
    crud.PlateAlreadyParked,
    crud.NoSlotAvailable,
    crud.SlotOccupied,
    crud.SlotTypeMismatch,
)


@app.get("/slots", response_model=list[schemas.SlotOut])
def list_slots(type: models.SlotType | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Slot)
    if type:
        q = q.filter(models.Slot.type == type)
    slots = q.order_by(models.Slot.level, models.Slot.code).all()
    active = {
        t.slot_id: t
        for t in db.query(models.Ticket)
        .filter(models.Ticket.status == models.TicketStatus.active)
        .all()
    }
    return [slot_out(s, active.get(s.id)) for s in slots]


@app.get("/dashboard", response_model=schemas.DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    return crud.get_dashboard(db)


@app.post("/checkin", response_model=schemas.TicketOut, status_code=201)
async def checkin(req: schemas.CheckInRequest, db: Session = Depends(get_db)):
    try:
        ticket = crud.check_in(db, req.plate, req.vehicle_type, req.slot_id)
    except CHECKIN_CONFLICTS as e:
        raise HTTPException(status_code=409, detail=str(e))
    except crud.SlotNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    await manager.broadcast({"event": "slot_update", "dashboard": crud.get_dashboard(db)})
    return ticket_out(ticket)


@app.post("/checkout", response_model=schemas.CheckOutResponse)
async def checkout(plate: str, db: Session = Depends(get_db)):
    try:
        ticket, hours, fee = crud.check_out(db, plate)
    except crud.TicketNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    await manager.broadcast({"event": "slot_update", "dashboard": crud.get_dashboard(db)})
    return schemas.CheckOutResponse(ticket=ticket_out(ticket), hours_charged=hours, amount=fee)


@app.get("/search", response_model=schemas.TicketOut)
def search(plate: str, db: Session = Depends(get_db)):
    ticket = crud.search_by_plate(db, plate)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"No active ticket for plate '{plate}'")
    return ticket_out(ticket)


@app.get("/pricing", response_model=schemas.PricingOut)
def get_pricing(db: Session = Depends(get_db)):
    return crud.get_pricing(db)


@app.patch("/pricing", response_model=schemas.PricingOut)
def update_pricing(update: schemas.PricingUpdate, db: Session = Depends(get_db)):
    rule = crud.get_pricing(db)
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@app.post("/simulate/sensor", response_model=schemas.CheckOutResponse)
async def simulate_sensor(event: schemas.SensorEvent, db: Session = Depends(get_db)):
    """IR/ultrasonic stand-in: occupy a slot (needs plate) or vacate it (checkout)."""
    hours, fee = 0, 0.0
    try:
        if event.occupied:
            if not event.plate or event.vehicle_type is None:
                raise HTTPException(
                    status_code=400,
                    detail="Sensor occupy needs a plate and vehicle_type (ANPR would supply these)",
                )
            ticket = crud.check_in(db, event.plate, event.vehicle_type, event.slot_id)
        else:
            ticket, hours, fee = crud.check_out_slot(db, event.slot_id)
    except CHECKIN_CONFLICTS as e:
        raise HTTPException(status_code=409, detail=str(e))
    except crud.SlotNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except crud.TicketNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    await manager.broadcast({"event": "slot_update", "dashboard": crud.get_dashboard(db)})
    return schemas.CheckOutResponse(ticket=ticket_out(ticket), hours_charged=hours, amount=fee)


@app.post("/simulate/anpr", response_model=schemas.TicketOut, status_code=201)
async def simulate_anpr(event: schemas.AnprEvent, db: Session = Depends(get_db)):
    """Camera stand-in: OCR a plate (or invent one) and check the car in."""
    plate = event.plate or anpr.read_plate()
    try:
        ticket = crud.check_in(db, plate, event.vehicle_type, event.slot_id)
    except CHECKIN_CONFLICTS as e:
        raise HTTPException(status_code=409, detail=str(e))
    except crud.SlotNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    await manager.broadcast({"event": "slot_update", "dashboard": crud.get_dashboard(db)})
    return ticket_out(ticket)


@app.get("/health")
def health():
    return {"status": "ok"}
