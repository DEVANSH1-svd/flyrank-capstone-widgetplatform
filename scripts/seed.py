"""Create a tenant and print its API key once.

Usage: python -m scripts.seed "Tenant Name"
"""
import sys

import psycopg
from psycopg.rows import dict_row

from app.config import settings
from app.repositories import tenants
from app.security import generate_api_key, hash_api_key


def main(name: str) -> None:
    raw_key = generate_api_key()
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        tenant = tenants.create_tenant(conn, name, hash_api_key(raw_key))
    print(f"Created tenant: {tenant['name']} (id {tenant['id']})")
    print(f"API key (shown once, save it now): {raw_key}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python -m scripts.seed "Tenant Name"')
    main(sys.argv[1])