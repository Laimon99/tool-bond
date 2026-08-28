"""Standalone API entrypoint for desktop packaged runtime."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("TOOL_BOND_API_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port_raw = os.getenv("TOOL_BOND_API_PORT", "8000").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 8000

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=1,
        log_level=os.getenv("UVICORN_LOG_LEVEL", "warning").strip() or "warning",
    )


if __name__ == "__main__":
    main()
