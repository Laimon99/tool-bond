"""Build the assets-only Cloudflare frontend for the public demo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = REPO_ROOT / ".cloudflare-build"
PUBLIC_ROOT = BUILD_ROOT / "public"
DEFAULT_PUBLIC_API_URL = "https://bondfx-api-laimon99.onrender.com"


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


def build_web(api_base_url: str) -> None:
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_BASE_URL"] = api_base_url
    env["NEXT_PUBLIC_PUBLIC_DEMO"] = "true"
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("npm is required to build the Cloudflare demo.")
    subprocess.run([npm, "run", "build"], cwd=REPO_ROOT / "apps" / "web", env=env, check=True)


def prepare(*, skip_web_build: bool, api_base_url: str) -> None:
    if not skip_web_build:
        build_web(api_base_url)

    web_output = REPO_ROOT / "apps" / "web" / "out"
    if not web_output.is_dir():
        raise SystemExit("Missing apps/web/out. Run without --skip-web-build first.")

    if BUILD_ROOT.exists():
        resolved_build_root = BUILD_ROOT.resolve()
        if resolved_build_root.parent != REPO_ROOT.resolve():
            raise SystemExit(f"Refusing to replace unexpected path: {resolved_build_root}")
        shutil.rmtree(resolved_build_root, onexc=remove_readonly)
    copy_tree(web_output, PUBLIC_ROOT)

    file_count = sum(1 for path in BUILD_ROOT.rglob("*") if path.is_file())
    print(f"Prepared {file_count} static files in {BUILD_ROOT}")
    print(f"Frontend API target: {api_base_url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-web-build", action="store_true")
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("BONDFX_PUBLIC_API_URL", DEFAULT_PUBLIC_API_URL),
    )
    args = parser.parse_args()
    prepare(skip_web_build=args.skip_web_build, api_base_url=args.api_base_url)
