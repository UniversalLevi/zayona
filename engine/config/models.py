"""Pydantic models representing Zayona configuration sections."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppConfig(BaseModel):
    """Application-level settings from default.toml."""

    model_config = ConfigDict(frozen=True)

    name: str = "Zayona"
    environment: str = "development"
    log_level: str = "INFO"
    data_directory: Path = Path("./data")
    plugin_directory: Path = Path("./plugins")
    provider: str = "ollama"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator("data_directory", "plugin_directory", mode="before")
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:
        """Normalize directory paths from TOML strings."""
        return Path(value)


class ModelRoleConfig(BaseModel):
    """Provider and model assignment for a single role."""

    model_config = ConfigDict(frozen=True)

    provider: str
    model: str


class ModelsConfig(BaseModel):
    """Model role mappings from models.toml."""

    model_config = ConfigDict(frozen=True)

    planner: ModelRoleConfig
    coder: ModelRoleConfig
    reviewer: ModelRoleConfig
    utility: ModelRoleConfig
    embeddings: ModelRoleConfig


class WorkerRoleConfig(BaseModel):
    """Enable/disable flag for a worker role."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True


class WorkersConfig(BaseModel):
    """Worker role settings from workers.toml."""

    model_config = ConfigDict(frozen=True)

    planner: WorkerRoleConfig
    coder: WorkerRoleConfig
    reviewer: WorkerRoleConfig
    utility: WorkerRoleConfig


class LoggingConfig(BaseModel):
    """Logging settings from logging.toml."""

    model_config = ConfigDict(frozen=True)

    level: str = "INFO"
    file: Path = Path("logs/zayona.log")
    console: bool = True

    @field_validator("file", mode="before")
    @classmethod
    def _coerce_log_path(cls, value: str | Path) -> Path:
        """Normalize log file path from TOML strings."""
        return Path(value)


class PluginsConfig(BaseModel):
    """Plugin settings placeholder for future configuration."""

    model_config = ConfigDict(frozen=True, extra="allow")


class Configuration(BaseModel):
    """Root configuration aggregate loaded from all TOML files."""

    model_config = ConfigDict(frozen=True)

    app: AppConfig
    models: ModelsConfig
    workers: WorkersConfig
    logging: LoggingConfig
    plugins: PluginsConfig
