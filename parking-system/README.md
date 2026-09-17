# Parking Garage System

A full-stack parking management system built with FastAPI and React. It supports live slot occupancy, dynamic pricing, ANPR-style check-ins, billing, daily reports, and role-based access for admin, attendant, and security-manager users.

## Features
- Smart vehicle assignment across compact, standard, and EV slot types
- Dynamic pricing stored in the database
- Plate normalization and duplicate-plate prevention
- Automated closing of sessions older than 24 hours
- Plate transfer without resetting the session lifecycle
- Daily revenue and vehicle reports
- Role-based login for Admin, Attendant, and Security / Manager
- WebSocket refreshes for live dashboard updates

## Tech stack
- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: React + Vite
- Testing: pytest

## Project structure
- backend/app/ — FastAPI app, CRUD logic, models, schemas
- backend/tests/ — backend regression tests
- frontend/src/ — React app and UI components

## Prerequisites
- Python 3.11+
- Node.js 18+
- npm
- Git

## Setup

### 1) Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
```

This creates the SQLite database and seed slot data.

### 2) Start the backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open the API docs at:
- http://localhost:8000/docs
- http://localhost:8000/redoc

### 3) Frontend setup
```bash
cd frontend
npm install
npm run dev
```

Open the UI at:
- http://localhost:5173

If the backend runs somewhere else, set:
```bash
export VITE_API_URL=http://localhost:8000
```

## Demo login accounts
- Admin: admin / admin123
- Attendant: attendant / attendant123
- Security / Manager: viewer / viewer123

## Debugging and troubleshooting

### Backend debugging
- Run tests:
```bash
cd backend
pytest -q
```
- Check API output in the interactive docs: http://localhost:8000/docs
- Inspect the database with SQLite tools or through Python if needed
- Rebuild the database if needed:
```bash
cd backend
rm -f parking.db
python -m app.seed
```

### Frontend debugging
- Run a production build:
```bash
cd frontend
npm run build
```
- If the UI cannot reach the backend, confirm the backend is running and check the `VITE_API_URL` variable
- Open browser devtools to inspect network calls and console errors

### Common issues
- 404 on API routes: confirm the backend is running and using the correct port
- pricing not updating: verify the PATCH request reaches /pricing
- duplicate plate or slot conflicts: confirm the DB state and ticket status are correct

## API endpoints

### Core routes
- GET /health — health check
- GET /slots — list all parking slots
- GET /slots?type=compact — filter slots by vehicle type
- GET /dashboard — dashboard metrics
- GET /search?plate=ABC123 — fetch active ticket for a plate

### Check-in / check-out
- POST /checkin
  - Body: { "plate": "ABC123", "vehicle_type": "compact", "slot_id": 1 }
- POST /checkout?plate=ABC123
- POST /simulate/anpr
  - Camera simulation; generates a plate if missing
- POST /simulate/sensor
  - Slot sensor simulation for entry/exit events

### Pricing
- GET /pricing — fetch current pricing rule
- PATCH /pricing — update first_hour_rate, additional_hour_rate, daily_cap
- POST /pricing/ingest — ingest cleaned rate-card rows

### Lifecycle and automation
- POST /clock
  - Body optional: { "now": "2026-09-17T18:00:00" }
  - scans active tickets and auto-closes sessions older than 24 hours
- POST /transfer
  - Body: { "current_plate": "ABC123", "new_plate": "XYZ999" }
  - updates the plate on an active session without resetting entry time

### Reports and alerts
- GET /daily-report?date=2026-09-17
  - returns total cars, car mix, revenue by car, total profit for the date
- GET /alerts
  - returns overdue and duplicate-plate alerts for active sessions

### WebSocket
- WS /ws/dashboard — live update stream for dashboard refreshes

## Notes for real deployment
- This project is intentionally simple and local-first.
- For production, replace the demo login with a secure auth provider.
- Use a proper database such as PostgreSQL.
- Add real ANPR OCR integration and secure API authentication.
- Add audit logs for all pricing and transfer operations.

## Useful commands
```bash
# backend tests
cd backend && pytest -q

# backend server
cd backend && uvicorn app.main:app --reload --port 8000

# frontend dev server
cd frontend && npm run dev

# frontend build check
cd frontend && npm run build
```
