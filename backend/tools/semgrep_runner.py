"""Runs Semgrep with the auto ruleset and returns normalized findings."""

from __future__ import annotations

import json
import os
import subprocess
import sys


def _semgrep_bin() -> str:
    venv_bin = os.path.join(os.path.dirname(sys.executable), "semgrep")
    if os.path.isfile(venv_bin):
        return venv_bin
    return "semgrep"


def run_semgrep(repo_path: str) -> list[dict]:
    result = subprocess.run(
        [_semgrep_bin(), "--config", "auto", repo_path, "--json", "--quiet"],
        capture_output=True,
        text=True,
        timeout=180,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    normalized = []
    for finding in data.get("results", []):
        extra = finding.get("extra", {})
        normalized.append({
            "source": "semgrep",
            "file": finding.get("path", ""),
            "line": finding.get("start", {}).get("line", 0),
            "severity": extra.get("severity", "WARNING").upper(),
            "description": extra.get("message", ""),
            "code": extra.get("lines", ""),
            "rule_id": finding.get("check_id", ""),
        })

    return normalized
