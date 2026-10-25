"""Application logging configuration."""

import logging


def setup_logging(level: str) -> None:
    """Configure the root logger using the requested log level."""
    # A single root configuration gives all modules the same log format.
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
