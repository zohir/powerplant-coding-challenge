# Powerplant Coding Challenge 

FastAPI REST service solving the ENGIE GEM SPaaS unit-commitment / merit-order dispatch problem on port `8888`.

- **Original Challenge Statement:** See [`docs/ORIGINAL_CHALLENGE_README.md`](docs/ORIGINAL_CHALLENGE_README.md) for the verbatim upstream ENGIE challenge description and acceptance criteria.
- **Engineering & AI Governance Rationale:** See [`docs/ENGINEERING_AND_AI_GOVERNANCE.md`](docs/ENGINEERING_AND_AI_GOVERNANCE.md) for why this project includes `Makefile` automation, a minimal non-root `Dockerfile`, fail-fast centralized config, zero hardcoded literals, exemplary `pytest` coverage, and an Agent-First / Human-Reviewed PR workflow.


## Build & Run

### Local (`uv` + `Makefile`)
```bash
make install   # Create .venv and install runtime + dev dependencies
make check     # Run ruff lint + pytest suite
make run       # Launch FastAPI on http://0.0.0.0:8888
```

> **Fail-Fast Configuration Note:** `src/powerplant/config.py` enforces a strict fail-fast policy with zero inline fallback defaults. `Makefile`, `Dockerfile`, and `.gitlab-ci.yml` inject `APP_HOST=0.0.0.0`, `APP_PORT=8888`, and `LOG_LEVEL=INFO` automatically. If running `pytest` or `uvicorn` directly outside `make`, export those variables first:
> ```bash
> export APP_HOST=0.0.0.0 APP_PORT=8888 LOG_LEVEL=INFO
> ```

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
3. **`pmin` Step-Down Back-Tracking:** When remaining load is positive but below the next merit-order plant's `pmin` (as in `example_payloads/payload2.json` where `20.0 MW < 100.0 MW`), already-dispatched preceding plants are stepped down in reverse merit order toward their own `pmin` so the next plant can be committed at `pmin` while matching `load` exactly (`380.0 + 100.0 = 480.0 MW`).
4. **Wind Turbine Dispatch & Curtailment:** Wind turbines generate at zero marginal cost with `effective_pmax = round(pmax * wind(%) / 100, 1)` and `effective_pmin = 0.0`, allowing partial curtailment if total available wind exceeds `load`.
5. **0.1 MW Precision:** Calculations run in integer tenths of a MW (`0.1 MW` units) to prevent IEEE-754 floating-point drift.
6. **Fuel Key Casing:** Accepts both `kerosine(euro/MWh)` (`example_payloads/`) and `kerosine(euro/Mwh)` (upstream `README.md` prose).
7. **Unachievable Load & Runtime Error Logging:** All payload validation (`422`), unachievable dispatch (`422`), and unhandled runtime errors (`500`) are logged as structured JSON to `stdout` and return explicit diagnostic details.
