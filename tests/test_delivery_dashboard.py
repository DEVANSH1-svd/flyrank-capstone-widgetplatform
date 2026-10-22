from app.config import settings

ORIGIN = {"Origin": "http://localhost:5500"}


def body(public_id, **extra):
    payload = {"widget_id": public_id, "data": {"email": "visitor@example.com"}}
    payload.update(extra)
    return payload


# ---- Widget delivery: versioned bundle and cached config ----

def test_script_is_served_with_long_immutable_cache(make_client):
    response = make_client().get("/static/widget.v1.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "max-age=31536000" in response.headers["cache-control"]
    assert "immutable" in response.headers["cache-control"]


def test_only_versioned_scripts_are_served(make_client):
    client = make_client()
    assert client.get("/static/widget.js").status_code == 404
    assert client.get("/static/..%2Fmain.py").status_code == 404


def test_config_is_cached_briefly_and_supports_etag(make_client, widget_public_id):
    client = make_client()
    url = f"/public/widgets/{widget_public_id}/config"
    first = client.get(url, headers=ORIGIN)
    assert first.status_code == 200
    assert "max-age=60" in first.headers["cache-control"]
    assert first.headers["access-control-allow-origin"] == "*"
    assert first.json()["fields"][0]["name"] == "email"
    assert "tenant_id" not in first.json()
    second = client.get(url, headers={**ORIGIN, "If-None-Match": first.headers["etag"]})
    assert second.status_code == 304


def test_config_for_unknown_widget_is_404(make_client):
    assert make_client().get("/public/widgets/doesnotexist/config").status_code == 404


# ---- Dashboard ----

def test_dashboard_requires_api_key(make_client):
    assert make_client().get("/dashboard/submissions").status_code == 401
    assert make_client().get("/dashboard/stats").status_code == 401


def test_dashboard_shows_own_submissions_and_stats_only(monkeypatch, make_client, tenant_factory):
    monkeypatch.setattr(settings, "geo_mode", "mock")
    a = tenant_factory("tenant a")
    b = tenant_factory("tenant b")
    client = make_client()
    for i in range(2):
        response = client.post("/submissions", json=body(a["public_id"], idempotency_key=f"k{i}"))
        assert response.status_code == 201

    rows_a = client.get("/dashboard/submissions", headers={"X-API-Key": a["api_key"]}).json()
    assert len(rows_a) == 2
    assert rows_a[0]["data"] == {"email": "visitor@example.com"}
    assert rows_a[0]["widget_id"] == a["widget_id"]

    stats_a = client.get("/dashboard/stats", headers={"X-API-Key": a["api_key"]}).json()
    assert stats_a["total"] == 2
    assert stats_a["per_widget"][0]["count"] == 2
    assert stats_a["per_country"] == [{"country": "Mockland", "count": 2}]

    # Tenant isolation: tenant B sees nothing of tenant A's data.
    assert client.get("/dashboard/submissions", headers={"X-API-Key": b["api_key"]}).json() == []
    assert client.get("/dashboard/stats", headers={"X-API-Key": b["api_key"]}).json()["total"] == 0