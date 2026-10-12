def create_tenant(conn, name: str, api_key_hash: str) -> dict:
    return conn.execute(
        "INSERT INTO tenants (name, api_key_hash) VALUES (%s, %s) "
        "RETURNING id, name, created_at",
        (name, api_key_hash),
    ).fetchone()


def get_tenant_by_key_hash(conn, api_key_hash: str) -> dict | None:
    """Return the tenant owning this key hash, or None if there is no match."""
    return conn.execute(
        "SELECT id, name FROM tenants WHERE api_key_hash = %s",
        (api_key_hash,),
    ).fetchone()