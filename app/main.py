"""Application entry point and top-level FastAPI configuration."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import authors, books, health
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import check_database, engine

# Load settings and configure logging before creating the application.
settings = get_settings()
setup_logging(settings.log_level)

# This logger records startup and shutdown events for operators.
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Check the database at startup and release resources at shutdown."""
    try:
        # Fail startup early when the configured database is unavailable.
        try:
            check_database()
        except Exception:
            logger.exception("Database startup check failed")
            raise

        # Keep the application running while FastAPI serves requests.
        logger.info("Database connection verified during startup")
        yield
    finally:
        # Close pooled connections cleanly when the process stops.
        engine.dispose()
        logger.info("Database connection pool disposed")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# Install global handlers before requests reach any registered router.
register_exception_handlers(app)

# Routers turn service functions into documented HTTP endpoints.
app.include_router(health.router)
app.include_router(authors.router)
app.include_router(books.router)