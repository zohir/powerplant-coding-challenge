"""FastAPI application entrypoint and global error boundary."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from powerplant.logger import get_logger

logger = get_logger(__name__)
app = FastAPI(title="Powerplant Service", version="0.1.0")


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
