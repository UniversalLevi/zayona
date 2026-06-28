"""Settings singleton providing access to loaded configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.config.loader import load_configuration
from engine.config.models import Configuration


class SettingsNotLoadedError(RuntimeError):
    """Raised when Settings.get() is called before Settings.load()."""


class Settings:
    """Singleton wrapper around the loaded Configuration instance."""

    _instance: Settings | None = None

    def __init__(self, configuration: Configuration) -> None:
        """Initialize settings with a validated configuration."""
        self._configuration = configuration

    @classmethod
    def load(
        cls,
        config_dir: Path | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> Settings:
        """Load configuration and cache the Settings singleton."""
        configuration = load_configuration(config_dir=config_dir, overrides=overrides)
        cls._instance = cls(configuration)
        return cls._instance

    @classmethod
    def get(cls) -> Settings:
        """Return the cached Settings instance."""
        if cls._instance is None:
            raise SettingsNotLoadedError(
                "Settings have not been loaded. Call Settings.load() first."
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clear the cached singleton. Intended for tests only."""
        cls._instance = None

    @property
    def config(self) -> Configuration:
        """Return the loaded configuration aggregate."""
        return self._configuration
