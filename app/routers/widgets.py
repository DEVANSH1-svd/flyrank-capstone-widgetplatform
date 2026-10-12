from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.db import get_connection
from app.dependencies import get_current_tenant
from app.repositories import widgets as repo
from app.schemas import SnippetOut, WidgetIn, WidgetOut
from app.services import widgets as service

router = APIRouter(prefix="/widgets", tags=["widgets"])


def _get_or_404(conn, tenant, widget_id: UUID) -> dict:
    # Wrong tenant and missing widget look identical: 404, never 403.
    widget = repo.get_widget(conn, tenant["id"], widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget


@router.post("", response_model=WidgetOut, status_code=201)
def create_widget(body: WidgetIn, tenant=Depends(get_current_tenant), conn=Depends(get_connection)):
    return repo.create_widget(conn, tenant["id"], service.generate_public_id(), body.model_dump())


@router.get("", response_model=list[WidgetOut])
def list_widgets(tenant=Depends(get_current_tenant), conn=Depends(get_connection)):
    return repo.list_widgets(conn, tenant["id"])


@router.get("/{widget_id}", response_model=WidgetOut)
def read_widget(widget_id: UUID, tenant=Depends(get_current_tenant), conn=Depends(get_connection)):
    return _get_or_404(conn, tenant, widget_id)


@router.put("/{widget_id}", response_model=WidgetOut)
def replace_widget(widget_id: UUID, body: WidgetIn, tenant=Depends(get_current_tenant), conn=Depends(get_connection)):
    widget = repo.update_widget(conn, tenant["id"], widget_id, body.model_dump())
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget


@router.delete("/{widget_id}", status_code=204)
def delete_widget(widget_id: UUID, tenant=Depends(get_current_tenant), conn=Depends(get_connection)):
    if not repo.delete_widget(conn, tenant["id"], widget_id):
        raise HTTPException(status_code=404, detail="Widget not found")
    return Response(status_code=204)


@router.get("/{widget_id}/snippet", response_model=SnippetOut)
def widget_snippet(widget_id: UUID, tenant=Depends(get_current_tenant), conn=Depends(get_connection)):
    widget = _get_or_404(conn, tenant, widget_id)
    return {"snippet": service.build_snippet(widget["public_id"])}