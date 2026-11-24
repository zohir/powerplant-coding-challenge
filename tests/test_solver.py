"""Unit tests for the merit-order + CO2 + pmin back-tracking solver."""

import pytest

from powerplant.models import Fuels, PlantType, PowerPlant, ProductionPlanRequest
from powerplant.solver import DispatchError, solve_production_plan


def _sample_fuels(wind: float = 60.0) -> Fuels:
    return Fuels.model_validate(
        {
            "gas(euro/MWh)": 13.4,
            "kerosine(euro/MWh)": 50.8,
            "co2(euro/ton)": 20.0,
            "wind(%)": wind,
        }
    )


def test_merit_order_prefers_wind_then_co2_adjusted_gas_then_turbojet() -> None:
    request = ProductionPlanRequest(
        load=120.0,
        fuels=_sample_fuels(wind=50.0),
        powerplants=[
            PowerPlant(name="tj1", type=PlantType.TURBOJET, efficiency=0.3, pmin=0, pmax=50),
            PowerPlant(name="gas1", type=PlantType.GASFIRED, efficiency=0.5, pmin=20, pmax=100),
            PowerPlant(name="wind1", type=PlantType.WINDTURBINE, efficiency=1.0, pmin=0, pmax=100),
        ],
    )
    result = solve_production_plan(request)
    assert [(item.name, item.p) for item in result] == [
        ("wind1", 50.0),
        ("gas1", 70.0),
        ("tj1", 0.0),
    ]


def test_pmin_backtracking_steps_down_previous_plant() -> None:
    request = ProductionPlanRequest(
        load=480.0,
        fuels=_sample_fuels(wind=0.0),
        powerplants=[
            PowerPlant(
                name="gas1", type=PlantType.GASFIRED, efficiency=0.53, pmin=100, pmax=460
            ),
            PowerPlant(
                name="gas2", type=PlantType.GASFIRED, efficiency=0.53, pmin=100, pmax=460
            ),
        ],
    )
    result = solve_production_plan(request)
    assert [(item.name, item.p) for item in result] == [
        ("gas1", 380.0),
        ("gas2", 100.0),
    ]
    assert round(sum(item.p for item in result), 1) == 480.0


def test_zero_load_dispatches_zero_across_all_plants() -> None:
    request = ProductionPlanRequest(
        load=0.0,
        fuels=_sample_fuels(wind=50.0),
        powerplants=[
            PowerPlant(name="wind1", type=PlantType.WINDTURBINE, efficiency=1.0, pmin=0, pmax=100),
            PowerPlant(name="gas1", type=PlantType.GASFIRED, efficiency=0.5, pmin=20, pmax=100),
        ],
    )
    result = solve_production_plan(request)
    assert all(item.p == 0.0 for item in result)


def test_unachievable_load_raises_transparent_dispatch_error() -> None:
    request = ProductionPlanRequest(
        load=500.0,
        fuels=_sample_fuels(wind=0.0),
        powerplants=[
            PowerPlant(name="gas1", type=PlantType.GASFIRED, efficiency=0.5, pmin=100, pmax=200),
        ],
    )
    with pytest.raises(DispatchError, match="Cannot dispatch load=500.0 MW"):
        solve_production_plan(request)
