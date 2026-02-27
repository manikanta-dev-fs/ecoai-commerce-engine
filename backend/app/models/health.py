"""Shared API response models."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: datetime