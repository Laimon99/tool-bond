"""Run storage facade using pluggable persistence adapters."""

from __future__ import annotations

from typing import Any, Dict

from .persistence import get_persistence_adapter


def save_run_artifact(
    run_id: str,
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
) -> tuple[Dict[str, Any], list[str]]:
    adapter, warnings = get_persistence_adapter()
    storage_info = adapter.save_run_artifact(run_id, request_payload, response_payload)
    return storage_info, warnings


def load_run_response(run_id: str) -> tuple[Dict[str, Any] | None, list[str]]:
    adapter, warnings = get_persistence_adapter()
    payload = adapter.load_run_response(run_id)
    return payload, warnings
