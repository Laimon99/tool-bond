"""JSON schema validation helpers."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator, FormatChecker

from .config import CONTRACTS_DIR


def _load_schema(path: Path) -> Dict[str, Any]:
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Wrangler packages Python modules but not arbitrary JSON files. The
    # Cloudflare staging script generates this module from the canonical
    # contracts; normal local and container builds continue to use the files.
    try:
        from ._bundled_contracts import SCHEMAS
    except ImportError as exc:  # pragma: no cover - deployment-only fallback
        raise FileNotFoundError(f"Schema not found: {path}") from exc

    return SCHEMAS[path.name]


REQUEST_SCHEMA = _load_schema(CONTRACTS_DIR / "run_valuation.request.schema.json")
RESPONSE_SCHEMA = _load_schema(CONTRACTS_DIR / "run_valuation.response.schema.json")

FORMAT_CHECKER = FormatChecker()
REQUEST_VALIDATOR = Draft202012Validator(REQUEST_SCHEMA, format_checker=FORMAT_CHECKER)
RESPONSE_VALIDATOR = Draft202012Validator(RESPONSE_SCHEMA, format_checker=FORMAT_CHECKER)


def validate_request(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    for err in sorted(REQUEST_VALIDATOR.iter_errors(payload), key=lambda e: list(e.path)):
        field_path = ".".join(str(p) for p in err.absolute_path) or "$"
        errors.append(
            {
                "code": "REQUEST_SCHEMA_ERROR",
                "message": err.message,
                "field": field_path,
            }
        )
    if errors:
        return errors

    valuation = payload["valuation"]
    bond = valuation["bond"]

    def add(message: str, field: str) -> None:
        errors.append(
            {
                "code": "REQUEST_SEMANTIC_ERROR",
                "message": message,
                "field": field,
            }
        )

    issue_date = date.fromisoformat(bond["issue_date"])
    maturity_date = date.fromisoformat(bond["maturity_date"])
    settlement_date = date.fromisoformat(valuation["settlement_date"])
    schedule_dates = [date.fromisoformat(value) for value in bond["schedule_dates"]]

    if issue_date >= maturity_date:
        add("issue_date must be before maturity_date.", "valuation.bond.maturity_date")
    if not issue_date <= settlement_date < maturity_date:
        add(
            "settlement_date must be on or after issue_date and before maturity_date.",
            "valuation.settlement_date",
        )
    if maturity_date not in schedule_dates:
        add("schedule_dates must include maturity_date.", "valuation.bond.schedule_dates")
    if any(value <= issue_date or value > maturity_date for value in schedule_dates):
        add(
            "Every schedule date must be after issue_date and on or before maturity_date.",
            "valuation.bond.schedule_dates",
        )

    df_dates = [row["date"] for row in valuation["usd_discount_curve"]["df_points"]]
    if len(df_dates) != len(set(df_dates)):
        add("Discount-factor dates must be unique.", "valuation.usd_discount_curve.df_points")

    fx_pillars = valuation["fx_forward_curve"]["pillars"]
    fx_dates = [row["end_date"] for row in fx_pillars]
    if len(fx_dates) != len(set(fx_dates)):
        add("FX-forward pillar dates must be unique.", "valuation.fx_forward_curve.pillars")
    if any(float(row["bid"]) > float(row["ask"]) for row in fx_pillars):
        add("Every FX-forward bid must be less than or equal to ask.", "valuation.fx_forward_curve.pillars")

    return errors


def validate_response(payload: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    for err in sorted(RESPONSE_VALIDATOR.iter_errors(payload), key=lambda e: list(e.path)):
        field_path = ".".join(str(p) for p in err.absolute_path) or "$"
        problems.append(f"{field_path}: {err.message}")
    return problems
