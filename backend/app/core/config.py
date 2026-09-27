from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
ENV_FILE = (BACKEND_DIRECTORY / ".env").resolve()


class Settings(BaseSettings):
    """Configuration loaded from backend/.env when it exists."""

    app_name: str = "DataPilot AI API"
    environment: str = "development"
    database_url: str = Field(validation_alias="DATABASE_URL")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
