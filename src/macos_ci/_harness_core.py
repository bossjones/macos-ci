"""Pure run-id/artifact-path/chezmoi-argv logic for the harness (spec 08 §"The run, composed
from tart primitives"; spec 12 §"The artifacts contract").

Stdlib-only. No clock, subprocess, or filesystem access -- `harness.py` supplies the timestamp,
random suffix, and mount path, and performs the actual `tart`/`ssh`/`chezmoi` I/O.
"""

from __future__ import annotations

from dataclasses import dataclass


def format_run_id(*, timestamp: str, suffix: str) -> str:
    return f"{timestamp}-{suffix}"


def clone_name(run_id: str, *, prefix: str = "dotfiles-test") -> str:
    """spec 08: "each gets its own ephemeral clone name (e.g. `dotfiles-test-<run-id>`)"."""
    return f"{prefix}-{run_id}"


def chezmoi_identity_env(run_id: str) -> dict[str, str]:
    """spec 08 step 6: the two unconditional (non-`$interactive`-gated) identity env vars."""
    return {"CM_computer_name": run_id, "CM_hostname": run_id}


def chezmoi_argv(*, source: str, version_manager: str = "mise") -> list[str]:
    """Verbatim shape from `zsh-dotfiles/scripts/smoke-test-docker.sh:361-365`, minus the
    `retry -t 4 --` wrapper (that belongs to `harness.py`, the impure sibling) and with
    `--source` pointed at the `tart --dir` mount instead of a local checkout.
    """
    return [
        "chezmoi",
        "init",
        "-R",
        "--debug",
        "-v",
        "--apply",
        "--force",
        "--promptString",
        f"version_manager={version_manager}",
        f"--source={source}",
    ]


@dataclass(frozen=True)
class RunArtifactPaths:
    """spec 12 §"The artifacts contract": `artifacts/<run-id>/*`."""

    root: str
    state: str
    doctor: str
    chezmoi_diff: str
    apply_log: str
    pytest_json: str
    manual_json: str
    screenshots_dir: str
    logs_dir: str
    verdict: str


def artifact_paths(run_id: str) -> RunArtifactPaths:
    root = f"artifacts/{run_id}"
    return RunArtifactPaths(
        root=root,
        state=f"{root}/state.json",
        doctor=f"{root}/doctor.json",
        chezmoi_diff=f"{root}/chezmoi-diff.txt",
        apply_log=f"{root}/apply.log",
        pytest_json=f"{root}/pytest.json",
        manual_json=f"{root}/manual.json",
        screenshots_dir=f"{root}/screenshots",
        logs_dir=f"{root}/logs",
        verdict=f"{root}/verdict.json",
    )
