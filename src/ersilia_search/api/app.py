"""FastAPI application factory for the Ersilia search engine."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ersilia_search.api.routes import router
from ersilia_search.io.loader import get_catalog
from ersilia_search.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the catalog cache at startup; log but don't crash if S3 is down."""
    try:
        get_catalog()
    except Exception as exc:
        logger.warning(
            f"Catalog warm-up failed at startup ({exc}); will retry on first request"
        )
    yield


app = FastAPI(
    title="Ersilia Search",
    description="Search the Ersilia Model Hub by keyword and structured filters.",
    lifespan=lifespan,
)
app.include_router(router)
