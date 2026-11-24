"""From-scratch merit-order unit commitment solver with CO2 and pmin back-tracking."""

from dataclasses import dataclass

from powerplant.config import CO2_TONS_PER_MWH, PERCENT_DIVISOR, POWER_UNITS_PER_MW
from powerplant.models import Fuels, PlantOutput, PlantType, PowerPlant, ProductionPlanRequest


class DispatchError(Exception):
    """Raised when fleet capacity and pmin bounds cannot match the requested load."""


@dataclass(frozen=True)
class _MeritEntry:
    """Internal merit-order representation in integer tenths of a MW."""

    cost: float
    pmin_t: int
    pmax_t: int
    index: int
    plant: PowerPlant


def _to_tenths(mw: float) -> int:
    return round(mw * POWER_UNITS_PER_MW)


def _from_tenths(units: int) -> float:
    return round(units / POWER_UNITS_PER_MW, 1)


def _marginal_cost(plant: PowerPlant, fuels: Fuels) -> float:
    if plant.type == PlantType.WINDTURBINE:
        return 0.0
    if plant.type == PlantType.GASFIRED:
        return (fuels.gas / plant.efficiency) + (CO2_TONS_PER_MWH * fuels.co2)
    return fuels.kerosine / plant.efficiency


def _effective_bounds_tenths(plant: PowerPlant, fuels: Fuels) -> tuple[int, int]:
    if plant.type == PlantType.WINDTURBINE:
        pmax_t = _to_tenths(plant.pmax * (fuels.wind / PERCENT_DIVISOR))
        pmin_t = min(_to_tenths(plant.pmin), pmax_t)
        return pmin_t, pmax_t
    return _to_tenths(plant.pmin), _to_tenths(plant.pmax)


def solve_production_plan(request: ProductionPlanRequest) -> list[PlantOutput]:
    """Compute merit-order dispatch in 0.1 MW units matching request.load exactly."""
    merit = [
        _MeritEntry(
            cost=_marginal_cost(plant, request.fuels),
            pmin_t=bounds[0],
            pmax_t=bounds[1],
            index=idx,
            plant=plant,
        )
        for idx, plant in enumerate(request.powerplants)
        for bounds in [_effective_bounds_tenths(plant, request.fuels)]
    ]
    merit.sort(key=lambda e: (e.cost, -e.pmax_t, e.index))

    rem = _to_tenths(request.load)
    allocated = [0] * len(merit)

    for i, entry in enumerate(merit):
        if rem == 0:
            break
        if entry.pmax_t == 0:
            continue
        if rem >= entry.pmin_t:
            take = min(rem, entry.pmax_t)
            allocated[i] = take
            rem -= take
            continue

        deficit = entry.pmin_t - rem
        slack = sum(allocated[j] - merit[j].pmin_t for j in range(i) if allocated[j] > 0)
        if slack >= deficit:
            need = deficit
            for j in range(i - 1, -1, -1):
                if allocated[j] == 0 or need == 0:
                    continue
                reducible = allocated[j] - merit[j].pmin_t
                if reducible > 0:
                    drop = min(reducible, need)
                    allocated[j] -= drop
                    need -= drop
            allocated[i] = entry.pmin_t
            rem = 0

    if rem != 0:
        raise DispatchError(
            f"Cannot dispatch load={request.load} MW with available fleet capacity/pmin bounds "
            f"(remaining={_from_tenths(rem):.1f} MW)"
        )

    return [
        PlantOutput(name=entry.plant.name, p=_from_tenths(allocated[i]))
        for i, entry in enumerate(merit)
    ]
