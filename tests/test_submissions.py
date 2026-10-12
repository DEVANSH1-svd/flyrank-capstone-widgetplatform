import time

from app.config import settings
from app.services import rate_limit

ORIGIN = {"Origin": "http://localhost:5500"}


def body(public_id, **extra):
    payload = {"widget_id": public_id, "data": {"email": "visitor@example.com"}}
    payload.update(extra)
    return payload


# ---- Probe 1: cross-origin submission is stored ----

def test_valid_cross_origin_submission_is_stored(make_client, widget_public_id, stored_rows):
    response = make_client().post("/submissions", json=body(widget_public_id), headers=ORIGIN)
    assert response.status_code == 201
    assert response.headers["access-control-allow-origin"] == "*"
    assert len(stored_rows(widget_public_id)) == 1


def test_preflight_is_answered(make_client):
    headers = {**ORIGIN, "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "content-type"}
    response = make_client().options("/submissions", headers=headers)
    assert response.status_code == 200
    assert "POST" in response.headers["access-control-allow-methods"]


def test_repeated_idempotency_key_stores_once(make_client, widget_public_id, stored_rows):
    client = make_client()
    first = client.post("/submissions", json=body(widget_public_id, idempotency_key="k1"))
    second = client.post("/submissions", json=body(widget_public_id, idempotency_key="k1"))
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["id"] == second.json()["id"]
    assert len(stored_rows(widget_public_id)) == 1


# ---- Probe 2: bad input gives clean 4xx, never 500 ----

def test_malformed_json_is_422(make_client):
    response = make_client().post("/submissions", content="{bad json",
                                  headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_invalid_email_is_422(make_client, widget_public_id):
    payload = {"widget_id": widget_public_id, "data": {"email": "not-an-email"}}
    assert make_client().post("/submissions", json=payload).status_code == 422


def test_oversized_payload_is_413(make_client, widget_public_id):
    response = make_client().post("/submissions", json=body(widget_public_id, padding="x" * 20000))
    assert response.status_code == 413


# ---- Probe 3: rate limiting ----

def test_burst_gets_429_then_service_recovers(make_client, widget_public_id):
    spam = body(widget_public_id, website="http://spam.example")  # honeypot: stores nothing
    attacker = make_client("203.0.113.20")
    codes = [attacker.post("/submissions", json=spam).status_code for _ in range(15)]
    assert 429 in codes
    # A different visitor is unaffected while the attacker is throttled.
    other = make_client("203.0.113.21").post("/submissions", json=body(widget_public_id))
    assert other.status_code == 201
    # After a short wait the throttled IP is served again.
    time.sleep(1.5)
    assert attacker.post("/submissions", json=body(widget_public_id)).status_code == 201


def test_per_widget_limit(monkeypatch, make_client, widget_public_id):
    monkeypatch.setattr(rate_limit, "widget_limiter", rate_limit.TokenBucketLimiter(2, 0.01))
    client = make_client("203.0.113.30")
    codes = [client.post("/submissions", json=body(widget_public_id)).status_code for _ in range(3)]
    assert codes == [201, 201, 429]


# ---- Probe 4: geo provider fallback chain ----

def test_provider_a_answers(monkeypatch, make_client, widget_public_id, stored_rows):
    monkeypatch.setattr(settings, "geo_mode", "mock")
    assert make_client().post("/submissions", json=body(widget_public_id)).status_code == 201
    row = stored_rows(widget_public_id)[0]
    assert (row["geo_provider"], row["country"]) == ("a", "Mockland")


def test_provider_b_answers_when_a_is_down(monkeypatch, make_client, widget_public_id, stored_rows):
    monkeypatch.setattr(settings, "geo_mode", "mock")
    monkeypatch.setattr(settings, "geo_force_down", "a")
    assert make_client().post("/submissions", json=body(widget_public_id)).status_code == 201
    row = stored_rows(widget_public_id)[0]
    assert (row["geo_provider"], row["city"]) == ("b", "Mock City B")


def test_all_providers_down_still_stores(monkeypatch, make_client, widget_public_id, stored_rows):
    monkeypatch.setattr(settings, "geo_mode", "mock")
    monkeypatch.setattr(settings, "geo_force_down", "a,b")
    assert make_client().post("/submissions", json=body(widget_public_id)).status_code == 201
    row = stored_rows(widget_public_id)[0]
    assert row["geo_provider"] is None and row["country"] is None


# ---- Probe 5: failing side effect does not block the submission ----

def test_email_failure_does_not_break_submission(monkeypatch, make_client, widget_public_id, stored_rows):
    monkeypatch.setattr(settings, "email_force_fail", True)
    monkeypatch.setattr(settings, "email_retry_delay_seconds", 0)
    response = make_client().post("/submissions", json=body(widget_public_id))
    assert response.status_code == 201
    assert len(stored_rows(widget_public_id)) == 1


# ---- Probe 6: honeypot ----

def test_honeypot_is_dropped_silently(make_client, widget_public_id, stored_rows):
    response = make_client().post("/submissions", json=body(widget_public_id, website="http://spam.example"))
    assert response.status_code == 201
    assert stored_rows(widget_public_id) == []