from __future__ import annotations

import logging
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Load .env from project root so API works regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

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

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {"service": "LA Property Query Service", "docs": "/docs", "health": "/health"}

    @app.get("//docs", include_in_schema=False)
    def redirect_double_slash_docs():
        return RedirectResponse(url="/docs", status_code=302)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(query_router)
    app.include_router(analytics_router)

    # Web visualizations (comps, ZIP/city/year, map)
    web_dir = _PROJECT_ROOT / "web"
    if web_dir.is_dir():
        app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")
        @app.get("/app", tags=["web"])
        def viz_app():
            return FileResponse(web_dir / "index.html")
        @app.get("/viz", tags=["web"])
        def viz_redirect():
            return RedirectResponse(url="/app", status_code=302)

    return app


app = create_app()

