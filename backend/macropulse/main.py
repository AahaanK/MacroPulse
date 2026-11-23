from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from macropulse.api.routers import (
    assets,
    correlations,
    data_status,
    event_studies,
    events,
    health,
    indicators,
    market_data,
    regimes,
    reports,
    research,
    surprises,
)
from macropulse.config import settings
from macropulse.db.init_db import init_db
from macropulse.ingest.pipeline import IngestionPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    init_db()
    # Check if DB has assets/indicators, otherwise seed from demo
    pipeline = IngestionPipeline()
    try:
        pipeline.ingest_all()
    finally:
        pipeline.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Macroeconomic Event Impact & Market Sentiment Research Platform",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure standard JSON error shape throughout the API."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
                "details": None,
            }
        },
    )


# Mount routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(indicators.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(market_data.router, prefix="/api")
app.include_router(event_studies.router, prefix="/api")
app.include_router(data_status.router, prefix="/api")
app.include_router(surprises.router, prefix="/api")
app.include_router(correlations.router, prefix="/api")
app.include_router(regimes.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_health": "/api/health",
    }
