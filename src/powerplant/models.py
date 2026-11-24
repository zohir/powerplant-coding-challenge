"""Domain schemas and enums for powerplant dispatch."""

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, Field, model_validator


class PlantType(StrEnum):
    """Supported powerplant types from the ENGIE challenge specification."""

    WINDTURBINE = "windturbine"
    GASFIRED = "gasfired"
    TURBOJET = "turbojet"


class Fuels(BaseModel):
    """Fuel prices and wind availability percentage."""

    gas: float = Field(alias="gas(euro/MWh)", ge=0)
    kerosine: float = Field(
        validation_alias=AliasChoices("kerosine(euro/MWh)", "kerosine(euro/Mwh)"),
        ge=0,
    )
    co2: float = Field(alias="co2(euro/ton)", ge=0)
    wind: float = Field(alias="wind(%)", ge=0, le=100)


class PowerPlant(BaseModel):
    """Single powerplant technical and economic parameters."""

    name: str = Field(min_length=1)
    type: PlantType
    efficiency: float = Field(gt=0, le=1)
    pmin: float = Field(ge=0)
    pmax: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_power_bounds(self) -> "PowerPlant":
        """Ensure minimum output never exceeds maximum output."""
        if self.pmin > self.pmax:
            raise ValueError(f"Plant {self.name!r} has pmin ({self.pmin}) > pmax ({self.pmax})")
        return self


class ProductionPlanRequest(BaseModel):
    """Incoming payload for POST /productionplan."""

    load: float = Field(ge=0)
    fuels: Fuels
    powerplants: list[PowerPlant]


class PlantOutput(BaseModel):
    """Dispatched power output for a single powerplant."""

    name: str
    p: float
