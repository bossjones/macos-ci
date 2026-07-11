"""Impure shell: `tart clone` -> headless `tart run` -> SSH apply -> `tart delete` (owned by 🛠 harness-builder after handoff).

SSH transport is two-phase (OQ-03/OQ-05, `.team/macos-ci-build.open-questions.md`): the golden image
only configures password auth, so a fresh clone can't yet accept the spec-mandated `BatchMode=yes`
key-based connection. `_bootstrap_key_trust()` makes one password-authenticated connection (via
`sshpass`, `_harness_core.bootstrap_ssh_argv`) to seed `harness/ssh/id_ed25519_harness.pub` into the
guest, then every subsequent command uses `_harness_core.steady_state_ssh_argv` (key-based,
`BatchMode=yes`, no `-t` -- G11).
"""

from __future__ import annotations

import json
import shlex
import subprocess
import time
import tomllib
from pathlib import Path
from typing import Any

import typer

from macos_ci import artifacts, tart
from macos_ci._config_core import load as load_config
from macos_ci._harness_core import (
    artifact_paths,
    bootstrap_ssh_argv,
    chezmoi_argv,
    chezmoi_identity_env,
    chezmoi_init_only_argv,
    clone_name,
    format_run_id,
    steady_state_ssh_argv,
)
from macos_ci._tart_core import DirMount

app: typer.Typer = typer.Typer(help="Run the dotfiles-test harness against a Tart VM.")

_VM_USER = "admin"
_KEY_PATH = Path("harness/ssh/id_ed25519_harness")
_IP_WAIT_SECS = 120.0
_SSH_WAIT_SECS = 60.0
_DOTFILES_MOUNT_TAG = "dotfiles"
_MOUNT_POINT = f"/Volumes/My Shared Files/{_DOTFILES_MOUNT_TAG}"


class HarnessError(RuntimeError):
    """A harness phase failed. `str(exc)` is the phase name; `exc.__cause__`/`.detail` is why."""

    phase: str
    detail: str

    def __init__(self, phase: str, detail: str) -> None:
        super().__init__(phase)
        self.phase = phase
        self.detail = detail


def _ensure_key_permissions() -> None:
    """git does not preserve the 0600 bit; OpenSSH refuses a more-permissive private key outright."""
    if _KEY_PATH.exists():
        _KEY_PATH.chmod(0o600)


def _resolve_golden_clone_source(image: str) -> str:
    """The name to `tart clone` FROM for a fresh test-run VM.

    NOT the OCI ref in `macos-versions.toml` -- that ref names the *vanilla base* packer builds
    the golden image FROM (spec 08(a)); `image.<name>.ref` is a build-time input, not a run-time
    clone source. The actual golden image is a local, already-provisioned tart VM.
    `packer/tart-golden-image.pkr.hcl` hardcodes its `vm_name` to `"dotfiles-golden"` regardless of
    which macos-versions.toml image built it (today, only `default` -- "sequoia" -- has been
    built). This function still reads macos-versions.toml, but only to validate `image` is a real,
    declared name (via `_config_core.load()`) -- discovered live, corrected from an earlier
    version that resolved straight to the OCI ref, which would have cloned an unprovisioned
    vanilla VM with no chezmoi/Homebrew/Xcode CLT (see OQ-07).

    TEMPORARY: `config.py` (the intended I/O owner of the file read, per the ownership table) has
    not landed yet. Minimal file read + `_config_core.load()` validation so `up`/`run` work today;
    refactor to delegate to `config.py` once it exists.
    """
    raw = tomllib.loads(Path("macos-versions.toml").read_text())
    config = load_config(raw)
    if image not in config.images:
        raise HarnessError(
            "resolve-image", f"image {image!r} is not declared in macos-versions.toml"
        )

    if image == config.default:
        return "dotfiles-golden"
    # Forward-looking convention for a future per-image golden template; nothing builds this yet.
    return f"dotfiles-golden-{image}"


def _wait_for_ip(name: str, *, timeout: float = _IP_WAIT_SECS) -> str:
    deadline = time.monotonic() + timeout
    while True:
        try:
            ip = tart.ip(name)
        except subprocess.CalledProcessError:
            ip = ""
        if ip:
            return ip
        if time.monotonic() >= deadline:
            raise HarnessError("wait-for-ip", f"tart ip {name} did not resolve within {timeout}s")
        time.sleep(2)


def _bootstrap_key_trust(ip: str) -> None:
    _ensure_key_permissions()
    pubkey_path = Path(f"{_KEY_PATH}.pub")
    argv = bootstrap_ssh_argv(ip, user=_VM_USER)
    result = subprocess.run(
        argv, input=pubkey_path.read_text(), capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise HarnessError("bootstrap-key-trust", result.stderr.strip() or result.stdout.strip())


def _wait_for_ssh(ip: str, *, timeout: float = _SSH_WAIT_SECS) -> None:
    deadline = time.monotonic() + timeout
    while True:
        argv = steady_state_ssh_argv(ip, "true", user=_VM_USER, key_path=str(_KEY_PATH))
        result = subprocess.run(argv, capture_output=True, text=True)
        if result.returncode == 0:
            return
        if time.monotonic() >= deadline:
            raise HarnessError(
                "wait-for-ssh",
                f"key-based SSH to {ip} not reachable within {timeout}s: {result.stderr.strip()}",
            )
        time.sleep(2)


_TOOLCHAIN_PATH_LINE = (
    'export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/share/mise/shims:'
    '$HOME/.bin:$HOME/.local/bin:$PATH"'
)


def _bootstrap_shell_env(ip: str) -> None:
    """Ensure Homebrew, mise-managed, and zsh-dotfiles-installed tools are on PATH for every
    subsequent non-interactive SSH session -- testinfra (`tests/integration/`) and pexpect
    (`tests/pty/`) both open their own SSH connections independent of `_ssh()`'s per-command
    export, so they need this fixed at the source. `.zshenv` -- not `.zprofile`/`.zshrc` -- is
    read for every zsh invocation, interactive or not.

    Found live (OQ-08): the golden image's `admin` user has no `.zshenv` at all before this; the
    dotfiles apply itself creates one, but only to source cargo/uv's own env files, never
    Homebrew's, mise's shim directory (mise-managed tools like `nvim` resolve only through
    `~/.local/share/mise/shims/`), or `~/.bin`/`~/.local/bin` (where the dotfiles install their own
    scripts -- `post-install-chezmoi` -- and sheldon itself). `mise activate`'s own PATH wiring is
    itself a `.zshrc`/`.zprofile` concern that a non-interactive session never reaches. Idempotent
    (checks before appending) and safe to call every `up` -- every clone is fresh, so there is
    nothing to accumulate across runs, but a retried `up` on the same clone must not double the
    line.
    """
    command = (
        f"grep -qxF {_shell_quote(_TOOLCHAIN_PATH_LINE)} ~/.zshenv 2>/dev/null "
        f"|| echo {_shell_quote(_TOOLCHAIN_PATH_LINE)} >> ~/.zshenv"
    )
    argv = steady_state_ssh_argv(ip, command, user=_VM_USER, key_path=str(_KEY_PATH))
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise HarnessError("bootstrap-shell-env", result.stderr.strip())


def _bootstrap_chezmoi_source_symlink(ip: str, *, source: str) -> None:
    """Found live (OQ-08): `zsh-dotfiles/home/.sheldon/plugins.toml`'s `[plugins.bossaliases]`
    entry hardcodes `local = "~/.local/share/chezmoi/home/shell/customs"` -- chezmoi's
    *conventional default* source directory -- rather than templating on
    `{{ .chezmoi.sourceDir }}`. Passing `--source=<tart --dir mount>` (spec 08(b), deliberately, to
    avoid a git clone inside the guest) never populates that default path, so `sheldon lock` fails
    with "matches 0 directories" even on a fully successful apply. Symlinking the conventional
    path at the mount preserves spec 08(b)'s "no copy, identical tree" intent while satisfying the
    hardcoded reference. `ln -sfn` is idempotent -- safe to call every `up`.

    Found live (`just matrix`, a genuinely fresh clone that had never run any prior bootstrap
    step): `ln -sfn` fails outright when its parent directory doesn't exist yet -- a brand-new
    clone has no `~/.local/share/` at all until something creates it (chezmoi itself would, on a
    normal un-hijacked run; mise's installer also does, later). My earlier manual verification of
    this symlink (OQ-08) ran against `dotfiles-test`, which had already been through one `chezmoi
    init --apply` and so already had `~/.local/share/` -- masking this on the very first `up` of a
    fresh clone. `mkdir -p` the parent first.
    """
    command = f"mkdir -p ~/.local/share && ln -sfn {_shell_quote(source)} ~/.local/share/chezmoi"
    argv = steady_state_ssh_argv(ip, command, user=_VM_USER, key_path=str(_KEY_PATH))
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise HarnessError("bootstrap-chezmoi-source-symlink", result.stderr.strip())


def _ssh(
    ip: str, command: str, *, run_id: str, timeout: float = 600.0
) -> subprocess.CompletedProcess[str]:
    argv = steady_state_ssh_argv(
        ip,
        command,
        user=_VM_USER,
        key_path=str(_KEY_PATH),
        env=chezmoi_identity_env(run_id),
    )
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def _dotfiles_path(dotfiles: str | None) -> Path:
    return Path(dotfiles or (Path.cwd().parent / "zsh-dotfiles")).resolve()


def _read_latest_state() -> dict[str, Any]:
    latest = artifacts.artifacts_root() / "latest" / "state.json"
    if not latest.exists():
        raise HarnessError("read-state", "no artifacts/latest/state.json -- run `up` first")
    data: dict[str, Any] = json.loads(latest.read_text())
    return data


def up_impl(
    *, vm: str | None = None, image: str = "sequoia", dotfiles: str | None = None
) -> dict[str, Any]:
    """`tart clone` -> headless `tart run` -> poll `tart ip` -> bootstrap key trust -> wait for
    key-based SSH. Never mutates the golden image -- every run clones fresh (spec 08(a))."""
    run_id = format_run_id(
        timestamp=time.strftime("%Y%m%d-%H%M%S"), suffix=f"{time.monotonic_ns() % 1_000_000:06d}"
    )
    name = vm or clone_name(run_id)
    source = _resolve_golden_clone_source(image)

    tart.clone(source, name)
    mounts = [
        DirMount(name=_DOTFILES_MOUNT_TAG, path=str(_dotfiles_path(dotfiles)), read_only=True)
    ]
    tart.run(name, headless=True, dirs=mounts)

    ip = _wait_for_ip(name)
    _bootstrap_key_trust(ip)
    _wait_for_ssh(ip)
    _bootstrap_shell_env(ip)
    _bootstrap_chezmoi_source_symlink(ip, source=_MOUNT_POINT)

    state = {
        "vm": name,
        "ip": ip,
        "image": image,
        "run_id": run_id,
        "mount_point": _MOUNT_POINT,
        "phase": "up",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    artifacts.write_json(run_id, "state.json", state)
    return state


def down_impl(*, vm: str) -> None:
    """Stop the VM, leave the clone on disk. `tart.py`/`_tart_core.py` (🐍's files) don't yet
    expose `tart stop` -- calling it directly here rather than duplicating a pure argv builder in
    another role's owned module for a single trivial verb.
    """
    subprocess.run(["tart", "stop", vm], check=True)


def destroy_impl(*, vm: str) -> None:
    """`tart delete` refuses to delete a running VM (found live, Steps 7-10: `tart delete` on a
    running clone fails with "the specified VM ... does not exist" -- a misleading message for
    "it's running"). Stop first, tolerating "already stopped" (`tart stop` exits 2 with "VM ...
    is not running" in that case -- not a real failure), then delete.
    """
    subprocess.run(["tart", "stop", vm], capture_output=True)
    tart.delete(vm)


def apply_impl(*, vm: str, version_manager: str = "mise") -> dict[str, Any]:
    """Only the chezmoi apply, against an already-live VM (fast iteration -- assumes `up` already
    ran and `artifacts/latest/state.json` names this VM's IP and run-id).
    """
    state = _read_latest_state()
    if state["vm"] != vm:
        raise HarnessError(
            "apply", f"artifacts/latest tracks {state['vm']!r}, not {vm!r} -- run `up` for this VM"
        )
    ip, run_id = state["ip"], state["run_id"]
    paths = artifact_paths(run_id)

    # OQ-08: `chezmoi diff` cannot render templates until a config exists (no --promptString of
    # its own), so seed one first. `chezmoi init` without `--apply` never touches the destination.
    init_argv = chezmoi_init_only_argv(source=_MOUNT_POINT, version_manager=version_manager)
    init_command = " ".join(_shell_quote(part) for part in init_argv)
    init_result = _ssh(ip, init_command, run_id=run_id)
    if init_result.returncode != 0:
        raise HarnessError("chezmoi-init", init_result.stderr.strip())

    diff = _ssh(ip, _diff_command(_MOUNT_POINT), run_id=run_id)
    Path(paths.chezmoi_diff).parent.mkdir(parents=True, exist_ok=True)
    Path(paths.chezmoi_diff).write_text(diff.stdout + diff.stderr)
    if diff.stderr.strip():
        raise HarnessError("chezmoi-diff", diff.stderr.strip())

    argv = chezmoi_argv(source=_MOUNT_POINT, version_manager=version_manager)
    command = "retry -t 4 -- " + " ".join(_shell_quote(part) for part in argv)
    apply_result = _ssh(ip, command, run_id=run_id, timeout=1800.0)
    Path(paths.apply_log).write_text(apply_result.stdout + apply_result.stderr)
    if apply_result.returncode != 0:
        raise HarnessError("chezmoi-apply", apply_result.stderr.strip())

    return {"vm": vm, "run_id": run_id, "phase": "apply", "ok": True}


def _shell_quote(part: str) -> str:
    return shlex.quote(part)


def _diff_command(source: str) -> str:
    # `source` (the `tart --dir` mount point) contains spaces ("/Volumes/My Shared Files/...") --
    # found live (OQ-08): an earlier unquoted f-string here made chezmoi stat the shell-split
    # "/Volumes/My" and fail immediately, before any real diff ran.
    return f"chezmoi diff --source={_shell_quote(source)}"


def run_impl(
    *, vm: str | None, image: str, version_manager: str, dotfiles: str | None = None
) -> dict[str, Any]:
    """The main loop: `up` -> `chezmoi diff` -> apply -> destroy. Always writes verdict.json, even
    on crash (spec 12 §"The artifacts contract").
    """
    run_id = None
    phase = "up"
    try:
        state = up_impl(vm=vm, image=image, dotfiles=dotfiles)
        run_id = state["run_id"]
        phase = "apply"
        apply_impl(vm=state["vm"], version_manager=version_manager)
        verdict = {"ok": True, "phase": "done", "cause": None, "evidence": [], "next_action": None}
        return verdict
    except HarnessError as exc:
        verdict = {
            "ok": False,
            "phase": exc.phase,
            "cause": exc.detail,
            "evidence": [],
            "next_action": "run `just debug` to triage",
        }
        raise
    finally:
        if run_id is not None:
            artifacts.write_json(
                run_id, "verdict.json", locals().get("verdict", {"ok": False, "phase": phase})
            )
        if vm is not None:
            try:
                destroy_impl(vm=vm)
            except subprocess.CalledProcessError:
                pass


def prune_impl() -> list[str]:
    """Delete orphan clones not tracked under artifacts/. Cross-references every `tart list` VM
    against every `artifacts/*/state.json`'s `vm` field; anything untracked is orphaned.
    """

    tracked: set[str] = set()
    for state_file in artifacts.artifacts_root().glob("*/state.json"):
        try:
            tracked.add(json.loads(state_file.read_text())["vm"])
        except (OSError, KeyError, ValueError):
            continue

    result = subprocess.run(["tart", "list", "--format", "json"], capture_output=True, text=True)
    all_vms = [entry["Name"] for entry in json.loads(result.stdout or "[]")]
    orphans = [
        name for name in all_vms if name.startswith("dotfiles-test-") and name not in tracked
    ]
    for name in orphans:
        tart.delete(name)
    return orphans


def matrix_impl(
    *, images: list[str] | None = None, version_managers: list[str] | None = None
) -> dict[str, Any]:
    """Cross-product of image x version_manager (spec 12 Testing table). Each leg gets its own VM
    name (`dotfiles-matrix-<image>-<version_manager>`) so legs never collide, and one leg's failure
    never aborts the others -- an `asdf` leg failing without `--with-prereq-installer` is expected
    (spec 09 §"What zsh-dotfiles cannot bootstrap on macOS": there is no macOS asdf *installer*,
    only an optional plugin script that exits 0 when the binary is absent), not a matrix bug.
    """
    raw = tomllib.loads(Path("macos-versions.toml").read_text())
    config = load_config(raw)
    images = images or [config.default]
    version_managers = version_managers or ["mise", "asdf"]

    results: dict[str, Any] = {}
    for image in images:
        for version_manager in version_managers:
            leg = f"{image}-{version_manager}"
            vm_name = f"dotfiles-matrix-{leg}"
            try:
                verdict = run_impl(vm=vm_name, image=image, version_manager=version_manager)
            except HarnessError as exc:
                verdict = {"ok": False, "phase": exc.phase, "cause": exc.detail}
            results[leg] = verdict
    return results


def logs_impl(*, vm: str) -> Path:
    """Sweep guest logs into artifacts/<run-id>/logs/ (spec 12 §"Log sources")."""
    state = _read_latest_state()
    if state["vm"] != vm:
        raise HarnessError("logs", f"artifacts/latest tracks {state['vm']!r}, not {vm!r}")
    ip, run_id = state["ip"], state["run_id"]
    paths = artifact_paths(run_id)
    logs_dir = Path(paths.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    sources = {
        "install": "cat /var/log/install.log",
        "brew": "brew config 2>&1",
        "unified": "log show --predicate 'eventMessage contains \"chezmoi\"' --last 30m 2>&1",
    }
    for label, command in sources.items():
        result = _ssh(ip, command, run_id=run_id)
        (logs_dir / f"{label}.log").write_text(result.stdout + result.stderr)

    chezmoi_apply_log = Path(paths.apply_log)
    if chezmoi_apply_log.exists():
        (logs_dir / "chezmoi.log").write_text(chezmoi_apply_log.read_text())

    return logs_dir


# --- Typer command wiring ---


@app.command()
def up(
    vm: str = typer.Option("dotfiles-test", "--vm"),
    image: str = typer.Option("sequoia", "--image"),
    dotfiles: str | None = typer.Option(None, "--dotfiles"),
) -> None:
    state = up_impl(vm=vm, image=image, dotfiles=dotfiles)
    typer.echo(f"up: {state['vm']} @ {state['ip']} (run {state['run_id']})")


@app.command()
def down(vm: str = typer.Option("dotfiles-test", "--vm")) -> None:
    down_impl(vm=vm)
    typer.echo(f"down: {vm}")


@app.command()
def destroy(vm: str = typer.Option("dotfiles-test", "--vm")) -> None:
    destroy_impl(vm=vm)
    typer.echo(f"destroyed: {vm}")


@app.command()
def apply(
    vm: str = typer.Option("dotfiles-test", "--vm"),
    version_manager: str = typer.Option("mise", "--version-manager"),
) -> None:
    result = apply_impl(vm=vm, version_manager=version_manager)
    typer.echo(f"apply: {result}")


@app.command()
def run(
    vm: str = typer.Option("dotfiles-test", "--vm"),
    image: str = typer.Option("sequoia", "--image"),
    version_manager: str = typer.Option("mise", "--version-manager"),
    dotfiles: str | None = typer.Option(None, "--dotfiles"),
) -> None:
    try:
        verdict = run_impl(vm=vm, image=image, version_manager=version_manager, dotfiles=dotfiles)
    except HarnessError as exc:
        typer.echo(f"run FAILED at phase={exc.phase}: {exc.detail}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"run: {verdict}")


@app.command()
def prune() -> None:
    orphans = prune_impl()
    typer.echo(f"pruned {len(orphans)} orphan clone(s): {orphans}")


@app.command()
def logs(vm: str = typer.Option("dotfiles-test", "--vm")) -> None:
    logs_dir = logs_impl(vm=vm)
    typer.echo(f"logs: {logs_dir}")


@app.command()
def matrix(
    images: str = typer.Option("", "--images", help="Comma-separated; default: config default"),
    version_managers: str = typer.Option("mise,asdf", "--version-managers"),
) -> None:
    image_list = [i.strip() for i in images.split(",") if i.strip()] or None
    vmgr_list = [v.strip() for v in version_managers.split(",") if v.strip()] or None
    results = matrix_impl(images=image_list, version_managers=vmgr_list)
    for leg, verdict in results.items():
        typer.echo(f"{leg}: {verdict}")
