"""Controller layer for health and readiness checks."""

from datetime import datetime, timezone

from app.config.database import mongodb
from app.config.settings import get_settings
from app.models.health import HealthResponse


async def get_health_status() -> HealthResponse:
    """Check service and dependency readiness."""
    db_state = "disconnected"

    if mongodb.database is not None:
        try:
            await mongodb.database.command("ping")
            db_state = "connected"
        except Exception:
            db_state = "unhealthy"

    settings = get_settings()
    return HealthResponse(
        status="ok" if db_state == "connected" else "degraded",
        service=settings.app_name,
        database=db_state,
        timestamp=datetime.now(timezone.utc),
    )