import secrets

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.config import settings
from app.main import app
from app.repositories import tenants, widgets
from app.security import hash_api_key
from app.services import rate_limit


@pytest.fixture(autouse=True)
def reset_rate_limits():
    rate_limit.ip_limiter.reset()
    rate_limit.widget_limiter.reset()


@pytest.fixture
def make_client():
    """Build a test client that appears to connect from the given IP address."""
    def _make(ip: str = "203.0.113.10") -> TestClient:
        return TestClient(app, client=(ip, 50000))
    return _make


@pytest.fixture
def widget_public_id():
    """Create a throwaway tenant and widget; delete them (cascade) afterwards."""
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        tenant = tenants.create_tenant(conn, "pytest tenant", hash_api_key(secrets.token_urlsafe(32)))
        widget = widgets.create_widget(
            conn,
            tenant["id"],
            secrets.token_urlsafe(9),
            {
                "type": "signup_form",
                "title": "Test widget",
                "description": None,
                "fields": [{"name": "email", "label": "Email", "type": "email", "required": True}],
                "button_text": "Send",
                "is_active": True,
            },
        )
        conn.commit()
    yield widget["public_id"]
    with psycopg.connect(settings.database_url) as conn:
        conn.execute("DELETE FROM tenants WHERE id = %s", (tenant["id"],))
        conn.commit()


@pytest.fixture
def stored_rows():
    def _rows(public_id: str) -> list[dict]:
        with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
            return conn.execute(
                "SELECT s.* FROM submissions s JOIN widgets w ON w.id = s.widget_id "
                "WHERE w.public_id = %s ORDER BY s.created_at",
                (public_id,),
            ).fetchall()
    return _rows