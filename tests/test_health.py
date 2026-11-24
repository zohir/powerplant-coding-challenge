"""Smoke tests for the reusable service skeleton and fail-fast config."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from powerplant.config import Settings
from powerplant.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unhandled_exception_surfaces_real_detail() -> None:
    router = APIRouter()

    @router.get("/_test-boom")
    def boom() -> None:
        raise RuntimeError("boom diagnostic detail")

    app.include_router(router)
    try:
        response = client.get("/_test-boom")
        assert response.status_code == 500
        assert response.json() == {"detail": "boom diagnostic detail"}
    finally:
        app.router.routes.pop()


@pytest.mark.parametrize("missing_var", ["APP_PORT", "APP_HOST", "LOG_LEVEL"])
def test_settings_from_env_fails_fast_when_missing(
    monkeypatch: pytest.MonkeyPatch, missing_var: str
) -> None:
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("APP_PORT", "8888")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.delenv(missing_var)

    with pytest.raises(RuntimeError, match=f"Missing required environment variable: {missing_var}"):
        Settings.from_env()
