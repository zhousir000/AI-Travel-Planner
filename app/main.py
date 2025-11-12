from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.v1.router import api_router
from .core.config import settings
from .db.init_db import init_db
from .views.router import view_router


def create_app() -> FastAPI:
    """Application factory for FastAPI."""
    app = FastAPI(
        title="AI Travel Planner",
        description="AI-assisted travel planning with itinerary, budgeting, and voice input.",
        version="0.1.0",
        docs_url=settings.api_docs_url,
        redoc_url=settings.api_redoc_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(view_router)

    app.mount(
        "/static",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()

    return app


app = create_app()
