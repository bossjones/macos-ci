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


def chezmoi_init_only_argv(*, source: str, version_manager: str = "mise") -> list[str]:
    """Prerequisite for the pre-apply `chezmoi diff` lint (spec 08(b) step 5), found live
    (OQ-08): `chezmoi diff` has no `--promptString`/config-generation flags of its own -- on a
    fresh clone with no `~/.config/chezmoi/chezmoi.yaml` yet, it refuses to render
    `.chezmoiignore.tmpl` at all (observed: "config file template has changed, run chezmoi init to
    regenerate config file", then a template error on the unset `.version_manager` key). `chezmoi
    init` (no `--apply`) only writes the config and initializes the source dir -- it does not
    touch the destination home directory, so this is safe to run before the lint diff.
    """
    return [
        "chezmoi",
        "init",
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


# --- Two-phase SSH auth (OQ-03/OQ-05: the golden image only configures password auth; the
# spec-mandated `ssh_opts` (BatchMode=yes) can never complete one on its own). Added under the
# lead's OQ-05 resolution -- see .team/macos-ci-build.open-questions.md. Pure argv builders only;
# `harness.py` runs them.

_HARNESS_KEY_PATH = "harness/ssh/id_ed25519_harness"

_BASE_SSH_OPTS: tuple[str, ...] = (
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "UserKnownHostsFile=/dev/null",
    "-o",
    "LogLevel=ERROR",
    "-o",
    "ConnectTimeout=8",
    # OQ-09 (validator red-team of OQ-08): `ConnectTimeout` only bounds the TCP handshake, not a
    # connection that goes dead afterward (host sleep, network drop, a VM that stops responding
    # mid-command). Detects that class of failure within ~45s instead of hanging indefinitely.
    # This does NOT bound a remote command that hangs while the connection stays healthy (e.g.
    # blocked on a read) -- per-command timeouts (a `timeout` wrapper, or subprocess.run's own
    # `timeout=`) are still required for that, and remain the primary backstop.
    "-o",
    "ServerAliveInterval=15",
    "-o",
    "ServerAliveCountMax=3",
)


def bootstrap_ssh_argv(ip: str, *, user: str = "admin", password: str = "admin") -> list[str]:
    """Phase 1, once per clone: the one connection allowed to use password auth.

    Seeds `harness/ssh/id_ed25519_harness.pub` into the guest's `authorized_keys` so every
    subsequent connection can use `steady_state_ssh_argv()`'s BatchMode=yes, key-based transport.
    `BatchMode=no` here is deliberate -- the opposite of steady state -- because this is the one
    command that must be allowed to prompt/accept a password.
    """
    return [
        "sshpass",
        "-p",
        password,
        "ssh",
        "-o",
        "BatchMode=no",
        *_BASE_SSH_OPTS,
        f"{user}@{ip}",
        (
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys "
            "&& chmod 600 ~/.ssh/authorized_keys"
        ),
    ]


# Found live, IMAGE-READY (OQ-08): a non-interactive `ssh host 'cmd'` session has no
# ~/.zshenv on the golden image's `admin` user, so it never sources Homebrew's `brew shellenv`
# (normally a .zprofile/.zshrc concern -- neither is read for a non-login, non-interactive exec).
# PATH is the bare system default (`/usr/bin:/bin:/usr/sbin:/sbin`), and chezmoi/retry/brew all
# live under /opt/homebrew/{bin,sbin} -- so every steady-state command needs this exported first,
# unconditionally, not just when the caller passes `env=`. mise-managed tools (nvim, tmux-via-mise,
# the asdf-managed devops CLI tail) resolve through ~/.local/share/mise/shims/, not a fixed
# Homebrew path, and mise's own shell activation is itself a .zshrc/.zprofile concern -- so that
# shim directory needs the same unconditional export. zsh-dotfiles' own installed scripts
# (post-install-chezmoi, etc.) live under ~/.bin, sheldon itself under ~/.local/bin -- neither
# reachable via .zshenv's cargo/uv sourcing either.
_TOOLCHAIN_PATH_EXPORT = (
    'export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/share/mise/shims:'
    '$HOME/.bin:$HOME/.local/bin:$PATH"; '
)


def steady_state_ssh_argv(
    ip: str,
    command: str,
    *,
    user: str = "admin",
    key_path: str = _HARNESS_KEY_PATH,
    env: dict[str, str] | None = None,
) -> list[str]:
    """Phase 2, everything else: key-based, `BatchMode=yes` -- spec 12's `ssh_opts` verbatim,
    plus `-i <key_path>`. No `-t` -- the absence of a TTY is what makes chezmoi's `stdinIsATTY`
    resolve false (G11); this must never be used with `-t`/`-tt`.
    """
    env_prefix = "".join(f"export {name}={value!r}; " for name, value in (env or {}).items())
    return [
        "ssh",
        *_BASE_SSH_OPTS,
        "-o",
        "BatchMode=yes",
        "-i",
        key_path,
        f"{user}@{ip}",
        _TOOLCHAIN_PATH_EXPORT + env_prefix + command,
    ]
