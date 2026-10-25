"""Alembic runtime configuration for SQLModel metadata and database URLs."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.models import Author, Book  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer the direct migration connection; use the application URL as fallback.
settings = get_settings()

migration_url = str(
    settings.migration_database_url or settings.database_url
)

# Escape '%' for Alembic's ConfigParser.
config.set_main_option(
    "sqlalchemy.url",
    migration_url.replace("%", "%%"),
)

# Imported models populate this metadata before autogeneration runs.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    # Offline mode generates SQL without opening a PostgreSQL connection.
    context.configure(
        url=migration_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""
    # NullPool keeps migration connections independent from API pooling.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()