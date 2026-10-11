"""Apply SQL migration files in order, skipping ones already applied."""
from pathlib import Path

import psycopg

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def run_migrations() -> None:
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "filename text PRIMARY KEY, "
            "applied_at timestamptz NOT NULL DEFAULT now())"
        )
        conn.commit()

        applied = {row[0] for row in conn.execute("SELECT filename FROM schema_migrations")}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                print(f"skip   {path.name} (already applied)")
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))
            conn.commit()
            print(f"apply  {path.name}")


if __name__ == "__main__":
    run_migrations()