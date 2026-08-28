"""Application service for run valuation endpoints."""

from __future__ import annotations

from datetime import datetime, timezone, date
from typing import Any, Dict, Tuple
import uuid

# Import config first to initialize local PYTHONPATH bootstrap for quant_engine.
from .config import QUANT_ENGINE_SRC  # noqa: F401
from quant_engine import run_valuation

from .run_storage import load_run_response, save_run_artifact
from .schema_validation import validate_request, validate_response


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_date(value: Any, default: str) -> str:
    if isinstance(value, str):
        try:
            date.fromisoformat(value)
            return value
        except ValueError:
            return default
    return default


def _safe_input_summary(payload: Dict[str, Any], cashflow_count: int = 0) -> Dict[str, Any]:
    valuation = payload.get("valuation", {}) if isinstance(payload, dict) else {}
    price_input = valuation.get("price_input", {})
    fx_forward = valuation.get("fx_forward_curve", {})

    input_mode = payload.get("input_mode", "manual") if isinstance(payload, dict) else "manual"
    if input_mode not in {"manual", "excel_import"}:
        input_mode = "manual"

    price_input_type = price_input.get("type", "clean_price")
    if price_input_type not in {"clean_price", "ytm"}:
        price_input_type = "clean_price"

    fx_interpolation = fx_forward.get("interpolation", "linear")
    if fx_interpolation not in {"linear", "loglinear"}:
        fx_interpolation = "linear"

    valuation_options = valuation.get("options", {})
    fx_rate_side = valuation_options.get("fx_rate_side", "ask")
    if fx_rate_side not in {"mid", "bid", "ask"}:
        fx_rate_side = "ask"

    return {
        "input_mode": input_mode,
        "settlement_date": _safe_date(valuation.get("settlement_date"), "1970-01-01"),
        "price_input_type": price_input_type,
        "fx_interpolation": fx_interpolation,
        "fx_rate_side": fx_rate_side,
        "cashflow_count": max(0, int(cashflow_count)),
    }


def _round_numbers(value: Any, decimals: int) -> Any:
    if isinstance(value, float):
        return round(value, decimals)
    if isinstance(value, list):
        return [_round_numbers(v, decimals) for v in value]
    if isinstance(value, dict):
        return {k: _round_numbers(v, decimals) for k, v in value.items()}
    return value


def _build_failed_response(
    *,
    run_id: str,
    created_at: str,
    completed_at: str,
    payload: Dict[str, Any],
    errors: list[Dict[str, str]],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "failed",
        "timestamps": {"created_at": created_at, "completed_at": completed_at},
        "input_summary": _safe_input_summary(payload),
        "result": None,
        "errors": errors,
        "warnings": [],
    }


def execute_run(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    created_at = _now_iso()
    run_id = f"run_{uuid.uuid4().hex[:12]}"

    schema_errors = validate_request(payload)
    if schema_errors:
        response = _build_failed_response(
            run_id=run_id,
            created_at=created_at,
            completed_at=_now_iso(),
            payload=payload,
            errors=schema_errors,
        )
        return response, 400

    valuation_opts = payload.get("valuation", {}).get("options", {})
    include_breakdown = valuation_opts.get("include_breakdown", True)
    persist_run = valuation_opts.get("persist_run", False)
    rounding_decimals = int(valuation_opts.get("rounding_decimals", 6))

    try:
        raw_result = run_valuation(payload)
        engine_warnings = raw_result.pop("_warnings", [])
        raw_result = _round_numbers(raw_result, rounding_decimals)
        cashflow_count = len(raw_result.get("breakdown", []))

        if not include_breakdown and "breakdown" in raw_result:
            raw_result.pop("breakdown")

        response: Dict[str, Any] = {
            "run_id": run_id,
            "status": "success",
            "timestamps": {"created_at": created_at, "completed_at": _now_iso()},
            "input_summary": _safe_input_summary(payload, cashflow_count=cashflow_count),
            "result": raw_result,
            "errors": [],
            "warnings": list(engine_warnings) if isinstance(engine_warnings, list) else [],
        }

        if persist_run:
            storage_info, persistence_warnings = save_run_artifact(run_id, payload, response)
            response["storage"] = storage_info
            if persistence_warnings:
                response["warnings"].extend(persistence_warnings)
        else:
            response["storage"] = {"persisted": False}

    except Exception as exc:  # pragma: no cover - defensive for PoC
        response = _build_failed_response(
            run_id=run_id,
            created_at=created_at,
            completed_at=_now_iso(),
            payload=payload,
            errors=[
                {
                    "code": "VALUATION_EXECUTION_ERROR",
                    "message": str(exc),
                    "field": "$",
                }
            ],
        )
        return response, 500

    # Defensive check: keep response aligned with T1 schema.
    response_issues = validate_response(response)
    if response_issues:
        fallback = _build_failed_response(
            run_id=run_id,
            created_at=created_at,
            completed_at=_now_iso(),
            payload=payload,
            errors=[
                {
                    "code": "RESPONSE_SCHEMA_ERROR",
                    "message": " | ".join(response_issues),
                    "field": "$",
                }
            ],
        )
        return fallback, 500

    return response, 200


def get_run(run_id: str) -> Tuple[Dict[str, Any], int]:
    payload, persistence_warnings = load_run_response(run_id)
    if payload is None:
        now = _now_iso()
        response = {
            "run_id": run_id,
            "status": "failed",
            "timestamps": {"created_at": now, "completed_at": now},
            "input_summary": {
                "input_mode": "manual",
                "settlement_date": "1970-01-01",
                "price_input_type": "clean_price",
                "fx_interpolation": "linear",
                "fx_rate_side": "ask",
                "cashflow_count": 0,
            },
            "result": None,
            "errors": [
                {
                    "code": "RUN_NOT_FOUND",
                    "message": f"Run '{run_id}' not found in local storage.",
                    "field": "run_id",
                }
            ],
            "warnings": persistence_warnings,
        }
        return response, 404
    if persistence_warnings and isinstance(payload.get("warnings"), list):
        payload["warnings"].extend(persistence_warnings)
    return payload, 200
