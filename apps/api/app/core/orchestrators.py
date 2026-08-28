"""Reusable application orchestration (HTTP-agnostic) for API flows."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..client_modules import resolve_client_adapter
from ..excel_import_service import ExcelImportOptions
from ..valuation_service import execute_run


def _append_warnings(response: Dict[str, Any], warnings: list[str]) -> None:
    if not warnings:
        return
    existing = response.get("warnings")
    if isinstance(existing, list):
        existing.extend(warnings)


def run_valuation_with_client_adapter(
    payload: Dict[str, Any],
    client_id: str | None = None,
) -> Tuple[Dict[str, Any], int]:
    tenant_id_value = payload.get("tenant_id") if isinstance(payload, dict) else None
    tenant_id = tenant_id_value if isinstance(tenant_id_value, str) else None
    adapter, resolve_warnings = resolve_client_adapter(client_id, tenant_id=tenant_id)

    patched_payload, adapter_warnings = adapter.preprocess_run_payload(payload)
    response, status_code = execute_run(patched_payload)
    _append_warnings(response, [*resolve_warnings, *adapter_warnings])
    response, status_code = adapter.postprocess_run_response(response, status_code, patched_payload)
    return response, status_code


def normalize_excel_with_client_adapter(
    file_blobs: List[Tuple[str, bytes]],
    options: ExcelImportOptions,
    client_id: str | None = None,
) -> Tuple[Dict[str, Any], int]:
    adapter, resolve_warnings = resolve_client_adapter(client_id)
    response, status_code = adapter.normalize_excel_import(file_blobs, options)
    _append_warnings(response, resolve_warnings)
    response, status_code = adapter.postprocess_import_response(response, status_code)
    return response, status_code
