from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health, ingestion, query
from app.composition.container import AppContainer
from app.core.config import Settings


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)
    app.state.settings = settings
    app.state.container = AppContainer(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in settings.cors_allowed_origins.split(",")
            if origin.strip()
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ingestion.router)
    app.include_router(query.router)
    app.include_router(documents.router)

    return app


app = create_app()
