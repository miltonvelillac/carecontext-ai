from fastapi import FastAPI

from app.core.config import Settings
from app.schemas.health import HealthResponse


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="CareContext AI API", version="0.1.0")
    app.state.settings = settings

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app


app = create_app()

