"""FastAPI application entrypoint and global error boundary."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from powerplant.logger import get_logger
from powerplant.models import PlantOutput, ProductionPlanRequest
from powerplant.solver import DispatchError, solve_production_plan

logger = get_logger(__name__)
app = FastAPI(title="Powerplant Service", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Log invalid payload schema/domain errors and return 422 details transparently."""
    errors = jsonable_encoder(exc.errors())
    logger.warning(
        "Payload validation failed on %s %s: %s",
        request.method,
        request.url.path,
        errors,
    )
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected errors with traceback and surface the real error detail."""
    logger.error(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok"}


@app.post("/productionplan", response_model=list[PlantOutput])
async def production_plan(payload: ProductionPlanRequest) -> list[PlantOutput] | JSONResponse:
    """Calculate merit-order powerplant dispatch for the requested load."""
    try:
        plan = solve_production_plan(payload)
        logger.info("Dispatched load=%.1f MW across %d plants", payload.load, len(plan))
        return plan
    except DispatchError as exc:
        logger.error("Dispatch failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=422, content={"detail": str(exc)})
