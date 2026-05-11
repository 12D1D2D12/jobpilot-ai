from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JobPilot AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    openai_api_key: str | None = None
    langgraph_checkpointer_url: str | None = None
    database_url: str = "postgresql+asyncpg://jobpilot:jobpilot@localhost:5432/jobpilot"
    playwright_headless: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
