import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import BodySizeLimitMiddleware
from app.routers import dashboard, public, submissions, widgets

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

app = FastAPI(title="Widget & Lead-Capture Platform")

# Added first = inner. CORS is added last = outermost, so even error
# responses (413, 422, 429) carry CORS headers and browsers can read them.
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["Retry-After"],
    max_age=600,
)

app.include_router(widgets.router)
app.include_router(public.router)
app.include_router(submissions.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    """Liveness probe: answers without touching the database."""
    return {"status": "ok"}