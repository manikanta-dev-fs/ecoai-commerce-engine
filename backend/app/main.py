"""FastAPI application bootstrap for EcoAI Commerce Engine."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

# Load .env before settings are consumed by app components.
load_dotenv()

from app.config.database import mongodb
from app.config.settings import get_settings
from app.routes.base import api_router
from app.utils.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Handle startup/shutdown resources."""
    await mongodb.connect()
    try:
        yield
    finally:
        await mongodb.close()


def create_app() -> FastAPI:
    """Application factory for easier testing and extensibility."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {"message": f"{settings.app_name} API"}

    return app


app = create_app()
