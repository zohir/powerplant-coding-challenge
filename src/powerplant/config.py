"""Centralized, fail-fast application configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded once at startup from environment variables."""

    app_host: str
    app_port: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Build and validate runtime settings."""
        raw_port = os.getenv("APP_PORT", "8888")
        try:
            app_port = int(raw_port)
        except ValueError as exc:
            raise ValueError(f"Invalid APP_PORT={raw_port!r}: must be an integer") from exc
        if not 1 <= app_port <= 65535:
            raise ValueError(f"Invalid APP_PORT={app_port}: must be between 1 and 65535")

        app_host = os.getenv("APP_HOST", "0.0.0.0").strip()
        if not app_host:
            raise ValueError("APP_HOST must not be empty")

        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if not log_level:
            raise ValueError("LOG_LEVEL must not be empty")

        return cls(app_host=app_host, app_port=app_port, log_level=log_level)


settings = Settings.from_env()
