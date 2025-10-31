from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import excel_management, exports, price_tracking
from .core.config import get_settings
from .database import init_db

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(exports.router, prefix=settings.api_prefix)
    app.include_router(price_tracking.router, prefix=settings.api_prefix)
    app.include_router(excel_management.router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def _startup() -> None:
        logger.info("Initializing database")
        init_db()

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
