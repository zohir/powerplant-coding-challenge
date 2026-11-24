# Powerplant Coding Challenge

FastAPI REST service solving the ENGIE GEM SPaaS unit-commitment / merit-order dispatch problem on port `8888`.

## Engineering Approach

This repository is structured in two deliberate commits:
1. **Commit 1 (`chore(structure)`):** Reusable `Python 3.12 + FastAPI + Docker + GitLab CI` service baseline (`config.py`, `logger.py`, `/health`, `Dockerfile`, `Makefile`, `AGENTS.md`).
2. **Commit 2 (`feat(solver)`):** Focused, from-scratch ENGIE dispatch implementation (`models.py`, `solver.py`, `POST /productionplan`, `pytest` suite) kept concise and line-by-line reviewable.

## Build & Run

### Local (`uv` + `Makefile`)
```bash
make install   # Create .venv and install runtime + dev dependencies
make check     # Run ruff lint + pytest suite
make run       # Launch FastAPI on http://0.0.0.0:8888
```

### Container (`Docker` / `Podman`)
```bash
make docker-build   # Build image (tar-streamed for macOS Podman safety)
make docker-run     # Run container exposing port 8888
make docker-smoke   # Verify GET http://127.0.0.1:8888/health
```

## API Usage

### `POST /productionplan`
```bash
curl -s -X POST http://127.0.0.1:8888/productionplan \
  -H "Content-Type: application/json" \
  -d @example_payloads/payload3.json
```

### `GET /health`
Returns `{"status": "ok"}` (HTTP `200`).

## Documented Assumptions

1. **CO2 Emissions:** `gasfired` plants include `0.3 ton/MWh` CO2 allowance cost (`gas / efficiency + 0.3 * co2`).
2. **Merit-Order Tie-Breaking & Output Order:** Plants are ordered by `(marginal_cost, -effective_pmax, input_index)`, and the response array follows merit-order sequence to match `example_payloads/response3.json` 1:1.
3. **0.1 MW Precision:** Calculations run in integer tenths of a MW (`0.1 MW` units); wind output (`pmax * wind(%) / 100`) is rounded to the nearest `0.1 MW`.
4. **Fuel Key Casing:** Accepts both `kerosine(euro/MWh)` (`example_payloads/`) and `kerosine(euro/Mwh)` (upstream `README.md` prose).
5. **Unachievable Load:** If fleet `pmin`/`pmax` bounds cannot satisfy `load` exactly, the API logs the exception with traceback and returns HTTP `422` with `{"detail": "..."}`.
