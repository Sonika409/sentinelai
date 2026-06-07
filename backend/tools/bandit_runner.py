"""Runs Bandit static analysis on a Python repo and returns normalized findings."""

from __future__ import annotations

import json
import os
import subprocess
import sys


def _bandit_bin() -> str:
    venv_bin = os.path.join(os.path.dirname(sys.executable), "bandit")
    if os.path.isfile(venv_bin):
        return venv_bin
    return "bandit"


def run_bandit(repo_path: str) -> list[dict]:
    result = subprocess.run(
        [_bandit_bin(), "-r", repo_path, "-f", "json", "-q"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    normalized = []
    for issue in data.get("results", []):
        normalized.append({
            "source": "bandit",
            "file": issue.get("filename", ""),
            "line": issue.get("line_number", 0),
            "severity": issue.get("issue_severity", "LOW").upper(),
            "confidence": issue.get("issue_confidence", "LOW").upper(),
            "description": issue.get("issue_text", ""),
            "code": issue.get("code", ""),
            "test_id": issue.get("test_id", ""),
        })

    return normalized
