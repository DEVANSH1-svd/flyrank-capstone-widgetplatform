import psycopg
from psycopg.rows import dict_row

from app.config import settings


def get_connection():
    """FastAPI dependency: one connection per request, always closed.

    The `with` block commits on success and rolls back if an exception escapes.
    """
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn