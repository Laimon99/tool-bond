"""Opt-in local-file persistence adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..config import RUNS_DIR
from .base import PersistenceAdapter


class LocalFilePersistenceAdapter(PersistenceAdapter):
    backend_id = "local_file"

    def _run_file(self, run_id: str) -> Path:
        return RUNS_DIR / f"{run_id}.json"

    def save_run_artifact(
        self,
        run_id: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = self._run_file(run_id)
        artifact = {"request": request_payload, "response": response_payload}
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(artifact, f, ensure_ascii=True, indent=2)

        return {
            "persisted": True,
            "path": str(file_path),
            "backend": self.backend_id,
        }

    def load_run_response(self, run_id: str) -> Dict[str, Any] | None:
        file_path = self._run_file(run_id)
        if not file_path.exists():
            return None
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("response")
