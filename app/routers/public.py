import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from app.db import get_connection
from app.repositories import widgets as widgets_repo

router = APIRouter(tags=["public"])

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
VERSIONED_SCRIPT = re.compile(r"^widget\.v\d+\.js$")


@router.get("/static/{filename}")
def serve_widget_script(filename: str):
    """Serve a versioned widget bundle. The version is in the URL, so it can be cached forever."""
    path = STATIC_DIR / filename
    if not VERSIONED_SCRIPT.match(filename) or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return Response(
        content=path.read_bytes(),
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("/public/widgets/{public_id}/config")
def widget_config(public_id: str, request: Request, conn=Depends(get_connection)):
    """Small public payload, cached briefly. An ETag lets browsers revalidate with a 304."""
    config = widgets_repo.get_public_config(conn, public_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    etag = f'"{config["version"]}"'
    headers = {"Cache-Control": "public, max-age=60", "ETag": etag}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=config, headers=headers)