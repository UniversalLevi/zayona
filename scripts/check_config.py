#!/usr/bin/env python3
"""Print a summary of the loaded Zayona configuration."""

from __future__ import annotations

import sys

from engine.config import ConfigError, Settings


def main() -> int:
    """Load and display configuration. Returns 0 on success, 1 on failure."""
    try:
        settings = Settings.load()
        config = settings.config
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    print(f"Application: {config.app.name}")
    print(f"Environment: {config.app.environment}")
    print(f"Provider:    {config.app.provider}")
    print(f"Host:        {config.app.host}:{config.app.port}")
    print(f"Data dir:    {config.app.data_directory}")
    print()
    print("Models:")
    for role in ("planner", "coder", "reviewer", "utility", "embeddings"):
        model_config = getattr(config.models, role)
        print(f"  {role:12} {model_config.provider}/{model_config.model}")
    print()
    print("Workers:")
    for role in ("planner", "coder", "reviewer", "utility"):
        worker_config = getattr(config.workers, role)
        status = "enabled" if worker_config.enabled else "disabled"
        print(f"  {role:12} {status}")
    print()
    print("Logging:")
    print(f"  Level:   {config.logging.level}")
    print(f"  File:    {config.logging.file}")
    print(f"  Console: {config.logging.console}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
