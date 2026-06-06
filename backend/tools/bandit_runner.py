"""Runs Bandit static analysis on a Python repo and returns normalized findings."""

from __future__ import annotations

import json
import subprocess


def run_bandit(repo_path: str) -> list[dict]:
    result = subprocess.run(
        ["bandit", "-r", repo_path, "-f", "json", "-q"],
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
