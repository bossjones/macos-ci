"""Impure shell: sweeps guest log sources over SSH and matches `_triage_core` signatures (owned by 🛠 harness-builder after handoff).

Networking caveat (spec 12 §"Networking caveat"): shells out to `ssh`, deliberately, rather than
opening a socket from Python -- this dodges macOS's "Local Network" errno-65 block.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from macos_ci import artifacts
from macos_ci._harness_core import artifact_paths, steady_state_ssh_argv
from macos_ci._triage_core import Finding, match

app = typer.Typer(help="Triage a Tart VM's log sources for known failure signatures.")

_VM_USER = "admin"
_KEY_PATH = "harness/ssh/id_ed25519_harness"

# spec 12 §"Log sources" -- where a Linux cluster has journalctl, a macOS guest has these.
_LOG_SOURCES: dict[str, str] = {
    "install": "cat /var/log/install.log",
    "brew": "brew config 2>&1",
    "unified": "log show --predicate 'eventMessage contains \"chezmoi\"' --last 30m 2>&1",
}


def _read_latest_state() -> dict[str, Any]:
    latest = artifacts.artifacts_root() / "latest" / "state.json"
    if not latest.exists():
        raise RuntimeError("no artifacts/latest/state.json -- run `up` first")
    data: dict[str, Any] = json.loads(latest.read_text())
    return data


def _ssh_capture(ip: str, command: str, *, run_id: str) -> str:
    import subprocess

    argv = steady_state_ssh_argv(ip, command, user=_VM_USER, key_path=_KEY_PATH)
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    return result.stdout + result.stderr


def sweep_impl(*, vm: str | None = None) -> tuple[list[Finding], dict[str, Any]]:
    """Collect every log source over SSH, feed the combined text to `_triage_core.match()`, write
    `verdict.json`. Exit codes per spec 12 §"Exit codes": 0 healthy, 2 issues found, 3 VM
    unreachable, 4 usage error.
    """
    state = _read_latest_state()
    if vm is not None and state["vm"] != vm:
        raise RuntimeError(f"artifacts/latest tracks {state['vm']!r}, not {vm!r}")
    ip, run_id = state["ip"], state["run_id"]
    paths = artifact_paths(run_id)

    collected: dict[str, str] = {}
    all_lines: list[str] = []
    for label, command in _LOG_SOURCES.items():
        text = _ssh_capture(ip, command, run_id=run_id)
        collected[label] = text
        all_lines.extend(text.splitlines())

    apply_log = Path(paths.apply_log)
    if apply_log.exists():
        apply_text = apply_log.read_text()
        collected["chezmoi"] = apply_text
        all_lines.extend(apply_text.splitlines())

    findings = match(all_lines)

    verdict: dict[str, Any] = {
        "ok": not findings,
        "phase": "vm-debug",
        "cause": findings[0].cause if findings else None,
        "evidence": [{"file": "vm-debug", "line": f.line_number, "text": f.line} for f in findings],
        "next_action": "investigate the named signature" if findings else None,
    }
    artifacts.write_json(run_id, "verdict.json", verdict)
    return findings, verdict


@app.command()
def sweep(
    vm: str | None = typer.Option(None, "--vm"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        findings, verdict = sweep_impl(vm=vm)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=4) from exc

    if json_output:
        typer.echo(json.dumps(verdict, indent=2))
    else:
        if not findings:
            typer.echo("no known failure signatures matched")
        for finding in findings:
            typer.echo(f"[{finding.signature}] line {finding.line_number}: {finding.cause}")

    raise typer.Exit(code=0 if not findings else 2)
