"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized app configuration."""

    app_name: str = "EcoAI Commerce Engine"
    app_version: str = "1.0.0"
    environment: str = "development"

    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="ecoai_commerce", alias="MONGODB_DB_NAME")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        alias="GROQ_BASE_URL",
    )
    groq_model: str = Field(default="llama3-70b-8192", alias="GROQ_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()