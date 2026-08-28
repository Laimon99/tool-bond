from typing import Any, Dict

from fastapi import FastAPI
from fastapi import File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import SETTINGS
from .core.orchestrators import normalize_excel_with_client_adapter, run_valuation_with_client_adapter
from .excel_import_service import ExcelImportOptions
from .valuation_service import get_run

app = FastAPI(
    title="BondFX API",
    version=SETTINGS.service_version,
    description="Educational API for transparent TRY bond valuation in USD.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(SETTINGS.cors_allow_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_public_api_headers(request, call_next):
    """Apply conservative defaults suitable for the public demo API."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/")
async def root() -> dict:
    return {
        "service": SETTINGS.service_name,
        "version": SETTINGS.service_version,
        "env": SETTINGS.app_env,
        "status": "ok",
        "message": "BondFX valuation API is ready.",
    }


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": SETTINGS.service_name,
        "version": SETTINGS.service_version,
        "env": SETTINGS.app_env,
    }


@app.get("/meta")
async def meta() -> dict:
    return {
        "service": SETTINGS.service_name,
        "version": SETTINGS.service_version,
        "env": SETTINGS.app_env,
        "limits": {
            "max_import_files": SETTINGS.max_import_files,
            "max_import_file_bytes": SETTINGS.max_import_file_bytes,
        },
        "features": {
            "db_required": False,
            "persistence_mode_default": SETTINGS.persistence_backend,
            "run_persistence_enabled": SETTINGS.allow_run_persistence,
        },
    }


@app.post("/run-valuation")
async def run_valuation_endpoint(payload: Dict[str, Any], client_id: str | None = None) -> JSONResponse:
    response, status_code = run_valuation_with_client_adapter(payload, client_id=client_id)
    return JSONResponse(content=response, status_code=status_code)


@app.get("/runs/{run_id}")
async def get_run_endpoint(run_id: str) -> JSONResponse:
    response, status_code = get_run(run_id)
    return JSONResponse(content=response, status_code=status_code)


@app.post("/import/excel")
async def import_excel_endpoint(
    files: list[UploadFile] = File(...),
    request_id: str | None = Form(default=None),
    client_id: str | None = Form(default=None),
    usd_budget: float = Form(default=100000.0),
    spot_usdtry_override: float | None = Form(default=None),
    include_breakdown: bool = Form(default=True),
    persist_run: bool = Form(default=False),
    rounding_decimals: int = Form(default=6),
    usd_flat_rate: float = Form(default=0.05),
) -> JSONResponse:
    if len(files) > SETTINGS.max_import_files:
        return JSONResponse(
            content={
                "status": "failed",
                "normalized_request": None,
                "warnings": [],
                "errors": [
                    {
                        "code": "TOO_MANY_FILES",
                        "message": f"Too many files: {len(files)} > {SETTINGS.max_import_files}.",
                        "field": "files",
                    }
                ],
            },
            status_code=400,
        )

    # openpyxl supports modern OOXML workbooks. Legacy binary .xls files are
    # intentionally rejected instead of being advertised and failing later.
    allowed_extensions = (".xlsx", ".xlsm")
    file_blobs: list[tuple[str, bytes]] = []
    for f in files:
        file_name = f.filename or "uploaded.xlsx"
        if not file_name.lower().endswith(allowed_extensions):
            return JSONResponse(
                content={
                    "status": "failed",
                    "normalized_request": None,
                    "warnings": [],
                    "errors": [
                        {
                            "code": "UNSUPPORTED_FILE_TYPE",
                            "message": f"Unsupported file type for '{file_name}'. Expected .xlsx or .xlsm.",
                            "field": file_name,
                        }
                    ],
                },
                status_code=400,
            )
        content = await f.read()
        if len(content) > SETTINGS.max_import_file_bytes:
            return JSONResponse(
                content={
                    "status": "failed",
                    "normalized_request": None,
                    "warnings": [],
                    "errors": [
                        {
                            "code": "FILE_TOO_LARGE",
                            "message": (
                                f"File '{file_name}' exceeds max size "
                                f"({len(content)} bytes > {SETTINGS.max_import_file_bytes} bytes)."
                            ),
                            "field": file_name,
                        }
                    ],
                },
                status_code=413,
            )
        file_blobs.append((file_name, content))

    options = ExcelImportOptions(
        request_id=request_id,
        usd_budget=usd_budget,
        spot_usdtry_override=spot_usdtry_override,
        include_breakdown=include_breakdown,
        persist_run=persist_run,
        rounding_decimals=rounding_decimals,
        usd_flat_rate=usd_flat_rate,
    )
    response, status_code = normalize_excel_with_client_adapter(file_blobs, options, client_id=client_id)
    return JSONResponse(content=response, status_code=status_code)
