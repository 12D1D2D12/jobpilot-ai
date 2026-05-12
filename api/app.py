from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from api.routes import health, job, jobs, resume
from database.init_db import init_db
from services.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_db()
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI agent engineering platform for job search automation.",
        lifespan=lifespan,
    )

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(job.router, prefix=settings.API_PREFIX)
    app.include_router(jobs.router, prefix=settings.API_PREFIX)
    app.include_router(resume.router, prefix=settings.API_PREFIX)

    return app
