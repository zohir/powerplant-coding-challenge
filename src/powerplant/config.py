"""Centralized, fail-fast application configuration."""

import os
from dataclasses import dataclass

CO2_TONS_PER_MWH = 0.3
POWER_UNITS_PER_MW = 10
PERCENT_DIVISOR = 100.0


def _require_env(name: str) -> str:
    """Return a required non-empty environment variable or fail fast."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded once at startup from environment variables."""

    app_host: str
    app_port: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Build and validate runtime settings from required environment variables."""
        raw_port = _require_env("APP_PORT")
        try:
            app_port = int(raw_port)
        except ValueError as exc:
            raise ValueError(f"Invalid APP_PORT={raw_port!r}: must be an integer") from exc
        if not 1 <= app_port <= 65535:
            raise ValueError(f"Invalid APP_PORT={app_port}: must be between 1 and 65535")

        app_host = _require_env("APP_HOST")
        log_level = _require_env("LOG_LEVEL").upper()

        return cls(app_host=app_host, app_port=app_port, log_level=log_level)


settings = Settings.from_env()
