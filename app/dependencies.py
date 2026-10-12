from fastapi import Depends, Header, HTTPException

from app.db import get_connection
from app.repositories import tenants
from app.security import hash_api_key


def get_current_tenant(
    x_api_key: str | None = Header(default=None),
    conn=Depends(get_connection),
) -> dict:
    """Authenticate the caller from the X-API-Key header, or raise 401."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    tenant = tenants.get_tenant_by_key_hash(conn, hash_api_key(x_api_key))
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return tenant