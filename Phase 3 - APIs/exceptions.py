"""
Custom exception classes and global error handlers for the API.

These are used to provide structured, user-friendly error responses
instead of raw Python tracebacks.
"""

from fastapi import Request, status
import logging
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class BillingError(Exception):
    """Base exception for billing domain errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TripNotFoundError(BillingError):
    """Raised when a trip is not found."""

    def __init__(self, trip_id: str):
        super().__init__(f"Trip {trip_id} not found", status_code=404)


class ContractNotFoundError(BillingError):
    """Raised when no active contract exists for a client."""

    def __init__(self, client_id: str):
        super().__init__(f"No active contract for client {client_id}", status_code=404)


class InvalidClientError(BillingError):
    """Raised when client_id validation fails."""

    def __init__(self, client_id: str):
        super().__init__(f"Invalid client ID: {client_id}", status_code=400)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that catches any unhandled exceptions and returns
    a structured JSON error response.

    This is registered in the FastAPI app to catch all exceptions that aren't
    explicitly handled by route-level error handling.

    Behavior:
    - BillingError subclasses: Return their custom status code and message
    - ValueError or domain errors: Return 400 with error message
    - All other exceptions: Return 500 with generic message (don't leak internals)
    """
    if isinstance(exc, BillingError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "detail": exc.message,
                "path": str(request.url.path),
            },
        )
    elif isinstance(exc, RequestValidationError):
        # Pydantic validation errors (e.g., malformed JSON)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "ValidationError",
                "detail": "Invalid request payload",
                "errors": exc.errors(),
            },
        )
    elif isinstance(exc, ValueError):
        # Generic value errors from business logic
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "ValueError",
                "detail": str(exc),
                "path": str(request.url.path),
            },
        )
    else:
        # Catch-all for unexpected errors: log the full traceback for debugging
        logging.exception("Unhandled exception while processing request %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "detail": "An unexpected error occurred",
                "path": str(request.url.path),
            },
        )
