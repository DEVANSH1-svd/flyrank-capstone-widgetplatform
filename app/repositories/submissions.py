from psycopg.types.json import Jsonb


def get_by_idempotency_key(conn, widget_id, idempotency_key: str) -> dict | None:
    return conn.execute(
        "SELECT id FROM submissions WHERE widget_id = %s AND idempotency_key = %s",
        (widget_id, idempotency_key),
    ).fetchone()


def create_submission(conn, widget: dict, data: dict, ip: str | None,
                      idempotency_key: str | None, geo: dict | None, geo_provider: str | None):
    """Store a submission and commit. Returns (submission_id, created).

    A repeated (widget, idempotency_key) pair stores nothing new and returns
    the id of the original row with created=False.
    """
    row = conn.execute(
        "INSERT INTO submissions (widget_id, tenant_id, data, ip_address, country, city, "
        "geo_provider, idempotency_key) VALUES (%s, %s, %s, %s::inet, %s, %s, %s, %s) "
        "ON CONFLICT (widget_id, idempotency_key) DO NOTHING RETURNING id",
        (
            widget["id"], widget["tenant_id"], Jsonb(data), ip,
            geo["country"] if geo else None, geo["city"] if geo else None,
            geo_provider, idempotency_key,
        ),
    ).fetchone()
    conn.commit()  # durable before we respond and before background work starts
    if row is not None:
        return row["id"], True
    return get_by_idempotency_key(conn, widget["id"], idempotency_key)["id"], False