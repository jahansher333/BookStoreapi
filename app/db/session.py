from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlmodel import Session

from app.core.config import get_settings

# The application uses the pooled database URL for normal requests.
settings = get_settings()

# SQLAlchemy's engine owns the connection pool used by API requests.
engine = create_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    connect_args={
        "connect_timeout": settings.db_connect_timeout,
        "application_name": settings.app_name,
    },
)


def get_session() -> Generator[Session, None, None]:
    """Yield a session and roll back if request handling fails."""
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


# FastAPI injects one request-scoped session into route handlers.
SessionDep = Annotated[Session, Depends(get_session)]


def check_database() -> None:
    """Run a lightweight query to verify database connectivity."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
"""Database engine and request-scoped SQLModel sessions."""
