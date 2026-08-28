"""Persistence adapter resolver."""

from __future__ import annotations

from typing import Tuple

from ..config import SETTINGS
from .base import PersistenceAdapter
from .local_file import LocalFilePersistenceAdapter
from .memory import InMemoryPersistenceAdapter


_LOCAL_FILE = LocalFilePersistenceAdapter()
_MEMORY = InMemoryPersistenceAdapter()

_ADAPTERS: dict[str, PersistenceAdapter] = {
    "local_file": _LOCAL_FILE,
    "memory": _MEMORY,
}


def get_persistence_adapter() -> Tuple[PersistenceAdapter, list[str]]:
    backend = SETTINGS.persistence_backend
    adapter = _ADAPTERS.get(backend)
    if adapter is not None:
        return adapter, []

    return _LOCAL_FILE, [f"Unknown persistence backend '{backend}'. Falling back to local_file."]
