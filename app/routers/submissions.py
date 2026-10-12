from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.db import get_connection
from app.repositories import submissions as submissions_repo
from app.repositories import widgets as widgets_repo
from app.schemas import SubmissionIn, SubmissionOut
from app.services import submissions as service

router = APIRouter(tags=["submissions"])


@router.post("/submissions", response_model=SubmissionOut, status_code=201)
def create_submission(
    body: SubmissionIn,
    request: Request,
    response: Response,
    conn=Depends(get_connection),
):
    # Honeypot: bots fill the hidden field. Pretend success, store nothing.
    if body.website:
        return {"id": uuid4(), "status": "received"}

    widget = widgets_repo.get_active_widget_by_public_id(conn, body.widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    try:
        clean = service.validate_submission(widget["fields"], body.data)
    except service.SubmissionValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors)

    ip = request.client.host if request.client else None
    submission_id, created = submissions_repo.create_submission(
        conn, widget, clean, ip, body.idempotency_key
    )
    if not created:
        response.status_code = 200  # replay of an earlier request
    return {"id": submission_id, "status": "received"}