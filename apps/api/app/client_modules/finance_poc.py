"""Example client adapter for a finance-specific PoC customization."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .base import ClientAdapter


class FinancePocClientAdapter(ClientAdapter):
    client_id = "finance_poc"

    def preprocess_run_payload(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        patched = deepcopy(payload)
        warnings: List[str] = []
        if not patched.get("tenant_id"):
            patched["tenant_id"] = self.client_id
            warnings.append("tenant_id defaulted to finance_poc by client adapter.")
        return patched, warnings

    def postprocess_run_response(
        self,
        response: Dict[str, Any],
        status_code: int,
        payload: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], int]:
        if status_code < 500 and isinstance(response, dict):
            warnings = response.get("warnings")
            if isinstance(warnings, list):
                warnings.append("finance_poc adapter active.")
        return response, status_code

    def postprocess_import_response(
        self,
        response: Dict[str, Any],
        status_code: int,
    ) -> Tuple[Dict[str, Any], int]:
        if isinstance(response, dict):
            warnings = response.get("warnings")
            if isinstance(warnings, list):
                warnings.append("finance_poc adapter active during import normalization.")
        return response, status_code
