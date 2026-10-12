from fastapi import FastAPI

from app.routers import widgets

app = FastAPI(title="Widget & Lead-Capture Platform")
app.include_router(widgets.router)


@app.get("/health")
def health_check():
    """Liveness probe: answers without touching the database."""
    return {"status": "ok"}