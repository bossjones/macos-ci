"""I/O shell: gathers host facts and evaluates them against `_doctor_core.check()`.

`just doctor --json` writes `artifacts/<run-id>/doctor.json` and exits 2 on any miss.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path

from macos_ci._doctor_core import REQUIRED_TOOLS, DoctorFacts, check, overall_ok
from macos_ci.artifacts import write_json

_VERSION_RE = re.compile(r"\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?")

# OQ-08: sshpass has no `--version` flag (`sshpass --version` errors "illegal option"); only
# `-V` reports the version. Per-tool override, default `--version` for everything else.
_VERSION_FLAG_OVERRIDES: dict[str, str] = {"sshpass": "-V"}


def _tool_version(tool: str) -> str | None:
    path = shutil.which(tool)
    if path is None:
        return None
    flag = _VERSION_FLAG_OVERRIDES.get(tool, "--version")
    try:
        result = subprocess.run([tool, flag], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = _VERSION_RE.search(result.stdout + result.stderr)
    return match.group() if match else None


def _login_keychain_unlocked() -> bool:
    """Best-effort, non-interactive probe (spec 01 §G8 documents no direct `security` query).

    A generic-password search against a name that (almost certainly) doesn't exist reaches the
    keychain either way: locked -> "interaction is not allowed" (errSecInteractionNotAllowed,
    -25308) without prompting; unlocked -> "could not be found in the keychain" (errSecItemNotFound,
    -25300), since the search itself succeeded.
    """
    try:
        probe = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                "macos-ci-doctor-probe",
                "-s",
                "macos-ci-doctor-probe",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    stderr = probe.stderr.lower()
    if "could not be found" in stderr:
        return True
    if "interaction is not allowed" in stderr or "-25308" in stderr:
        return False
    return probe.returncode == 0


def collect_facts() -> DoctorFacts:
    zsh_dotfiles = os.environ.get("ZSH_DOTFILES", str(Path.cwd().parent / "zsh-dotfiles"))
    free_bytes = shutil.disk_usage("/").free
    return DoctorFacts(
        tool_versions={tool: _tool_version(tool) for tool in REQUIRED_TOOLS},
        arch=platform.machine(),
        macos_version=platform.mac_ver()[0] or "0.0",
        login_keychain_unlocked=_login_keychain_unlocked(),
        zsh_dotfiles_path=zsh_dotfiles,
        zsh_dotfiles_path_exists=Path(zsh_dotfiles).exists(),
        free_disk_space_gb=free_bytes / 1e9,
    )


def run(*, json_output: bool = False, run_id: str | None = None) -> int:
    facts = collect_facts()
    results = check(facts)
    ok = overall_ok(results)

    rows = [{"tool": r.tool, "required": r.required, "found": r.found, "ok": r.ok} for r in results]

    rid = run_id or time.strftime("%Y%m%d-%H%M%S")
    write_json(rid, "doctor.json", rows)

    if json_output:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            mark = "OK" if row["ok"] else "MISSING"
            print(
                f"[{mark:>7}] {row['tool']:<24} required={row['required']:<12} found={row['found']}"
            )

    return 0 if ok else 2
