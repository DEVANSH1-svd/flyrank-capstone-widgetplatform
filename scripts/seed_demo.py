"""Create a demo tenant with one widget and print how to try it.

Usage: python -m scripts.seed_demo
"""
import psycopg
from psycopg.rows import dict_row

from app.config import settings
from app.repositories import tenants, widgets
from app.security import generate_api_key, hash_api_key
from app.services.widgets import build_snippet, generate_public_id

DEMO_WIDGET = {
    "type": "signup_form",
    "title": "Join the Acme newsletter",
    "description": "Monthly news, no spam.",
    "fields": [
        {"name": "name", "label": "Your name", "type": "text", "required": False},
        {"name": "email", "label": "Email", "type": "email", "required": True},
    ],
    "button_text": "Subscribe",
    "is_active": True,
}


def main() -> None:
    api_key = generate_api_key()
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        tenant = tenants.create_tenant(conn, "Demo Tenant", hash_api_key(api_key))
        widget = widgets.create_widget(conn, tenant["id"], generate_public_id(), DEMO_WIDGET)
        conn.commit()
    public_id = widget["public_id"]
    print(f"Tenant:     {tenant['name']}")
    print(f"API key (shown once, save it now): {api_key}")
    print(f"Widget public id: {public_id}")
    print(f"Embed snippet: {build_snippet(public_id)}")
    print(f"Test page: http://localhost:5500/?widget={public_id}")


if __name__ == "__main__":
    main()