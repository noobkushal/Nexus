"""Structured Logging Configuration."""
import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures structured console logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    logger = logging.getLogger("nexus")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()


def get_audit_logger() -> logging.Logger:
    """Returns specialized logger for auditing security and agent actions."""
    audit_logger = logging.getLogger("nexus.audit")
    return audit_logger
