"""Runtime configuration and project paths for API service."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys


APP_DIR = Path(__file__).resolve().parent


def _detect_project_root() -> Path:
    env_root = os.getenv("TOOL_BOND_PROJECT_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            return Path(meipass).resolve()

    # Cloudflare's deployment build stages the app and its data files under
    # one read-only source directory. Keep the regular monorepo layout as the
    # default while allowing the same application code to run at the edge.
    bundled_root = APP_DIR.parent
    if (bundled_root / "contracts").exists() and (bundled_root / "quant_engine").exists():
        return bundled_root

    return APP_DIR.parents[2]


def _detect_storage_dir(project_root: Path) -> Path:
    env_storage = os.getenv("TOOL_BOND_STORAGE_DIR", "").strip()
    if env_storage:
        return Path(env_storage).resolve()

    if getattr(sys, "frozen", False):
        local_app_data = Path(os.getenv("LOCALAPPDATA", str(Path.home())))
        return local_app_data / "ToolBond" / "storage" / "local"

    return project_root / "storage" / "local"


PROJECT_ROOT = _detect_project_root()
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
STORAGE_DIR = _detect_storage_dir(PROJECT_ROOT)
RUNS_DIR = STORAGE_DIR / "runs"
QUANT_ENGINE_SRC = (
    PROJECT_ROOT
    if (PROJECT_ROOT / "quant_engine").exists()
    else PROJECT_ROOT / "services" / "quant-engine"
)

# PoC path bootstrap: allow importing local quant_engine package without installation.
if QUANT_ENGINE_SRC.exists() and str(QUANT_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(QUANT_ENGINE_SRC))


def _env_int(name: str, default: int, *, min_value: int = 1, max_value: int | None = None) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    if value < min_value:
        value = min_value
    if max_value is not None and value > max_value:
        value = max_value
    return value


def _env_csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name, default).strip()
    values = tuple(v.strip() for v in raw.split(",") if v.strip())
    return values or ("*",)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ApiSettings:
    service_name: str
    service_version: str
    app_env: str
    cors_allow_origins: tuple[str, ...]
    max_import_files: int
    max_import_file_bytes: int
    persistence_backend: str
    allow_run_persistence: bool


def load_settings() -> ApiSettings:
    return ApiSettings(
        service_name=os.getenv("API_SERVICE_NAME", "tool-bond-api").strip() or "tool-bond-api",
        service_version=os.getenv("API_SERVICE_VERSION", "0.2.0").strip() or "0.2.0",
        app_env=os.getenv("APP_ENV", "dev").strip() or "dev",
        cors_allow_origins=_env_csv("CORS_ALLOW_ORIGINS", "*"),
        max_import_files=_env_int("MAX_IMPORT_FILES", 10, min_value=1, max_value=100),
        max_import_file_bytes=_env_int(
            "MAX_IMPORT_FILE_BYTES",
            10_000_000,
            min_value=1_000,
            max_value=200_000_000,
        ),
        persistence_backend=os.getenv("PERSISTENCE_BACKEND", "memory").strip().lower() or "memory",
        allow_run_persistence=_env_bool("ALLOW_RUN_PERSISTENCE", True),
    )


SETTINGS = load_settings()
