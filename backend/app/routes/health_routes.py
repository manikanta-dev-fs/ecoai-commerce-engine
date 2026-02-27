"""Health check routes."""

from fastapi import APIRouter

from app.controllers.health_controller import get_health_status
from app.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic liveness and readiness endpoint."""
    return await get_health_status()