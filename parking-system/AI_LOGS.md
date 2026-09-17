1.The storyline



A busy multi-level city-centre parking garage. Cars come and go all day, and the attendant needs to check a car in, check it out, and charge the right fee. Rates are tiered — the first hour is one price, each extra hour is cheaper, and there’s a daily cap so nobody is overcharged for a long stay; part-hours round up. Spots are limited and come in types — compact, standard, and EV (with a charger) — and an EV must get an EV spot. Drivers keep asking ‘is an EV spot free right now?’ and the attendant hunts for a car by its plate. By evening the log is huge.



Build the attendant something so every car is charged correctly and no spot is double-parked.



(The attendant’s day is the spec — build it for any garage, not one. Get check-in / check-out and the fee right first, then the spot types and lookups.)

This is the problem statement now i have an idea



I want to allot parking system as per book my show movie seats (like in book my show there is vacant seats and whenever we book seats colour changes )



Also i have to create a dashboard where there is three types of category are present:



1.Compact(Hatchback or small cars)



2.Standard(SUV and sedan)



3.Ev(Contains ev charger)



So allotment has to be done in these empty spaces



Charging functionaity-

First hour fix charge(Ex:50)

After one hour add (Ex:10 per hour)

Max charge per parking (300;Not excessing 300 irresepecive of its hours)

For marking if we can use a sensor for recording it's initial timestamp and final timestamp and calculate time according to it

For detecting number plates if u have any suggestion you could tell me

If we could check empty and occupied spaces on dashboard using sensor

If you could suggest any improvements pls do first create a basic layout -get it approved by me then start coding

2.First give me tech stack

3.Now create a full fledge end to end or production grade code

4.Tell me what have done till now and also tell me the gaps

5.Clear those gaps



Run in browser

7.Create a front page that contains therse funciotnalities of

Compact

Standard

EV

these are furether gettimg redericted to these indivisual parking pages



The front pages must contain these info such as

Total cars present

Total vacant spaces

Profit earned



Also ev charger must be present in each ev charging station check wheter it is in use or not

And in the ebove ss you could see that i have already selected compact still there is pop up showing which vechicle to select overcome this

8.Each submission is expected to be a working full-stack product. Every solution must include:

- A database (real persistence with a sensible schema).

- REST APIs for the core operations — and the candidate must list these endpoints in the README.

- A usable UI over those APIs.

- User registration and login.

- Search.

- A one-page landing page for the product (what it is, key features, target audience, how it helps, and three features they would build next).

- Pagination and sorting





Does our project contains each of these components and pls list them

9.Run this project



10.1:You're given a rate card that's "dirty" — likely things like inconsistent formats ($12.00 vs 1200 vs "12"), typos in spot-type names ("Compact " vs "compact" vs "COMPACT"), missing fields, duplicate entries, or malformed rows. You need to:



1. Parse and **clean/normalize** this input into a consistent internal rate structure (per spot type: first-hour rate, extra-hour rate, daily cap)

2. Make your pricing engine consume the *cleaned* rates

3. Handle bad rows gracefully (skip, flag, or default) rather than crashing



This is testing whether your ingestion layer is decoupled from your pricing logic, and whether you can defensively parse untrusted input.

2:### Level 2 — Twist T2: Automation / Scheduled Job



**What it tests:** time-driven side effects, not just request/response actions.



The system needs a background process (simulated via a `POST /clock` endpoint, since graders can't literally wait 24 hours) that:



1. Advances/sets the "current time" in your system

2. Scans all open sessions

3. **Auto-closes** any session that's been parked over 24 hours

4. **Bills it correctly** — this likely interacts with your daily cap logic (does a 30-hour stay get capped once, or does the cap reset per 24h period? — you need to decide and be consistent)

### Level 3 — Twist T6: Lifecycle Transfer



**What it tests:** mutating an entity's identity mid-lifecycle without breaking its state.



A valet hands a car off to another car's plate mid-session — meaning:



- The **session stays open** (same spot occupied, same entry time, same fee-accrual clock)

- Only the **plate number** on that session changes

- The spot must **not** be treated as freed/re-parked, and the entry time must **not** reset



This tests your data model: is a "session" identified by plate (bad — breaks here) or by a stable internal session/spot ID with plate as a mutable attribute (good — survives this twist)? It's really a stress test of whether you conflated "car" and "session" as the same concept.

Now add these functionalities



11.A one-page landing page for the product (what it is, key features, target audience, how it helps, and three features they would build next).

12.Now it should have following functionaliites

Avoid any typo

2.Parse and make data clear and consistent

3.Scans all open slots

4.Auto close session

5.Billing correctly

6.If any cars switched it must auto update the entries

13.Create a database containg logs of a single day

Has all type of cars that came in a day

2.Money earned from each car total profit

3.Profit earned at a single day

14.Create a database containg logs of a single day

Has all type of cars that came in a day

2.Money earned from each car total profit

3.Profit earned at a single day

15.Use a simple login system with roles such as:



- Admin

- Attendant

- Viewer

Also add fucntionalities such as 

- Admin login

- change pricing

- view daily profit reports

- manage garage settings

- Attendant login

- check vehicles in/out

- search plates

- update occupancy

- Security/manager login

- monitor active sessions

- view alerts like overdue vehicles or duplicate plates

16.Yes create a dedictaed report page 

