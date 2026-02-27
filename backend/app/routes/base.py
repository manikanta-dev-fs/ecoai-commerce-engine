"""Central router registry."""

from fastapi import APIRouter

from app.routes.ai_routes import router as ai_router
from app.routes.health_routes import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(ai_router)