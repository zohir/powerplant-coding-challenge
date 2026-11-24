"""Smoke tests for the reusable service skeleton."""

from fastapi import APIRouter
from fastapi.testclient import TestClient

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
    response = client.get("/_test-boom")
    assert response.status_code == 500
    assert response.json() == {"detail": "boom diagnostic detail"}
