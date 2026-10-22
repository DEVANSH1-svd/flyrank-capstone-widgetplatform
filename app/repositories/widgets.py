from psycopg.types.json import Jsonb

COLUMNS = (
    "id, public_id, type, title, description, fields, button_text, "
    "config_version, is_active, created_at, updated_at"
)


def create_widget(conn, tenant_id, public_id: str, data: dict) -> dict:
    return conn.execute(
        f"INSERT INTO widgets (tenant_id, public_id, type, title, description, "
        f"fields, button_text, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
        f"RETURNING {COLUMNS}",
        (
            tenant_id, public_id, data["type"], data["title"], data["description"],
            Jsonb(data["fields"]), data["button_text"], data["is_active"],
        ),
    ).fetchone()


def list_widgets(conn, tenant_id) -> list[dict]:
    return conn.execute(
        f"SELECT {COLUMNS} FROM widgets WHERE tenant_id = %s ORDER BY created_at DESC",
        (tenant_id,),
    ).fetchall()


def get_widget(conn, tenant_id, widget_id) -> dict | None:
    return conn.execute(
        f"SELECT {COLUMNS} FROM widgets WHERE id = %s AND tenant_id = %s",
        (widget_id, tenant_id),
    ).fetchone()


def update_widget(conn, tenant_id, widget_id, data: dict) -> dict | None:
    return conn.execute(
        f"UPDATE widgets SET type = %s, title = %s, description = %s, fields = %s, "
        f"button_text = %s, is_active = %s, config_version = config_version + 1, "
        f"updated_at = now() WHERE id = %s AND tenant_id = %s RETURNING {COLUMNS}",
        (
            data["type"], data["title"], data["description"], Jsonb(data["fields"]),
            data["button_text"], data["is_active"], widget_id, tenant_id,
        ),
    ).fetchone()


def delete_widget(conn, tenant_id, widget_id) -> bool:
    cur = conn.execute(
        "DELETE FROM widgets WHERE id = %s AND tenant_id = %s",
        (widget_id, tenant_id),
    )
    return cur.rowcount == 1


def get_active_widget_by_public_id(conn, public_id: str) -> dict | None:
    """Look up an active widget for the public submission path."""
    return conn.execute(
        "SELECT id, tenant_id, title, fields FROM widgets WHERE public_id = %s AND is_active",
        (public_id,),
    ).fetchone()


def get_public_config(conn, public_id: str) -> dict | None:
    """Fields safe to show publicly (no tenant or internal ids)."""
    return conn.execute(
        "SELECT public_id, type, title, description, fields, button_text, "
        "config_version AS version FROM widgets WHERE public_id = %s AND is_active",
        (public_id,),
    ).fetchone()
