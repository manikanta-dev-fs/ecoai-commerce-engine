"""Global exception handlers for consistent API error responses."""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.exceptions import AIServiceError, DatabaseError


async def _json_error_response(
    request: Request,
    status_code: int,
    error: str,
    details: object,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "details": details,
            "path": str(request.url.path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach application-wide exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return await _json_error_response(
            request=request,
            status_code=422,
            error="ValidationError",
            details=exc.errors(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return await _json_error_response(
            request=request,
            status_code=exc.status_code,
            error="HTTPException",
            details=exc.detail,
        )

    @app.exception_handler(AIServiceError)
    async def ai_service_exception_handler(
        request: Request,
        exc: AIServiceError,
    ) -> JSONResponse:
        return await _json_error_response(
            request=request,
            status_code=502,
            error="AIServiceError",
            details=str(exc),
        )

    @app.exception_handler(DatabaseError)
    async def database_exception_handler(
        request: Request,
        exc: DatabaseError,
    ) -> JSONResponse:
        return await _json_error_response(
            request=request,
            status_code=503,
            error="DatabaseError",
            details=str(exc),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return await _json_error_response(
            request=request,
            status_code=500,
            error="InternalServerError",
            details="Unexpected server error",
        )
