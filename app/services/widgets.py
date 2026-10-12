import secrets

from app.config import settings


def generate_public_id() -> str:
    """Random, unguessable id used in the embed snippet (12 URL-safe characters)."""
    return secrets.token_urlsafe(9)


def build_snippet(public_id: str) -> str:
    base = settings.public_base_url.rstrip("/")
    return f'<script src="{base}/static/widget.v1.js" data-widget-id="{public_id}"></script>'