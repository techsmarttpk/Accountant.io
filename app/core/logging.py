"""Structured logging configuration.

Production services must never leak raw exception text to end users (the
legacy tax_bot.py did exactly this). Instead, full detail goes to structured
logs keyed by a request/correlation id, and callers get a safe, generic
message plus an error code they can quote back to support.
"""

import logging
import sys

import structlog

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level.upper())

    # Quiet noisy third-party loggers unless we're actually debugging them.
    for noisy in ("httpx", "httpcore", "sqlalchemy.engine", "telegram"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING if not settings.debug else logging.INFO
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
