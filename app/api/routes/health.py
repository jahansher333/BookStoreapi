import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.session import check_database

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Liveness does not query the database; it only checks that the API process runs.
@router.get("/health/live")
def health_live() -> dict[str, str]:
    """Confirm that the API process is running."""
    return {"status": "ok"}


@router.get("/health/ready", response_model=None)
def health_ready() -> dict[str, str] | JSONResponse:
    """Confirm that the API can reach its database."""
    # Readiness is used by deployment platforms before sending traffic.
    try:
        check_database()
    except Exception:
        logger.exception("Database readiness check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "database": "error",
            },
        )

    return {
        "status": "ok",
        "database": "ok",
    }
"""Liveness and readiness endpoints for service monitoring."""
