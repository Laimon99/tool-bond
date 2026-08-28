"""Persistence adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class PersistenceAdapter(ABC):
    backend_id = "base"

    @abstractmethod
    def save_run_artifact(
        self,
        run_id: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def load_run_response(self, run_id: str) -> Dict[str, Any] | None:
        raise NotImplementedError
