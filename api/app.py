from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from api.routes import health
from services.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI agent engineering platform for job search automation.",
        lifespan=lifespan,
    )

    app.include_router(health.router, prefix=settings.api_prefix)

    return app
