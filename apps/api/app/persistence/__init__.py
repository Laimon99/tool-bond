"""Persistence adapters for run artifacts (file-first, DB-later)."""

from .registry import get_persistence_adapter

__all__ = ["get_persistence_adapter"]
