from fastapi import FastAPI

from app.api.routes import documents, health, ingestion, query
from app.core.config import Settings


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)
    app.state.settings = settings

    app.include_router(health.router)
    app.include_router(ingestion.router)
    app.include_router(query.router)
    app.include_router(documents.router)

    return app


app = create_app()
