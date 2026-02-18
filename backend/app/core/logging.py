"""Structured logging with loguru."""

import sys
from loguru import logger
from app.core.config import get_settings


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console handler — human-readable for development
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG,
    )

    # File handler — JSON-structured for machine parsing
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        level="DEBUG" if settings.DEBUG else "INFO",
        format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {name}:{function}:{line} | {message}",
        rotation="50 MB",
        retention="14 days",
        compression="gz",
        enqueue=True,  # thread-safe
    )

    logger.info(f"Logging initialized at level={settings.LOG_LEVEL}")


def get_logger(name: str = "f1_rag"):
    """Get a named logger instance."""
    return logger.bind(module=name)
