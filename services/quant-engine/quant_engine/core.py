def ping() -> dict:
    """Simple health-style method for early integration tests."""
    return {
        "service": "quant-engine",
        "status": "ok",
        "message": "quant skeleton ready"
    }
