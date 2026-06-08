"""
Clones a Git repository and detects its tech stack.
Replace the stubs below with real implementations before the demo.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def clone_repo(repo_url: str, scan_id: str) -> str:
    dest = os.path.join(tempfile.gettempdir(), f"vulnsentinel_{scan_id}")
    subprocess.run(
        [
            "git", "clone",
            "--depth", "1",        # shallow — only latest commit
            "--single-branch",     # skip all other branches
            "--no-tags",           # skip tag objects
            "--filter=blob:limit=2m",  # skip individual files > 2 MB
            repo_url, dest,
        ],
        check=True,
        capture_output=True,
        timeout=300,               # 5 minutes — enough for any large repo
    )
    return dest


def detect_tech_stack(repo_path: str) -> dict:
    path = Path(repo_path)
    languages = []
    deps: list[str] = []

    if any(path.rglob("*.py")):
        languages.append("python")
    if any(path.rglob("*.js")) or any(path.rglob("*.ts")):
        languages.append("javascript")
    if any(path.rglob("*.go")):
        languages.append("go")
    if any(path.rglob("*.java")):
        languages.append("java")

    req_file = path / "requirements.txt"
    if req_file.exists():
        deps = [l.strip() for l in req_file.read_text().splitlines() if l.strip()]

    pkg_file = path / "package.json"
    if pkg_file.exists():
        import json
        pkg = json.loads(pkg_file.read_text())
        deps += list(pkg.get("dependencies", {}).keys())

    return {"languages": languages, "dependencies": deps}
