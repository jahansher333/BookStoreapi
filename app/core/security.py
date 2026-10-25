"""Authentication dependencies for protected API routes."""

import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> None:
    """Require the configured API key for business operations."""
    configured_key = get_settings().api_key

    if configured_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if x_api_key is None or not secrets.compare_digest(
        x_api_key,
        configured_key.get_secret_value(),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
