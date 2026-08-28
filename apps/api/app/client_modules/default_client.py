"""Default adapter used when no specific client customization is requested."""

from __future__ import annotations

from .base import ClientAdapter


class DefaultClientAdapter(ClientAdapter):
    client_id = "default"
