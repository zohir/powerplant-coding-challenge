"""Integration tests for POST /productionplan using upstream example payloads."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from powerplant.main import app

client = TestClient(app)
PAYLOADS_DIR = Path(__file__).resolve().parent.parent / "example_payloads"


def _load_json(filename: str) -> dict | list:
    return json.loads((PAYLOADS_DIR / filename).read_text(encoding="utf-8"))


def test_payload1_exact_load_and_bounds() -> None:
    payload = _load_json("payload1.json")
    response = client.post("/productionplan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert round(sum(item["p"] for item in data), 1) == payload["load"]


def test_payload2_wind_zero_triggers_pmin_backtracking() -> None:
    payload = _load_json("payload2.json")
    response = client.post("/productionplan", json=payload)
    assert response.status_code == 200
    data = response.json()
    by_name = {item["name"]: item["p"] for item in data}
    assert by_name["gasfiredbig1"] == 380.0
    assert by_name["gasfiredbig2"] == 100.0
    assert round(sum(item["p"] for item in data), 1) == 480.0


def test_payload3_matches_upstream_response3_exactly() -> None:
    payload = _load_json("payload3.json")
    expected = _load_json("response3.json")
    response = client.post("/productionplan", json=payload)
    assert response.status_code == 200
    assert response.json() == expected


def test_kerosine_lowercase_mwh_alias_is_accepted() -> None:
    payload = _load_json("payload1.json")
    payload["fuels"]["kerosine(euro/Mwh)"] = payload["fuels"].pop("kerosine(euro/MWh)")
    response = client.post("/productionplan", json=payload)
    assert response.status_code == 200


def test_invalid_plant_bounds_returns_422() -> None:
    payload = _load_json("payload1.json")
    payload["powerplants"][0]["pmin"] = 999
    response = client.post("/productionplan", json=payload)
    assert response.status_code == 422


def test_unachievable_load_returns_422_with_diagnostic_detail() -> None:
    payload = _load_json("payload1.json")
    payload["load"] = 99999
    response = client.post("/productionplan", json=payload)
    assert response.status_code == 422
    assert "Cannot dispatch load=99999" in response.json()["detail"]
