"""Cloudflare Workers entry point for the staged BondFX FastAPI app."""

import os

from workers import WorkerEntrypoint


_APP = None


def get_app():
    """Load packages that need entropy only after a request has started."""
    global _APP
    if _APP is not None:
        return _APP

    os.environ.setdefault("API_SERVICE_NAME", "bondfx-demo")
    os.environ.setdefault("API_SERVICE_VERSION", "0.2.0")
    os.environ.setdefault("APP_ENV", "public-demo")
    os.environ.setdefault("PERSISTENCE_BACKEND", "memory")
    os.environ.setdefault("ALLOW_RUN_PERSISTENCE", "false")
    os.environ.setdefault("MAX_IMPORT_FILES", "3")
    os.environ.setdefault("MAX_IMPORT_FILE_BYTES", "5000000")

    from app.main import app

    @app.middleware("http")
    async def add_public_demo_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    _APP = app
    return _APP


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(get_app(), request.js_object, self.env)
