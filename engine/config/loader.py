"""Configuration loader for reading and validating TOML files."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from engine.config.models import (
    AppConfig,
    Configuration,
    LoggingConfig,
    ModelsConfig,
    PluginsConfig,
    WorkersConfig,
)

CONFIG_FILES = {
    "app": "default.toml",
    "models": "models.toml",
    "workers": "workers.toml",
    "logging": "logging.toml",
    "plugins": "plugins.toml",
}


class ConfigError(Exception):
    """Raised when configuration files cannot be read or validated."""


def _project_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).resolve().parents[2]


def resolve_config_dir(config_dir: Path | None = None) -> Path:
    """Resolve the configuration directory from argument or environment."""
    if config_dir is not None:
        return config_dir

    env_dir = os.environ.get("ZAYONA_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    return _project_root() / "configs"


def load_toml_file(path: Path) -> dict[str, Any]:
    """Read a single TOML file and return its contents as a dictionary."""
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc

    return data if isinstance(data, dict) else {}


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override values into a base dictionary."""
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_section(
    config_dir: Path,
    section: str,
    overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    """Load one configuration section and apply optional overrides."""
    filename = CONFIG_FILES[section]
    data = load_toml_file(config_dir / filename)

    section_overrides = overrides.get(section, {}) if overrides else {}
    if section_overrides:
        data = _deep_merge(data, section_overrides)

    return data


def load_configuration(
    config_dir: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> Configuration:
    """Load, validate, and return the full Zayona configuration."""
    resolved_dir = resolve_config_dir(config_dir)

    if not resolved_dir.is_dir():
        raise ConfigError(f"Configuration directory not found: {resolved_dir}")

    try:
        return Configuration(
            app=AppConfig.model_validate(_load_section(resolved_dir, "app", overrides)),
            models=ModelsConfig.model_validate(
                _load_section(resolved_dir, "models", overrides)
            ),
            workers=WorkersConfig.model_validate(
                _load_section(resolved_dir, "workers", overrides)
            ),
            logging=LoggingConfig.model_validate(
                _load_section(resolved_dir, "logging", overrides)
            ),
            plugins=PluginsConfig.model_validate(
                _load_section(resolved_dir, "plugins", overrides)
            ),
        )
    except ValidationError as exc:
        raise ConfigError(f"Configuration validation failed: {exc}") from exc
