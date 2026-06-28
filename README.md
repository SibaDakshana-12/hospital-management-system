# Hospital Management System (HMS)

A mini hospital management web application built with Django, featuring doctor availability management, patient appointment booking with race-condition-safe concurrency handling, Google Calendar integration, and a separate serverless email notification service.

## Setup and Run

### Prerequisites
- Python 3.12+ (Python 3.14 also tested working)
- Node.js 18+ (for the serverless email service)
- PostgreSQL 14+ installed locally
- A Google Cloud project with Calendar API enabled (instructions below)

### 1. Clone the repository
```bash
git clone 
cd hospital-management
```

### 2. Set up the Django app

```bash
cd hms
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r ../requirements.txt
```

### 3. Create the PostgreSQL database

```bash
psql -U postgres
```
```sql
CREATE DATABASE hms_db;
\q
```

### 4. Configure environment variables

Copy `.env.example` (at project root) to `.env` and fill in your actual values:
```bash
cp ../.env.example ../.env
```
DB_NAME=hms_db

DB_USER=postgres

DB_PASSWORD=<your_postgres_password>

DB_HOST=localhost

DB_PORT=5432

SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">

DEBUG=True

### 5. Set up Google Calendar OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → create a project
2. Enable the **Google Calendar API**
3. Configure the OAuth consent screen (External, add yourself as a test user)
4. Create OAuth Client ID (Web application), add authorized redirect URI:
   `http://127.0.0.1:8080/calendar/oauth/callback/`
5. Download the JSON credentials and save as `hms/credentials.json` (this file is gitignored — you must provide your own)

### 6. Run migrations and start the Django server

```bash
python manage.py makemigrations
python manage.py migrate
$env:OAUTHLIB_INSECURE_TRANSPORT="1"     # Windows PowerShell, dev only
python manage.py runserver 8080
```

Visit `http://127.0.0.1:8080/`

### 7. Set up and run the serverless email service (separate terminal)

```bash
cd email-service
npm install
```

Copy `.env.example` to `.env` and fill in your SMTP credentials (use a [Gmail App Password](https://myaccount.google.com/apppasswords), not your real password):
SMTP_USER=youremail@gmail.com

SMTP_PASSWORD=<16-character app password>

```bash
npx serverless offline
```

The email function will be live at `http://localhost:3000/sendEmail`.

### 8. Using the app

Both servers (Django on :8080 and serverless-offline on :3000) must be running simultaneously for the full feature set — auth and booking work without the email service running, but signup/booking emails require it to be up.

Visit `http://127.0.0.1:8080/` → sign up as a Doctor or Patient → log in → use the respective dashboard.

### 9. (Optional) Verifying the race condition directly

A standalone script, `hms/test_race_condition.py`, fires two simultaneous booking attempts at the same slot using two threads and prints which one succeeded and which was rejected. Create two patient accounts and one free slot first, update the usernames inside the script, then run:
```bash
python test_race_condition.py
```

---

## System Architecture

### High-level flow
Browser → Django (HMS app) → PostgreSQL

↓

Google Calendar API (OAuth2)

↓

HTTP call → Serverless Email Function (serverless-offline) → SMTP

### Django app structure
- `accounts/` — custom User model (role: DOCTOR/PATIENT), signup/login/logout, role-based decorators
- `doctors/` — availability slot model, service layer, doctor dashboard views
- `patients/` — patient dashboard, available-slots listing
- `bookings/` — booking model and the booking service (race-condition handling lives here)
- `calendar_service/` — Google OAuth2 flow, credential storage, calendar event creation
- `email_client/` — thin client that calls the separate serverless email function over HTTP

### Data model
- `User` (custom, extends `AbstractUser`): adds `role` field (DOCTOR/PATIENT), unique email, unique username (inherited)
- `Availability`: belongs to a doctor, has date/start_time/end_time, `is_booked` flag, unique constraint on (doctor, date, start_time, end_time)
- `Booking`: OneToOne with `Availability` (a slot can have at most one booking, enforced at the database level), FK to patient
- `GoogleCredential`: OneToOne with User, stores OAuth token/refresh_token per user

### Role-based access enforcement
Custom decorators (`accounts/decorators.py`) — `doctor_required` and `patient_required` — wrap every role-specific view and raise `PermissionDenied` (403) if the logged-in user's `role` doesn't match. This is enforced at the view layer, not at login — there is a single shared login form for both roles, and what a logged-in user can *do* afterward is restricted entirely by these decorators on every doctor-only and patient-only view. A user's role is fixed permanently at signup and tied to a unique email/username, so one identity always maps to exactly one role.

### Booking flow (service layer)
Views are kept thin. All booking logic lives in `bookings/services.py::BookingService.book_slot()`, which wraps the check-and-create operation in `transaction.atomic()` with `select_for_update()` on the slot row — see Design Decision below.

### Slot creation
A doctor enters a date plus a start/end time range and a slot duration (e.g. 30 minutes). `DoctorService.create_slots()` automatically splits that range into discrete, individually bookable `Availability` rows rather than creating one wide slot — so a 10:00–13:00 entry with a 1-hour duration becomes three separate 1-hour slots, each independently bookable.

### Google Calendar integration
Each user connects their own Google account once via `/calendar/oauth/connect/` (OAuth2, scope: `calendar.events`). Credentials are stored per-user in `GoogleCredential`. When a booking succeeds, `GoogleCalendarService.create_booking_events()` creates one event on the patient's calendar and one on the doctor's calendar. If a user hasn't connected their calendar, event creation is skipped silently (logged, not raised) — calendar integration failure must never block a booking.

### Serverless email service
`email-service/` is a completely separate Python project (Serverless Framework + `serverless-offline`), with its own `requirements.txt` and `serverless.yml`. Django's `email_client/services.py` calls it over plain HTTP (`requests.post`) — not via Python import — to genuinely simulate the serverless/microservice boundary the assignment asks for. Two triggers are supported: `SIGNUP_WELCOME` and `BOOKING_CONFIRMATION`. As with calendar integration, email failures are caught and logged, never allowed to break the core signup/booking flow.

---

## The Design Decision

**Problem:** When two patients attempt to book the same time slot at virtually the same instant, the system must guarantee that exactly one booking succeeds and the other is rejected cleanly — without corrupting data or double-booking a doctor.

**Approach 1 — Optimistic locking.** Perform a conditional `UPDATE Availability SET is_booked = TRUE WHERE id = ? AND is_booked = FALSE`, and check how many rows were affected. If 0 rows changed, someone else already booked it, so reject. No database row locking occurs — both transactions race, and the database's row-level write guarantees ensure only one `UPDATE` actually changes a row.

**Approach 2 — Pessimistic locking (what I chose).** Use `select_for_update()` inside `transaction.atomic()` to lock the `Availability` row the moment one transaction reads it. A second concurrent request for the same slot blocks at the database level until the first transaction commits or rolls back, then sees the now-updated `is_booked=True` state and fails cleanly with a custom `SlotAlreadyBookedError`.

**Why I chose pessimistic locking:** For this system's actual usage pattern — a handful of patients occasionally competing for a specific slot, not thousands of concurrent writers — the brief row-lock cost is negligible, and the code is far easier to read and reason about correctly. `select_for_update()` makes the lock-then-check-then-write sequence explicit and atomic in one readable block, whereas the optimistic approach requires manually inspecting `rowcount`/affected rows and is easier to get subtly wrong (e.g., forgetting to check the count, or not wrapping the whole booking-creation step in the same atomicity boundary). Correctness and readability mattered more here than raw throughput, since this system was never going to face high-concurrency write contention at the scale the assignment describes. I verified this behavior both through the UI (two browser sessions booking the same slot) and through a standalone threaded test script that fires two booking attempts at the exact same instant.

---

## Limitations

- **No automated test suite.** The race condition was verified manually and via a standalone concurrency script (`test_race_condition.py`), not formal Django `TestCase`s. In production, this would need proper unit/integration tests, especially around the booking service and OAuth token refresh paths.
- **OAuth tokens are stored in plaintext in the database.** `GoogleCredential` stores `token`/`refresh_token` as plain `TextField`s. In production these must be encrypted at rest (e.g., via Django's `django-cryptography` or a secrets manager).
- **No token refresh handling.** If a user's Google access token expires and the refresh token itself becomes invalid (e.g., revoked access), calendar event creation will fail silently rather than prompting re-authentication.
- **Email/calendar failures are only logged, not surfaced to the user.** If a booking confirmation email fails to send, the patient has no indication anything went wrong — acceptable for this assignment's scope, but a production system would need a retry queue and/or a "notifications" status visible to the user.
- **No rate limiting or abuse protection** on signup, login, or booking endpoints.
- **`DEBUG=True` and a default `SECRET_KEY`** are used for local development; both must be changed before any real deployment.
- **Serverless function is not actually deployed to AWS** — only tested via `serverless-offline`, per the assignment's scope. Real deployment would require IAM roles, environment secrets management, and probably moving off direct SMTP to a transactional email provider (SES, SendGrid) for deliverability.
- **No pagination** on slot/booking lists — would not scale past a small number of doctors/slots.
- **One identity, one fixed role.** Email and username are globally unique, so the same person cannot hold both a doctor and a patient account under one email — a deliberate simplification, not an oversight (see System Architecture).