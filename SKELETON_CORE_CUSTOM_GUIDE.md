# Skeleton Reuse Guide (Core vs Custom)

This document defines how to reuse the project across multiple clients without forking the codebase.

## Core (reusable, client-agnostic)
- Contracts:
  - `contracts/run_valuation.request.schema.json`
  - `contracts/run_valuation.response.schema.json`
- Quant engine:
  - `services/quant-engine/quant_engine/valuation.py`
- API orchestration:
  - `apps/api/app/core/orchestrators.py`
- API transport:
  - `apps/api/app/main.py`
- Validation/storage baseline:
  - `apps/api/app/schema_validation.py`
  - `apps/api/app/run_storage.py`
  - `apps/api/app/persistence/*`

## Custom (client-specific)
- Client adapters:
  - `apps/api/app/client_modules/*.py`
- Client assets/docs:
  - `clients/<client_id>/`

## Extension points
- Input normalization customization:
  - override `ClientAdapter.normalize_excel_import(...)`
- Run payload customization:
  - override `ClientAdapter.preprocess_run_payload(...)`
- Response customization:
  - override `ClientAdapter.postprocess_run_response(...)`
  - override `ClientAdapter.postprocess_import_response(...)`
- Persistence backend swap (DB-later):
  - implement new adapter under `apps/api/app/persistence/`
  - map it in `apps/api/app/persistence/registry.py`

## Practical flow
1. API receives request (`main.py`).
2. Core orchestrator resolves client adapter (`core/orchestrators.py`).
3. Core valuation engine runs (`valuation_service.py` + quant engine).
4. Adapter applies client-specific post-processing.
5. API returns contract-compliant response.

## Rule of thumb
- If logic can apply to all clients, keep it in Core.
- If logic is specific to one client/workflow, keep it in Custom adapter.
