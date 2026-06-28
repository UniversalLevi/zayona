"""Tests for the Zayona configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.config import (
    ConfigError,
    Settings,
    SettingsNotLoadedError,
    load_configuration,
    resolve_config_dir,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "configs"


@pytest.fixture(autouse=True)
def reset_settings() -> None:
    """Ensure Settings singleton is reset between tests."""
    Settings.reset()
    yield
    Settings.reset()


def test_load_real_configuration() -> None:
    """Load the repository configs/ directory successfully."""
    config = load_configuration(config_dir=CONFIG_DIR)

    assert config.app.name == "Zayona"
    assert config.app.environment == "development"
    assert config.app.provider == "ollama"
    assert config.app.host == "127.0.0.1"
    assert config.app.port == 8000


def test_model_role_resolves_correctly() -> None:
    """Validate planner model mapping from models.toml."""
    config = load_configuration(config_dir=CONFIG_DIR)

    assert config.models.planner.provider == "ollama"
    assert config.models.planner.model == "deepseek-r1:8b"
    assert config.models.coder.model == "qwen2.5-coder:7b"
    assert config.models.embeddings.model == "nomic-embed-text"


def test_workers_enabled_by_default() -> None:
    """Validate worker enable flags from workers.toml."""
    config = load_configuration(config_dir=CONFIG_DIR)

    assert config.workers.planner.enabled is True
    assert config.workers.coder.enabled is True
    assert config.workers.reviewer.enabled is True
    assert config.workers.utility.enabled is True


def test_logging_config() -> None:
    """Validate logging settings from logging.toml."""
    config = load_configuration(config_dir=CONFIG_DIR)

    assert config.logging.level == "INFO"
    assert config.logging.console is True
    assert config.logging.file.as_posix() == "logs/zayona.log"


def test_missing_config_directory_raises() -> None:
    """Raise ConfigError when config directory does not exist."""
    with pytest.raises(ConfigError, match="Configuration directory not found"):
        load_configuration(config_dir=Path("/nonexistent/config/dir"))


def test_missing_file_raises(tmp_path: Path) -> None:
    """Raise ConfigError when a required TOML file is missing."""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_configuration(config_dir=tmp_path)


def test_invalid_toml_raises(tmp_path: Path) -> None:
    """Raise ConfigError when TOML syntax is invalid."""
    (tmp_path / "default.toml").write_text("invalid [[toml", encoding="utf-8")
    for name in ("models.toml", "workers.toml", "logging.toml", "plugins.toml"):
        (tmp_path / name).write_text("", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_configuration(config_dir=tmp_path)


def test_invalid_field_raises(tmp_path: Path) -> None:
    """Raise ConfigError when validation fails on bad field values."""
    (tmp_path / "default.toml").write_text("port = 99999\n", encoding="utf-8")
    for name in ("models.toml", "workers.toml", "logging.toml", "plugins.toml"):
        (tmp_path / name).write_text("", encoding="utf-8")

    with pytest.raises(ConfigError, match="Configuration validation failed"):
        load_configuration(config_dir=tmp_path)


def test_overrides_merge_correctly() -> None:
    """Apply override dict to change configuration values."""
    config = load_configuration(
        config_dir=CONFIG_DIR,
        overrides={"app": {"environment": "testing"}},
    )

    assert config.app.environment == "testing"
    assert config.app.name == "Zayona"


def test_settings_load_and_get() -> None:
    """Settings.load() caches instance retrievable via Settings.get()."""
    loaded = Settings.load(config_dir=CONFIG_DIR)
    retrieved = Settings.get()

    assert loaded is retrieved
    assert retrieved.config.app.name == "Zayona"


def test_settings_get_before_load_raises() -> None:
    """Settings.get() raises when called before Settings.load()."""
    with pytest.raises(SettingsNotLoadedError, match="not been loaded"):
        Settings.get()


def test_resolve_config_dir_default() -> None:
    """Default config directory resolves to project configs/."""
    resolved = resolve_config_dir()

    assert resolved == PROJECT_ROOT / "configs"
