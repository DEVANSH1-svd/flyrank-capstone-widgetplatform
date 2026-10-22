from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db import get_connection
from app.dependencies import get_current_tenant
from app.repositories import dashboard as repo
from app.schemas_dashboard import StatsOut, SubmissionRow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/submissions", response_model=list[SubmissionRow])
def list_submissions(
    widget_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    tenant=Depends(get_current_tenant),
    conn=Depends(get_connection),
):
    return repo.list_submissions(conn, tenant["id"], widget_id, limit, offset)


@router.get("/stats", response_model=StatsOut)
def stats(
    days: int = Query(30, ge=1, le=365),
    tenant=Depends(get_current_tenant),
    conn=Depends(get_connection),
):
    return {"days": days, **repo.stats(conn, tenant["id"], days)}