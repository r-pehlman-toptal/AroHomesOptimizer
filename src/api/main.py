from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request

from src.api.query_router import router as query_router
from src.api.analytics_router import router as analytics_router


logger = logging.getLogger("la_api")


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(title="LA Property Query Service")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        logger.info("Incoming %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled error for %s %s", request.method, request.url.path)
            raise
        duration_ms = (time.time() - start) * 1000.0
        logger.info(
            "Completed %s %s with status %s in %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(query_router)
    app.include_router(analytics_router)
    return app


app = create_app()

