# Parking garage system

End-to-end parking allocation and billing system: FastAPI + SQLite backend,
React (Vite) dashboard with a BookMyShow-style seat map.

## What it does
- Check a car in and out; fee is computed automatically (₹50 first hour,
  +₹10/hour after, capped at ₹300/day; part-hours round up)
- Three slot types — compact, standard, EV — with EV vehicles restricted to
  EV slots, and compact cars allowed to overflow into standard slots if
  compact is full (standard never overflows into compact)
- Live dashboard: free/occupied counts per category, a clickable seat-map
  grid, plate search, and a WebSocket feed so the grid updates the moment
  another attendant checks a car in or out
- Pricing (first-hour rate, per-hour rate, daily cap) is stored in the DB,
  not hardcoded, so a different garage can change its rates without a
  code change

## Run the backend
```
cd backend
pip install -r requirements.txt
python -m app.seed        # creates parking.db with a sample slot layout
uvicorn app.main:app --reload --port 8000
```
API docs at http://localhost:8000/docs. Run tests with `pytest -q`.

## Run the frontend
```
cd frontend
npm install
npm run dev
```
Opens at http://localhost:5173, talking to the backend at localhost:8000
(override with a `VITE_API_URL` env var if the backend runs elsewhere).

## Adapting to a real garage
Edit the `layout` list in `backend/app/seed.py` to match your actual level
and slot counts — nothing else in the code assumes a specific garage size.

## Hardware (simulated, ready to swap)
- Click a **free** tile to check in **that** slot (allocation rules still apply).
- Click an **occupied** tile to see the car and check out, or run a simulated
  slot-sensor exit (`POST /simulate/sensor`).
- **Pricing** can be edited on the dashboard (`GET`/`PATCH /pricing`).
- **ANPR** is `POST /simulate/anpr` (blank plate → fake OCR). Later, point a
  camera pipeline at that endpoint or at `POST /checkin` with the plate string.
