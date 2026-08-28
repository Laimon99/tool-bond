# BondFX API

FastAPI transport, validation, Excel normalization and orchestration for the
BondFX educational PoC.

## Run locally

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PERSISTENCE_BACKEND="memory"
python -m uvicorn app.main:app --reload --port 8000
~~~

Interactive documentation is available at http://localhost:8000/docs.

## Endpoints

- GET /health
- GET /meta
- POST /run-valuation
- GET /runs/{run_id}
- POST /import/excel

The Excel endpoint accepts modern .xlsx and .xlsm files and maps supported demo
layouts to RunValuationRequest.

## Tests

~~~powershell
$env:PERSISTENCE_BACKEND="memory"
.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

The suite uses only synthetic fixtures from ../../examples/demo-data.
