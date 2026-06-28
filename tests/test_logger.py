"""Tests for the Zayona logging system."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from engine.config import Settings, SettingsNotLoadedError
from engine.config.models import LoggingConfig
from engine.utils.logger import (
    ROOT_LOGGER_NAME,
    get_logger,
    reset_logging,
    setup_logging,
)

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"


@pytest.fixture(autouse=True)
def reset_logging_state() -> None:
    """Ensure logging and settings are reset between tests."""
    reset_logging()
    Settings.reset()
    yield
    reset_logging()
    Settings.reset()


def _logging_config(
    tmp_path: Path,
    *,
    level: str = "INFO",
    console: bool = False,
    filename: str = "test.log",
) -> LoggingConfig:
    """Build a LoggingConfig that writes to a temporary file."""
    return LoggingConfig(
        level=level,
        file=tmp_path / filename,
        console=console,
    )


def test_setup_logging_with_explicit_config(tmp_path: Path) -> None:
    """Configure logging from an explicit LoggingConfig without Settings."""
    config = _logging_config(tmp_path)
    setup_logging(config=config)

    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    assert root_logger.handlers
    assert root_logger.level == logging.INFO


def test_file_handler_writes_component_prefix(tmp_path: Path) -> None:
    """File handler emits lines formatted as `[Component] message`."""
    config = _logging_config(tmp_path)
    setup_logging(config=config)

    logger = get_logger("Provider")
    logger.info("hello")

    for handler in logging.getLogger(ROOT_LOGGER_NAME).handlers:
        handler.flush()

    content = config.file.read_text(encoding="utf-8")
    assert "[Provider] hello" in content


def test_console_handler_attached_when_enabled(tmp_path: Path) -> None:
    """Attach a StreamHandler when console logging is enabled."""
    config = _logging_config(tmp_path, console=True)
    setup_logging(config=config)

    handlers = logging.getLogger(ROOT_LOGGER_NAME).handlers
    console_handlers = [
        handler for handler in handlers if type(handler) is logging.StreamHandler
    ]
    assert console_handlers


def test_no_console_handler_when_disabled(tmp_path: Path) -> None:
    """Skip StreamHandler when console logging is disabled."""
    config = _logging_config(tmp_path, console=False)
    setup_logging(config=config)

    handlers = logging.getLogger(ROOT_LOGGER_NAME).handlers
    console_handlers = [
        handler for handler in handlers if type(handler) is logging.StreamHandler
    ]
    assert not console_handlers


def test_log_level_filters_debug_messages(tmp_path: Path) -> None:
    """DEBUG messages are excluded when level is INFO."""
    config = _logging_config(tmp_path, level="INFO", console=False)
    setup_logging(config=config)

    logger = get_logger("Scheduler")
    logger.debug("hidden")
    logger.info("visible")

    for handler in logging.getLogger(ROOT_LOGGER_NAME).handlers:
        handler.flush()

    content = config.file.read_text(encoding="utf-8")
    assert "hidden" not in content
    assert "[Scheduler] visible" in content


def test_setup_logging_is_idempotent(tmp_path: Path) -> None:
    """Repeated setup without force does not duplicate handlers."""
    config = _logging_config(tmp_path)
    setup_logging(config=config)
    handler_count = len(logging.getLogger(ROOT_LOGGER_NAME).handlers)

    setup_logging(config=config)
    assert len(logging.getLogger(ROOT_LOGGER_NAME).handlers) == handler_count


def test_setup_logging_force_reconfigures(tmp_path: Path) -> None:
    """Force setup replaces existing handlers."""
    config = _logging_config(tmp_path, console=False)
    setup_logging(config=config)

    config_with_console = _logging_config(tmp_path, console=True, filename="other.log")
    setup_logging(config=config_with_console, force=True)

    handlers = logging.getLogger(ROOT_LOGGER_NAME).handlers
    console_handlers = [
        handler for handler in handlers if type(handler) is logging.StreamHandler
    ]
    assert console_handlers


def test_setup_logging_from_settings(tmp_path: Path) -> None:
    """Load logging configuration from Settings when config is omitted."""
    Settings.load(
        config_dir=CONFIG_DIR,
        overrides={
            "logging": {
                "file": str(tmp_path / "settings.log"),
                "console": False,
            }
        },
    )
    setup_logging()

    logger = get_logger("Worker")
    logger.info("from settings")

    for handler in logging.getLogger(ROOT_LOGGER_NAME).handlers:
        handler.flush()

    content = (tmp_path / "settings.log").read_text(encoding="utf-8")
    assert "[Worker] from settings" in content


def test_setup_logging_without_settings_raises() -> None:
    """Omitting config before Settings.load() raises SettingsNotLoadedError."""
    with pytest.raises(SettingsNotLoadedError, match="not been loaded"):
        setup_logging()


def test_missing_log_directory_is_created(tmp_path: Path) -> None:
    """Create parent directories for the configured log file path."""
    log_file = tmp_path / "nested" / "logs" / "zayona.log"
    config = LoggingConfig(level="INFO", file=log_file, console=False)
    setup_logging(config=config)

    logger = get_logger("Verifier")
    logger.info("passed")

    for handler in logging.getLogger(ROOT_LOGGER_NAME).handlers:
        handler.flush()

    assert log_file.is_file()
    assert "[Verifier] passed" in log_file.read_text(encoding="utf-8")


def test_reset_logging_clears_handlers(tmp_path: Path) -> None:
    """reset_logging removes handlers from the root Zayona logger."""
    config = _logging_config(tmp_path)
    setup_logging(config=config)
    assert logging.getLogger(ROOT_LOGGER_NAME).handlers

    reset_logging()
    assert not logging.getLogger(ROOT_LOGGER_NAME).handlers
