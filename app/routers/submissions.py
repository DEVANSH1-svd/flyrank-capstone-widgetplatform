import ipaddress
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response

from app.db import get_connection
from app.repositories import submissions as submissions_repo
from app.repositories import widgets as widgets_repo
from app.schemas import SubmissionIn, SubmissionOut
from app.services import geo, notifications, rate_limit
from app.services import submissions as service

router = APIRouter(tags=["submissions"])


def _client_ip(request: Request) -> str | None:
    """Return the caller's IP if it is a valid address, else None."""
    host = request.client.host if request.client else None
    try:
        return str(ipaddress.ip_address(host))
    except (ValueError, TypeError):
        return None


def _too_many_requests(wait_seconds: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="Too many requests",
        headers={"Retry-After": str(wait_seconds)},
    )


def limit_by_ip(request: Request) -> None:
    """Dependency: runs before the body is processed or the database is touched."""
    wait = rate_limit.ip_limiter.check(_client_ip(request) or "unknown")
    if wait is not None:
        raise _too_many_requests(wait)


@router.post(
    "/submissions",
    response_model=SubmissionOut,
    status_code=201,
    dependencies=[Depends(limit_by_ip)],
)
def create_submission(
    body: SubmissionIn,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    conn=Depends(get_connection),
):
    # Honeypot: bots fill the hidden field. Pretend success, store nothing.
    if body.website:
        return {"id": uuid4(), "status": "received"}

    widget = widgets_repo.get_active_widget_by_public_id(conn, body.widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    wait = rate_limit.widget_limiter.check(body.widget_id)
    if wait is not None:
        raise _too_many_requests(wait)

    try:
        clean = service.validate_submission(widget["fields"], body.data)
    except service.SubmissionValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors)

    # A retry of an already-stored submission skips the slow geo lookup entirely.
    if body.idempotency_key:
        existing = submissions_repo.get_by_idempotency_key(conn, widget["id"], body.idempotency_key)
        if existing:
            response.status_code = 200
            return {"id": existing["id"], "status": "received"}

    ip = _client_ip(request)
    geo_data, geo_provider = geo.enrich(ip)  # never raises

    submission_id, created = submissions_repo.create_submission(
        conn, widget, clean, ip, body.idempotency_key, geo_data, geo_provider
    )
    if not created:
        response.status_code = 200

    # Side effect runs after the response; its failure cannot affect the submission.
    if created and "email" in clean:
        background_tasks.add_task(notifications.send_confirmation, clean["email"], widget["title"])

    return {"id": submission_id, "status": "received"}