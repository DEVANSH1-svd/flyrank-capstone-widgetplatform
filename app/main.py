from fastapi import FastAPI

app = FastAPI(title="Widget & Lead-Capture Platform")


@app.get("/health")
def health_check():
    """Liveness probe: answers without touching the database."""
    return {"status": "ok"}