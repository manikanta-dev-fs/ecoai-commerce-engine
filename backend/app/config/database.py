"""MongoDB client lifecycle and database dependency helpers."""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import get_settings


class MongoDB:
    """Manage MongoDB async connection lifecycle."""

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        settings = get_settings()
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.database = self.client[settings.mongodb_db_name]
        await self.database.command("ping")

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None
        self.database = None


mongodb = MongoDB()


def get_database() -> AsyncIOMotorDatabase:
    """Return active database instance for dependencies/services."""
    if mongodb.database is None:
        raise RuntimeError("Database connection has not been initialized")
    return mongodb.database