"""Optional API key gate via X-API-KEY header when a key env var is set."""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def _configured_api_key() -> str | None:
    return os.getenv("CASES_DB_API_KEY") or os.getenv("API_KEY")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        configured_key = _configured_api_key()
        if configured_key is None or request.url.path == "/health":
            return await call_next(request)

        if request.headers.get("X-API-KEY") != configured_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
