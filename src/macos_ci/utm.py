"""I/O shell: executes argv built by `_utm_core` and reads/parses UTM host state (spec 05 §4.5
"IP discovery without a guest agent (host-side)"; `specs/utm-improvements.md`).

SSH transport mirrors `harness.py`'s two-phase bootstrap (see its module docstring): one
password-authenticated connection seeds the harness key into the guest, then every subsequent
command uses key-based, `BatchMode=yes` auth. A full extraction into a shared `sshboot.py` is an
optional later refactor -- out of scope here (`specs/utm-improvements.md` step 4).
"""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, cast

import typer

from macos_ci import artifacts
from macos_ci._gui_core import next_screenshot_sequence, screenshot_filename
from macos_ci._harness_core import (
    bootstrap_ssh_argv,
    format_run_id,
    steady_state_ssh_argv,
)
from macos_ci._utm_core import (
    DHCPD_LEASES_PATH,
    UTM_DOCUMENTS_DIR,
    UTM_GUEST_MOUNT_POINT,
    StopMode,
    UtmVm,
    build_screencapture_argv,
    bundle_config_path,
    clone_argv,
    delete_argv,
    extract_macs_from_config_plist,
    find_ip_for_mac,
    find_ip_for_mac_arp,
    list_argv,
    manual_apply_script,
    parse_utmctl_list,
    start_argv,
    status_argv,
    stop_argv,
)

app: typer.Typer = typer.Typer(
    help="Manual GUI lane for UTM (spec 10: human escape hatch -- never gates CI)."
)

_UTM_APP_INFO_PLIST = "/Applications/UTM.app/Contents/Info.plist"
_VM_USER = "admin"
_KEY_PATH = Path("harness/ssh/id_ed25519_harness")
_IP_WAIT_SECS = 180.0
_SSH_WAIT_SECS = 60.0

# Naming convention (spec's "Notes" §"Config stays convention-based"): the UTM golden is a
# one-time hand-made artifact, env-overridable, distinct from the tart-lane names in harness.py.
_UTM_VM_DEFAULT = "dotfiles-utm"
_UTM_GOLDEN_DEFAULT = "dotfiles-golden-utm"
_TART_GOLDEN_DEFAULT = "dotfiles-golden"
_IMPORT_STAGING_DIR = Path("artifacts/utm-import")
_IMPORT_SCRATCH_VM_DEFAULT = "utm-export-scratch"


class UtmError(RuntimeError):
    """A UTM-lane phase failed. `str(exc)` is the phase name; `.detail` is why (mirrors
    `harness.HarnessError`)."""

    phase: str
    detail: str

    def __init__(self, phase: str, detail: str) -> None:
        super().__init__(phase)
        self.phase = phase
        self.detail = detail


def utm_app_version() -> str | None:
    """`CFBundleShortVersionString` from `UTM.app/Contents/Info.plist`.

    Never `utmctl version` -- that subcommand launches UTM.app (unlike `--help`, pgrep-confirmed
    clean on this host: `tests/fixtures/utm/spike-a-disk-format.md` and the utmctl-help fixtures).
    A doctor row must never have the side effect of opening a GUI app.
    """
    path = Path(_UTM_APP_INFO_PLIST)
    if not path.exists():
        return None
    try:
        data = cast(dict[str, object], plistlib.loads(path.read_bytes()))
    except (OSError, ValueError):
        return None
    version = data.get("CFBundleShortVersionString")
    return version if isinstance(version, str) else None


def _documents_dir() -> str:
    return os.environ.get("MACOS_CI_UTM_DIR", UTM_DOCUMENTS_DIR)


def list_vms() -> list[UtmVm]:
    result = subprocess.run(list_argv(), check=True, capture_output=True, text=True)
    return parse_utmctl_list(result.stdout)


def status(name: str) -> str:
    result = subprocess.run(status_argv(name), check=True, capture_output=True, text=True)
    return result.stdout.strip()


def start(name: str, *, recovery: bool = False, hide: bool = False) -> None:
    subprocess.run(start_argv(name, recovery=recovery, hide=hide), check=True)


def stop(name: str, *, mode: StopMode = "request") -> None:
    subprocess.run(stop_argv(name, mode=mode), check=True)


def clone(source: str, *, name: str | None = None) -> None:
    subprocess.run(clone_argv(source, name=name), check=True)


def delete(name: str) -> None:
    subprocess.run(delete_argv(name), check=True)


def read_config_plist_bytes(vm_name: str) -> bytes:
    path = Path(bundle_config_path(_documents_dir(), vm_name)).expanduser()
    return path.read_bytes()


def mac_for_vm(vm_name: str) -> str:
    macs = extract_macs_from_config_plist(read_config_plist_bytes(vm_name))
    if not macs:
        raise UtmError("mac-for-vm", f"no MacAddress found in {vm_name}.utm/config.plist")
    return macs[0]


def ip(name: str, *, leases_path: str = DHCPD_LEASES_PATH) -> str | None:
    """MAC (from the bundle's `config.plist`) -> `dhcpd_leases` -> `arp -an` fallback (spec 05
    §4.5). Returns `None` rather than raising -- callers decide whether "not yet up" is fatal."""
    mac = mac_for_vm(name)
    leases_text = Path(leases_path).read_text()
    found = find_ip_for_mac(leases_text, mac)
    if found:
        return found
    arp_result = subprocess.run(["arp", "-an"], capture_output=True, text=True)
    return find_ip_for_mac_arp(arp_result.stdout, mac)


def wait_for_ip(name: str, *, timeout: float = _IP_WAIT_SECS) -> str:
    deadline = time.monotonic() + timeout
    while True:
        found = ip(name)
        if found:
            return found
        if time.monotonic() >= deadline:
            raise UtmError("wait-for-ip", f"no IP found for {name} within {timeout}s")
        time.sleep(2)


def _ensure_key_permissions() -> None:
    if _KEY_PATH.exists():
        _KEY_PATH.chmod(0o600)


def _bootstrap_key_trust(ip_address: str) -> None:
    _ensure_key_permissions()
    pubkey_path = Path(f"{_KEY_PATH}.pub")
    argv = bootstrap_ssh_argv(ip_address, user=_VM_USER)
    result = subprocess.run(
        argv, input=pubkey_path.read_text(), capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise UtmError("bootstrap-key-trust", result.stderr.strip() or result.stdout.strip())


def _wait_for_ssh(ip_address: str, *, timeout: float = _SSH_WAIT_SECS) -> None:
    deadline = time.monotonic() + timeout
    while True:
        argv = steady_state_ssh_argv(ip_address, "true", user=_VM_USER, key_path=str(_KEY_PATH))
        result = subprocess.run(argv, capture_output=True, text=True)
        if result.returncode == 0:
            return
        if time.monotonic() >= deadline:
            detail = (
                f"key-based SSH to {ip_address} not reachable within {timeout}s: "
                + result.stderr.strip()
            )
            raise UtmError("wait-for-ssh", detail)
        time.sleep(2)


def up_impl(*, vm: str = _UTM_VM_DEFAULT, golden: str = _UTM_GOLDEN_DEFAULT) -> dict[str, Any]:
    """`utmctl clone` (if missing) -> windowed `utmctl start` -> MAC->leases/arp IP -> two-phase
    SSH bootstrap -> `state.json` with `lane: "utm"`. Mirrors `harness.up_impl`'s shape but never
    touches a tart VM; the human drives the dotfiles apply afterward (`bootstrap-dotfiles`), SSH
    here is only the feedback channel.
    """
    existing_names = {existing.name for existing in list_vms()}
    if vm not in existing_names:
        clone(golden, name=vm)
    start(vm)  # windowed by default -- the window is the product

    ip_address = wait_for_ip(vm)
    _bootstrap_key_trust(ip_address)
    _wait_for_ssh(ip_address)

    run_id = format_run_id(
        timestamp=time.strftime("%Y%m%d-%H%M%S"), suffix=f"{time.monotonic_ns() % 1_000_000:06d}"
    )
    state: dict[str, Any] = {
        "vm": vm,
        "ip": ip_address,
        "run_id": run_id,
        "lane": "utm",
        "mount_point": UTM_GUEST_MOUNT_POINT,
        "phase": "up",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    artifacts.write_json(run_id, "state.json", state)
    return state


def _resolve_latest_run_id() -> str:
    """`artifacts/latest` is the symlink `artifacts.write_json` repoints at every write (spec 12);
    reading through it is how `up_impl`'s `run_id` is recovered by a later `shot` invocation
    without a second, redundant "latest run" mechanism (mirrors `harness._read_latest_state`, but
    raises `UtmError` to stay in this lane's error type).
    """
    latest = artifacts.artifacts_root() / "latest" / "state.json"
    if not latest.exists():
        raise UtmError("resolve-run", "no artifacts/latest/state.json -- run `just utm-up` first")
    data = cast(dict[str, Any], json.loads(latest.read_text()))
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise UtmError("resolve-run", "artifacts/latest/state.json has no run_id")
    return run_id


def _foreground_utm() -> None:
    """Best-effort: bring UTM.app forward so the window being captured is on top. Never fatal --
    `screencapture` can still succeed (e.g. `--full`) even if this fails.
    """
    subprocess.run(["open", "-a", "UTM"], check=False)


def _resolve_utm_window_id(vm: str) -> int | None:
    """Dependency-free CGWindowID lookup via `osascript` (no pyobjc/Quartz -- spec mvp.md A2's
    honest design note: this repo values no-new-deps). Any failure -- osascript missing, UTM not
    running, window not found, unparseable output -- degrades to `None`, and the caller falls back
    to a whole-display capture rather than ever raising.
    """
    script = (
        'tell application "System Events" to tell process "UTM" '
        f'to get id of first window whose name contains "{vm}"'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def shot_impl(*, label: str, vm: str = _UTM_VM_DEFAULT, full: bool = False) -> str:
    """Host-side `screencapture` of the UTM window into `artifacts/<run-id>/screenshots/` -- the
    only capture path for an Apple-backend guest (no VNC framebuffer, no in-guest screencapture
    over SSH; spec mvp.md A2). Foregrounds UTM, best-effort resolves the VM's window id, and falls
    back to a whole-display capture (`full=True`, or window-id resolution failing) rather than
    ever failing the capture outright.
    """
    run_id = _resolve_latest_run_id()
    screenshots_dir = artifacts.run_dir(run_id) / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    sequence = next_screenshot_sequence(os.listdir(screenshots_dir))
    filename = screenshot_filename(sequence, label)
    path = str(screenshots_dir / filename)

    _foreground_utm()
    window_id = None if full else _resolve_utm_window_id(vm)
    subprocess.run(build_screencapture_argv(path, window_id=window_id, full=full), check=True)
    return path


def doctor_impl(
    *, golden: str = _UTM_GOLDEN_DEFAULT, leases_path: str = DHCPD_LEASES_PATH
) -> list[dict[str, Any]]:
    """UTM.app version (Info.plist only, never launches the app), golden bundle presence, and
    `dhcpd_leases` readability -- the three facts `just utm-doctor` reports (spec table, step 7).
    """
    version = utm_app_version()
    golden_bundle = Path(bundle_config_path(_documents_dir(), golden)).expanduser().parent
    golden_exists = golden_bundle.exists()
    leases_readable = os.access(leases_path, os.R_OK)
    return [
        {"tool": "utm", "found": version, "ok": version is not None},
        {
            "tool": "utm-golden-bundle",
            "found": str(golden_bundle) if golden_exists else None,
            "ok": golden_exists,
        },
        {
            "tool": "dhcpd-leases-readable",
            "found": leases_path if leases_readable else None,
            "ok": leases_readable,
        },
    ]


_IMPORT_CHECKLIST_TEMPLATE = """
Manual GUI import checklist (one-time; the Apple backend has no scriptable import path):
  1. Open UTM.app -> Create a New Virtual Machine -> Virtualize -> macOS.
  2. In Drive settings, delete the auto-created disk.
  3. Import the staged raw image above as the VM's drive ("Only raw images are supported").
  4. Set Network = Shared Network (spec 05 sect 4.5's IP discovery depends on this).
  5. Add a VirtioFS shared directory pointing at your zsh-dotfiles checkout.
  6. Add a serial (PTTY) device -- the `utm-serial` degraded path if IP discovery ever fails.
  7. Boot; log in as admin/admin; confirm SSH answers (`just utm-up` then `just utm-ssh`).
Name the VM "{golden}" so `just utm-clone`/`just utm-up` find it by default.
""".strip()


def import_golden_impl(
    *,
    tart_vm: str = _TART_GOLDEN_DEFAULT,
    scratch_vm: str = _IMPORT_SCRATCH_VM_DEFAULT,
    dest_dir: Path = _IMPORT_STAGING_DIR,
) -> Path:
    """Stages the tart golden disk as a raw image for manual UTM import (spec 06 "Importing the
    tart golden disk"). Never touches the live golden: clones it first via `tart clone` (fast,
    copy-on-write -- unlike a byte-for-byte disk copy) and stages FROM the throwaway clone, which
    is deleted again afterward.
    """
    subprocess.run(["tart", "clone", tart_vm, scratch_vm], check=True)
    try:
        source = Path.home() / ".tart" / "vms" / scratch_vm / "disk.img"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "disk.img"
        shutil.copy2(source, dest)
    finally:
        subprocess.run(["tart", "delete", scratch_vm], check=True)
    return dest


# --- Typer command wiring ---


@app.command("doctor")
def doctor_command(
    golden: str = typer.Option(_UTM_GOLDEN_DEFAULT, "--golden"),
) -> None:
    rows = doctor_impl(golden=golden)
    ok = all(row["ok"] for row in rows)
    for row in rows:
        mark = "OK" if row["ok"] else "MISSING"
        typer.echo(f"[{mark:>7}] {row['tool']:<24} found={row['found']}")
    raise typer.Exit(code=0 if ok else 2)


@app.command("ip")
def ip_command(vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm")) -> None:
    found = ip(vm)
    if found is None:
        typer.echo(
            "no IP found (leases + arp both missed) -- try `utm serial` for the degraded path",
            err=True,
        )
        raise typer.Exit(code=2)
    typer.echo(found)


@app.command("mac")
def mac_command(vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm")) -> None:
    typer.echo(mac_for_vm(vm))


@app.command("up")
def up_command(
    vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm"),
    golden: str = typer.Option(_UTM_GOLDEN_DEFAULT, "--golden"),
) -> None:
    state = up_impl(vm=vm, golden=golden)
    typer.echo(f"up: {state['vm']} @ {state['ip']} (run {state['run_id']}, lane={state['lane']})")


@app.command("status")
def status_command(vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm")) -> None:
    typer.echo(status(vm))


@app.command("stop")
def stop_command(vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm")) -> None:
    stop(vm)
    typer.echo(f"stopped: {vm}")


@app.command("shot")
def shot_command(
    label: str,
    vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm"),
    full: bool = typer.Option(False, "--full"),
) -> None:
    saved = shot_impl(label=label, vm=vm, full=full)
    typer.echo(saved)


@app.command("destroy")
def destroy_command(vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm")) -> None:
    if vm == _UTM_GOLDEN_DEFAULT:
        typer.echo(f"refusing to destroy the golden VM {vm!r}", err=True)
        raise typer.Exit(code=2)
    delete(vm)
    typer.echo(f"destroyed: {vm}")


@app.command("clone")
def clone_command(
    vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm"),
    golden: str = typer.Option(_UTM_GOLDEN_DEFAULT, "--golden"),
) -> None:
    existing_names = {existing.name for existing in list_vms()}
    if vm in existing_names:
        typer.echo(f"clone: {vm} already exists, no-op")
        return
    clone(golden, name=vm)
    typer.echo(f"cloned: {golden} -> {vm}")


@app.command("bootstrap-dotfiles")
def bootstrap_dotfiles_command(
    version_manager: str = typer.Option("mise", "--version-manager"),
) -> None:
    typer.echo(manual_apply_script(source=UTM_GUEST_MOUNT_POINT, version_manager=version_manager))


@app.command("import-golden")
def import_golden_command(
    tart_vm: str = typer.Option(_TART_GOLDEN_DEFAULT, "--tart-vm"),
) -> None:
    dest = import_golden_impl(tart_vm=tart_vm)
    typer.echo(f"staged raw disk at {dest}")
    typer.echo(_IMPORT_CHECKLIST_TEMPLATE.format(golden=_UTM_GOLDEN_DEFAULT))
