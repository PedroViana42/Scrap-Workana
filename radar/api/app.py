from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from radar.api.routes import health, jobs, sources, stats
from radar.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Radar API",
        version="0.1.0",
        description="Read-only HTTP API for Radar jobs, sources, and operational stats.",
    )
    if settings.api_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.api_cors_origins),
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["*"],
        )
    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(sources.router)
    app.include_router(stats.router)
    return app


app = create_app()
