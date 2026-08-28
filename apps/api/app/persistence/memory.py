"""In-memory persistence adapter for testing/dev fallback."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from .base import PersistenceAdapter


class InMemoryPersistenceAdapter(PersistenceAdapter):
    backend_id = "memory"

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def save_run_artifact(
        self,
        run_id: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._store[run_id] = {
            "request": deepcopy(request_payload),
            "response": deepcopy(response_payload),
        }
        return {
            "persisted": True,
            "path": f"memory://runs/{run_id}",
            "backend": self.backend_id,
        }

    def load_run_response(self, run_id: str) -> Dict[str, Any] | None:
        artifact = self._store.get(run_id)
        if artifact is None:
            return None
        return deepcopy(artifact.get("response"))
