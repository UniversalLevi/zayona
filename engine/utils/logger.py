"""Component logging utilities for Zayona."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from engine.config.models import LoggingConfig
from engine.config.settings import Settings

ROOT_LOGGER_NAME = "zayona"

_configured = False


class ComponentFormatter(logging.Formatter):
    """Format log records with a component prefix stripped from the logger name."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a log line as `[Component] message`."""
        component = record.name.removeprefix(f"{ROOT_LOGGER_NAME}.")
        if component == record.name:
            component = ROOT_LOGGER_NAME
        return f"[{component}] {record.getMessage()}"


def _resolve_level(level_name: str) -> int:
    """Convert a config level string to a logging level integer."""
    level = logging.getLevelName(level_name.upper())
    if isinstance(level, int):
        return level
    return logging.INFO


def _attach_handlers(logger: logging.Logger, config: LoggingConfig) -> None:
    """Attach console and file handlers to the root Zayona logger."""
    formatter = ComponentFormatter()

    if config.console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if config.file:
        log_path = Path(config.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def setup_logging(
    config: LoggingConfig | None = None,
    *,
    force: bool = False,
) -> None:
    """Configure Zayona logging from LoggingConfig.

    Uses ``LoggingConfig.level`` from ``configs/logging.toml`` as the
    authoritative log level. ``AppConfig.log_level`` is not used here.

    If ``config`` is omitted, reads from ``Settings.get().config.logging``.
    """
    global _configured

    if _configured and not force:
        return

    if config is None:
        config = Settings.get().config.logging

    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(_resolve_level(config.level))
    logger.propagate = False

    _attach_handlers(logger, config)
    _configured = True


def get_logger(component: str) -> logging.Logger:
    """Return a component logger under the ``zayona`` hierarchy."""
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{component}")


def reset_logging() -> None:
    """Clear logging configuration. Intended for tests only."""
    global _configured

    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    _configured = False
