# Embeddable Widget & Lead-Capture Platform

A backend where customers define embeddable widgets (signup and contact forms), install them on any website with one `<script>` tag, and receive visitor submissions that are validated, spam-filtered, rate-limited, enriched with location data, stored, and shown in an authenticated dashboard.

Built with Python, FastAPI and PostgreSQL as the FlyRank Internship Backend Track capstone.

## Architecture

```
Widget owner (X-API-Key)
  -> Owner API: /widgets (CRUD), /widgets/{id}/snippet, /dashboard/*
  -> repositories (every query filters by tenant_id) -> PostgreSQL

Customer website (any origin)
  <script src=".../static/widget.v1.js" data-widget-id="PUBLIC_ID">
  -> GET /static/widget.v1.js            (public, immutable cache, versioned URL)
  -> GET /public/widgets/{id}/config     (public, max-age=60 + ETag, CORS)
  -> renders the form

Website visitor
  -> POST /submissions                   (public, CORS)
       size limit        too big?   413
       rate limit (IP)   flood?     429 + Retry-After
       honeypot          bot?       fake 201, nothing stored
       widget lookup     unknown?   404
       rate limit (widget)          429
       validation        invalid?   422 (never 500)
       idempotency       retry?     200, original id
       geo enrichment    provider A -> provider B -> none (never fails)
       store + commit
       background job    confirmation email, 3 retries, ALERT log on failure
```

Layers: `app/routers` (HTTP only), `app/services` (rules), `app/repositories` (all SQL), `app/schemas*.py` (validation), `migrations/` (schema).

## Setup

Requirements: Python 3.12+, Docker Desktop.

```
python -m venv .venv
# Windows PowerShell:  .\.venv\Scripts\Activate.ps1      Linux/macOS:  source .venv/bin/activate
python -m pip install -r requirements.txt
# Windows: Copy-Item .env.example .env                    Linux/macOS: cp .env.example .env
docker compose up -d db
python -m scripts.migrate
python -m scripts.seed_demo
python -m uvicorn app.main:app --port 8000
```

`seed_demo` prints a demo API key (shown once), a widget public id, the embed snippet and a test-page URL.

The "customer website" is a plain HTML page on a second origin (port 5500):

```
python -m http.server 5500 --directory test-site
```

Open the printed URL, for example `http://localhost:5500/?widget=PUBLIC_ID`.

Run the tests (needs the database running): `python -m pytest -q`

Interactive API docs: `http://127.0.0.1:8000/docs`
## API

### Owner API (header `X-API-Key`)

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | /widgets | 201 | 401, 422 |
| GET | /widgets | 200 | 401 |
| GET | /widgets/{id} | 200 | 401, 404 |
| PUT | /widgets/{id} | 200 | 401, 404, 422 |
| DELETE | /widgets/{id} | 204 | 401, 404 |
| GET | /widgets/{id}/snippet | 200 | 401, 404 |
| GET | /dashboard/submissions?widget_id=&limit=&offset= | 200 | 401, 422 |
| GET | /dashboard/stats?days=30 | 200 | 401, 422 |

A widget owned by another tenant returns 404, never 403, so its existence is not revealed.

### Public API

| Method | Path | Notes |
|---|---|---|
| GET | /static/widget.v1.js | `Cache-Control: public, max-age=31536000, immutable`; new version = new URL |
| GET | /public/widgets/{public_id}/config | `max-age=60`, ETag, 304 on revalidation |
| POST | /submissions | 201 stored, 200 replay, 404, 413, 422, 429 |
| GET | /health | liveness |

### Example requests

Create a widget (Windows: use `curl.exe` and put the JSON in a file):

```
curl.exe -X POST http://127.0.0.1:8000/widgets -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" -d "@widget.json"
```

```json
{"type": "signup_form", "title": "Join us", "fields": [{"name": "email", "label": "Email", "type": "email", "required": true}], "button_text": "Subscribe"}
```

Submit as a visitor:

```
curl.exe -X POST http://127.0.0.1:8000/submissions -H "Content-Type: application/json" -H "Origin: http://localhost:5500" -d "@submission.json"
```

```json
{"widget_id": "PUBLIC_ID", "data": {"email": "visitor@example.com"}, "idempotency_key": "abc-123"}
```

Response: `201 {"id": "...", "status": "received"}`. Invalid input: `422 {"detail": [{"field": "email", "msg": "Invalid email address"}]}`.

## Reproducing the acceptance probes

All toggles are environment variables (see `.env.example`):

- Burst and rate limit: send many rapid POSTs, expect 429 with a `Retry-After` header, then a normal request succeeds after a moment. Tuned by `RATE_LIMIT_IP_BURST` and `RATE_LIMIT_IP_PER_SECOND`.
- Geo fallback, deterministic: `GEO_MODE=mock` answers from mock provider A. Add `GEO_FORCE_DOWN=a` and provider B answers. `GEO_FORCE_DOWN=a,b` stores the submission with no geo data. Leave `GEO_MODE=live` to call ip-api.com then ipapi.co.
- Failing side effect: `EMAIL_FORCE_FAIL=true`. The submission still returns 201; the log shows retries and an `ALERT` line.
- Honeypot: send a non-empty `website` field. The response is a fake 201 and nothing is stored.

Each of these is also covered by an automated test in `tests/`.

## Design decisions

- API-key auth: only a SHA-256 hash of each key is stored. Keys are random 256-bit values, so a fast hash is safe. The raw key is shown once by the seed script.
- Token-bucket rate limiter written in-house, because the per-widget limit depends on the JSON body, which a header-only limiter cannot see.
- Geo enrichment, rate limiting and email never raise into the request path: a broken dependency degrades the response and never destroys it.
- Rows are committed explicitly before the response and before background work starts.
- Tenant isolation is enforced in SQL: every owner query includes `tenant_id`; submissions also carry `tenant_id`.

## Limitations

- The rate limiter keeps its counters in memory, so limits are per process. Multiple workers or servers would need a shared store such as Redis.
- The client IP is taken from the TCP connection. Behind a reverse proxy it would need trusted `X-Forwarded-For` handling.
- The background email job runs in-process with retries. If the server crashes mid-retry the job is lost. A durable queue would fix this.
- Email is logged to the console, not delivered. The geo providers are free tiers with their own rate limits.
- Live geo lookups run synchronously with a 2 second timeout per provider.
- Tenants are created by a seed script; there is no self-service signup (an explicit non-goal, see `docs/design.md`).
- Preflight returns 200, not the 204 mentioned in the design document; both are valid.
- Migrations are plain SQL files with a small runner, not Alembic.

## Future improvements

- Dockerize the API so one `docker compose up` runs everything.
- Durable job queue for emails and webhooks.
- Redis-backed rate limiting.
- Minified production bundle, targeting rules, and double opt-in.