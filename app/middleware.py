from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MAX_SUBMISSION_BYTES = 10_000


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized POSTs to /submissions before the body is parsed."""

    async def dispatch(self, request, call_next):
        if request.method == "POST" and request.url.path == "/submissions":
            length = request.headers.get("content-length")
            if length is None:
                return JSONResponse({"detail": "Content-Length header required"}, status_code=411)
            if not length.isdigit():
                return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
            if int(length) > MAX_SUBMISSION_BYTES:
                return JSONResponse({"detail": "Payload too large"}, status_code=413)
        return await call_next(request)