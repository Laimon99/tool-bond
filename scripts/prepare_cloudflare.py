"""Build a minimal, generated bundle for the Cloudflare public demo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = REPO_ROOT / ".cloudflare-build"
SOURCE_ROOT = BUILD_ROOT / "src"
PUBLIC_ROOT = BUILD_ROOT / "public"


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"),
    )


def remove_readonly(func, path, _exc_info) -> None:
    """Allow replacement of generated files on Windows/OneDrive workspaces."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def build_web() -> None:
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_BASE_URL"] = "same-origin"
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("npm is required to build the Cloudflare demo.")
    subprocess.run([npm, "run", "build"], cwd=REPO_ROOT / "apps" / "web", env=env, check=True)


def prepare(*, skip_web_build: bool) -> None:
    if not skip_web_build:
        build_web()

    web_output = REPO_ROOT / "apps" / "web" / "out"
    if not web_output.is_dir():
        raise SystemExit("Missing apps/web/out. Run without --skip-web-build first.")

    if BUILD_ROOT.exists():
        resolved_build_root = BUILD_ROOT.resolve()
        if resolved_build_root.parent != REPO_ROOT.resolve():
            raise SystemExit(f"Refusing to replace unexpected path: {resolved_build_root}")
        shutil.rmtree(resolved_build_root, onexc=remove_readonly)
    SOURCE_ROOT.mkdir(parents=True)

    copy_tree(REPO_ROOT / "apps" / "api" / "app", SOURCE_ROOT / "app")
    copy_tree(REPO_ROOT / "services" / "quant-engine" / "quant_engine", SOURCE_ROOT / "quant_engine")
    copy_tree(web_output, PUBLIC_ROOT)
    shutil.copy2(Path(__file__).with_name("worker.py"), SOURCE_ROOT / "worker.py")

    contract_names = (
        "run_valuation.request.schema.json",
        "run_valuation.response.schema.json",
    )
    contracts = {
        name: json.loads((REPO_ROOT / "contracts" / name).read_text(encoding="utf-8"))
        for name in contract_names
    }
    bundled_contracts = (
        '"""Generated from the canonical JSON Schema contracts."""\n\n'
        f"SCHEMAS = {contracts!r}\n"
    )
    (SOURCE_ROOT / "app" / "_bundled_contracts.py").write_text(
        bundled_contracts,
        encoding="utf-8",
        newline="\n",
    )

    file_count = sum(1 for path in BUILD_ROOT.rglob("*") if path.is_file())
    print(f"Prepared {file_count} runtime files in {BUILD_ROOT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-web-build", action="store_true")
    args = parser.parse_args()
    prepare(skip_web_build=args.skip_web_build)
