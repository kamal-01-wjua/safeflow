# apps/api/app/error_handlers.py
"""
SafeFlow Centralized Error Handlers
=====================================
Registered on the FastAPI app in main.py.
All errors return a consistent JSON envelope:

    {
        "error": {
            "code": "NOT_FOUND",
            "message": "Transaction not found",
            "status": 404
        }
    }
"""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("safeflow.api")


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "status": status_code,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers on the app instance.
    Call this in main.py after creating the app.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle all HTTPException (404, 403, 401, etc.)"""
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMITED",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return _error_response(code, message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic request validation errors (422)."""
        errors = exc.errors()
        # Build a readable message from the first error
        if errors:
            first = errors[0]
            loc = " → ".join(str(x) for x in first.get("loc", []))
            msg = first.get("msg", "Validation error")
            message = f"{loc}: {msg}" if loc else msg
        else:
            message = "Request validation failed"

        return _error_response(
            "VALIDATION_ERROR",
            message,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unhandled exceptions — log and return 500."""
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            str(exc),
            traceback.format_exc(),
        )
        return _error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred. Check server logs.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
