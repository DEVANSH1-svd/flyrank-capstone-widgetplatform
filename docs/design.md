# Design Document: Embeddable Widget & Lead-Capture Platform

## 1. Problem

Small businesses want to collect leads (signups, contact requests) on their own websites without building a backend. This platform lets a customer (a "tenant") define a widget, then paste one `<script>` tag into any website. Visitors submit the widget's form; the platform validates the input, blocks spam and floods, enriches the submission with the visitor's location, stores it, and shows it to the tenant in an authenticated dashboard.

The defining constraint: the submission endpoint is public. It receives requests from browsers and origins we do not control, so we never trust input, cannot predict traffic, and must degrade gracefully when dependencies fail.

## 2. Data model

PostgreSQL. Schema is managed with migrations.

### tenants
| Column | Type | Notes |
|---|---|---|
| id | uuid, primary key | |
| name | text, not null | |
| api_key_hash | text, unique, not null | Hash of the API key; the raw key is shown once at creation and never stored |
| created_at | timestamptz, not null | |

### widgets
| Column | Type | Notes |
|---|---|---|
| id | uuid, primary key | Internal id |
| public_id | text, unique, not null | Random, unguessable id used in the embed snippet |
| tenant_id | uuid, foreign key to tenants, not null | Owner; every query filters on this |
| type | text, not null | signup_form or contact_form |
| title | text, not null | |
| description | text | |
| fields | jsonb, not null | Form field definitions |
| button_text | text, not null | |
| config_version | integer, not null | Incremented on every change; used for cache busting |
| is_active | boolean, not null | |
| created_at, updated_at | timestamptz, not null | |

### submissions
| Column | Type | Notes |
|---|---|---|
| id | uuid, primary key | |
| widget_id | uuid, foreign key to widgets, not null | |
| tenant_id | uuid, foreign key to tenants, not null | Copied from the widget so dashboard queries filter without a join |
| data | jsonb, not null | Validated visitor input |
| ip_address | inet | |
| country, city | text | Null when no geo provider answered |
| geo_provider | text | Which provider enriched this row; null if none |
| idempotency_key | text | Supplied by the widget script to make retries safe |
| created_at | timestamptz, not null | |

### Indexes
- widgets (tenant_id)
- submissions (tenant_id, widget_id, created_at)
- unique (widget_id, idempotency_key) on submissions: a retried submission is stored once
## 3. API surface

Three request paths, kept separate.

### Owner API (authenticated with the `X-API-Key` header)
| Method | Path | Success | Errors |
|---|---|---|---|
| POST | /widgets | 201 + widget | 401, 422 |
| GET | /widgets | 200 + list | 401 |
| GET | /widgets/{id} | 200 | 401, 404 |
| PUT | /widgets/{id} | 200 | 401, 404, 422 |
| DELETE | /widgets/{id} | 204 | 401, 404 |
| GET | /widgets/{id}/snippet | 200 + embed snippet | 401, 404 |
| GET | /dashboard/submissions | 200 + paginated list (query: widget_id, limit, offset) | 401 |
| GET | /dashboard/stats | 200 + counts per widget, per day, per country | 401 |

A widget that belongs to another tenant returns 404, not 403, so its existence is not revealed.

### Customer-site path (public, cached, CORS)
| Method | Path | Success | Cache-Control |
|---|---|---|---|
| GET | /static/widget.v1.js | 200 JavaScript | public, max-age=31536000, immutable (new version = new URL) |
| GET | /public/widgets/{public_id}/config | 200 small JSON | public, max-age=60 |

Embed snippet: `<script src="https://HOST/static/widget.v1.js" data-widget-id="PUBLIC_ID"></script>`

### Visitor path (public, CORS, protected)
| Method | Path | Success | Errors |
|---|---|---|---|
| OPTIONS | /submissions | 204 preflight | |
| POST | /submissions | 201 | 404 unknown widget, 413 too large, 422 invalid, 429 rate limited |

Request body: `widget_id` (public id), `data` (object), `idempotency_key`, `website` (honeypot, must be empty). A filled honeypot returns a fake 201 and stores nothing. A repeated idempotency key returns the original result and stores nothing new. Errors are always JSON, never a 500.

Order of work in POST /submissions: size check, rate limit, validation, honeypot, idempotency check, geo enrichment (provider A, then B, then none), store, then a non-critical side effect (confirmation email) that may fail without affecting the response.

## 4. Layers

| Layer | Folder | Responsibility | Must not |
|---|---|---|---|
| Routers | app/routers | HTTP only: parse request, call a service, return a response | contain business rules or SQL |
| Services | app/services | Rules: spam check, geo fallback chain, email side effect | know about HTTP or write SQL |
| Repositories | app/repositories | All SQL; every query filters by tenant_id | contain rules |
| Schemas | app/schemas.py | Pydantic validation of requests and responses | |
| Config | app/config.py | Settings from environment variables | hold secrets in code |

## 5. Non-goal

No self-service tenant signup or visual form builder. Tenants are created by a seed script that prints a one-time API key. The platform proves the hard parts (public API security, caching, resilience), not account management.