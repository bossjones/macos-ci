"""Writes structured state to artifacts/<run-id>/*.json (spec 12 §"The artifacts contract")."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def artifacts_root() -> Path:
    return Path.cwd() / "artifacts"


def run_dir(run_id: str) -> Path:
    return artifacts_root() / run_id


def write_json(run_id: str, name: str, data: Any) -> Path:
    path = run_dir(run_id) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    latest = artifacts_root() / "latest"
    latest.unlink(missing_ok=True)
    latest.symlink_to(run_id)

    return path
