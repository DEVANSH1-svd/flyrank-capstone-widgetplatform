def list_submissions(conn, tenant_id, widget_id, limit: int, offset: int) -> list[dict]:
    return conn.execute(
        "SELECT id, widget_id, data, country, city, geo_provider, created_at "
        "FROM submissions WHERE tenant_id = %s AND (%s::uuid IS NULL OR widget_id = %s::uuid) "
        "ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (tenant_id, widget_id, widget_id, limit, offset),
    ).fetchall()


def stats(conn, tenant_id, days: int) -> dict:
    window = "tenant_id = %s AND created_at >= now() - make_interval(days => %s)"
    params = (tenant_id, days)
    total = conn.execute(f"SELECT count(*) AS count FROM submissions WHERE {window}", params).fetchone()["count"]
    per_widget = conn.execute(
        "SELECT w.id AS widget_id, w.title, count(*) AS count "
        "FROM submissions s JOIN widgets w ON w.id = s.widget_id "
        "WHERE s.tenant_id = %s AND s.created_at >= now() - make_interval(days => %s) "
        "GROUP BY w.id, w.title ORDER BY count DESC",
        params,
    ).fetchall()
    per_day = conn.execute(
        f"SELECT created_at::date AS day, count(*) AS count FROM submissions WHERE {window} "
        "GROUP BY 1 ORDER BY 1",
        params,
    ).fetchall()
    per_country = conn.execute(
        f"SELECT coalesce(country, 'Unknown') AS country, count(*) AS count FROM submissions "
        f"WHERE {window} GROUP BY 1 ORDER BY count DESC",
        params,
    ).fetchall()
    return {"total": total, "per_widget": per_widget, "per_day": per_day, "per_country": per_country}