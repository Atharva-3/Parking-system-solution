# Reasoning and solution process

## Goals
The parking app was built to solve a few core problems in a garage environment:
- allocate slots correctly by vehicle type
- calculate parking charges without hardcoded assumptions
- handle dirty and inconsistent input safely
- keep a live view of slot occupancy
- support background lifecycle automation such as auto-closing overdue sessions
- support safe identity transfer when a car plate changes mid-session

## Design decisions

### 1) Separate business logic from API code
The app keeps the real parking rules in the CRUD layer instead of burying them directly inside the FastAPI routes. This matters because the pricing logic, session logic, and slot assignment rules are independent business concerns and should be testable without the HTTP layer.

This separation makes it easier to:
- test price calculations directly
- reuse rules across endpoints
- isolate failures when a bug appears in billing or slot allocation

### 2) Normalize before using data
The rate-card ingestion problem required defensive parsing because input is likely dirty. Instead of assuming every row is clean, the system interprets common variations such as:
- "$12.00" vs "12"
- "Compact " vs "COMPACT"
- duplicates
- malformed values like "NaN"

The normalize logic strips whitespace, uppercases the type names, removes currency symbols, and rejects invalid rows. Bad rows are skipped with warnings instead of crashing the whole app.

### 3) Solve the lifecycle problem using stable session identity
A critical bug pattern is treating the plate as the identity of the whole session. That breaks when a valet transfers a car to another plate while the same car remains parked in the same spot.

The solution keeps a stable session record tied to a slot and a ticket, while the plate is a mutable field on the session. This means:
- the same session stays open
- the same entry time remains unchanged
- the same slot remains occupied
- only the plate value changes

This is the correct model for a garage because the session represents the parked event, not the car identity alone.

### 4) Use the current clock abstraction
The auto-close feature is time-driven, but we cannot literally wait 24 hours in tests. The application therefore introduces a controllable current-time abstraction so the system can be advanced in tests and in a simulated scheduler.

This let us simulate:
- a session remaining active under 24 hours
- a session crossing the 24-hour limit
- correct billing at closure time

### 5) Keep charging rules consistent
The system charges based on a first-hour rule and then an additional hourly rule, capped by a daily cap. This creates a clear pricing model and avoids accidental overcharging if someone stays for a long time.

Implementation decisions:
- part-hours round up
- minimum 1 hour charge is enforced
- daily cap is applied to prevent unbounded fees
- the cap is enforced consistently for each close event

## Testing strategy

### TDD workflow used
The project was built with a test-first mindset. Each major behavior was turned into a failing test before the implementation was added.

Examples of behaviors covered by tests:
- rate-card normalization and dirty-row rejection
- EV slot restrictions
- compact overflow rules
- full check-in / check-out flow
- double check-in prevention
- auto-close after 24 hours
- plate transfer while preserving session identity
- daily report totals and per-car revenue
- alert generation for overdue or duplicate sessions

### Why tests mattered here
This project has a few failure-prone edges:
- inconsistent user input from external sources
- time-based logic that can be hard to reproduce manually
- session state that mutates across the lifecycle

Without strong automated checks, these bugs are easy to miss.

## Bug-fix process used in practice

### Example 1: dirty rate data
The initial issue was that the pricing engine assumed clean numeric data and clean slot-type labels. This caused failures when values came in as currency strings, duplicates, or typos.

Fix:
- create a normalization method that accepts common dirty forms
- canonicalize type names to enum values
- ignore invalid rows gracefully
- keep valid rows and warn on invalid ones

### Example 2: overdue session closure
The system initially had no time-driven closure mechanism, so sessions stayed active forever if the time passed the 24-hour threshold.

Fix:
- add a clock abstraction
- add a scheduled scan for active tickets older than 24 hours
- close the ticket and release the slot

### Example 3: plate transfer bug
The original risk was that the plate field was acting like the session identity. If a car switched plates, the old ticket would disappear or duplicate logic would fire.

Fix:
- keep the ticket as the durable session record
- allow plate mutation on that active ticket
- preserve slot id, entry time, and billing clock

### Example 4: reporting and alerts
The project needed to show the admin and manager what happened during the day, including total revenue and alerting conditions.

Fix:
- add a day-summary report that aggregates closed tickets by date
- add alert generation for overdue and duplicate active sessions
- expose the metrics via dedicated endpoints for the frontend

## Validation
The test suite was run after each major fix to ensure no regressions. This gave confidence that the parking logic still behaved correctly while new features were added.

The final verification command was:

```bash
cd backend && pytest -q tests/test_api.py
```

This returned successful results after the implementation was finished.

## Takeaway
This project is a good example of building a real-world business workflow with defensive input parsing, clean domain modeling, and lifecycle-aware state handling. The critical theme is not just “make the app work,” but “make the app survive messy real-world data and state changes without breaking the business rules.”
