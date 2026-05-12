from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "JobPilot AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    API_PREFIX: str = "/api/v1"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "qwen-plus"

    DATABASE_URL: str = ""

    PLAYWRIGHT_HEADLESS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()


def get_settings():
    return settings