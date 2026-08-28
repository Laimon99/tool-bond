"""Client adapter registry and resolver."""

from __future__ import annotations

from typing import List, Tuple

from .base import ClientAdapter
from .default_client import DefaultClientAdapter
from .finance_poc import FinancePocClientAdapter


DEFAULT_ADAPTER = DefaultClientAdapter()
REGISTERED_ADAPTERS: dict[str, ClientAdapter] = {
    "default": DEFAULT_ADAPTER,
    "finance_poc": FinancePocClientAdapter(),
}


def resolve_client_adapter(client_id: str | None, tenant_id: str | None = None) -> Tuple[ClientAdapter, List[str]]:
    requested = (client_id or tenant_id or "").strip().lower()
    if not requested:
        return DEFAULT_ADAPTER, []

    adapter = REGISTERED_ADAPTERS.get(requested)
    if adapter is not None:
        return adapter, []

    return DEFAULT_ADAPTER, [f"Unknown client '{requested}'. Default adapter applied."]
