"""Base client adapter hooks for reusable core/custom separation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from ..excel_import_service import ExcelImportOptions, normalize_excel_files


class ClientAdapter:
    """Default no-op adapter. Custom clients override only needed hooks."""

    client_id = "default"

    def normalize_excel_import(
        self,
        file_blobs: List[Tuple[str, bytes]],
        options: ExcelImportOptions,
    ) -> Tuple[Dict[str, Any], int]:
        return normalize_excel_files(file_blobs, options)

    def preprocess_run_payload(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        return deepcopy(payload), []

    def postprocess_run_response(
        self,
        response: Dict[str, Any],
        status_code: int,
        payload: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], int]:
        return response, status_code

    def postprocess_import_response(
        self,
        response: Dict[str, Any],
        status_code: int,
    ) -> Tuple[Dict[str, Any], int]:
        return response, status_code
