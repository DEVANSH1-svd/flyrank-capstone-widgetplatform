from psycopg.types.json import Jsonb


def create_submission(conn, widget: dict, data: dict, ip: str | None, idempotency_key: str | None):
    """Store a submission. Returns (submission_id, created).

    A repeated (widget, idempotency_key) pair stores nothing new and returns
    the id of the original row with created=False.
    """
    row = conn.execute(
        "INSERT INTO submissions (widget_id, tenant_id, data, ip_address, idempotency_key) "
        "VALUES (%s, %s, %s, %s::inet, %s) "
        "ON CONFLICT (widget_id, idempotency_key) DO NOTHING RETURNING id",
        (widget["id"], widget["tenant_id"], Jsonb(data), ip, idempotency_key),
    ).fetchone()
    if row is not None:
        return row["id"], True
    existing = conn.execute(
        "SELECT id FROM submissions WHERE widget_id = %s AND idempotency_key = %s",
        (widget["id"], idempotency_key),
    ).fetchone()
    return existing["id"], False