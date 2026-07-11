"""Pure argv builders + parsers for the `utmctl` CLI and host-side UTM state (spec 05 §4.5
"IP discovery without a guest agent (host-side)"; spec 06 §"VirtioFS shared directories" /
§"Importing the tart golden disk"; `specs/utm-improvements.md`).

Stdlib-only. No subprocess execution, no real file reads -- `utm.py` owns that. UTM has no QEMU
guest agent on the Apple backend (05 §4.2: `utmctl exec/file/ip-address` do not work), so IP
discovery here is host-side: a VM's MAC comes from its `.utm/config.plist` (Shared Network mode),
looked up against `/var/db/dhcpd_leases`, with `arp -an` as a fallback.
"""

from __future__ import annotations

import plistlib
import shlex
from dataclasses import dataclass
from typing import Literal, cast

from macos_ci._harness_core import chezmoi_argv

UTMCTL_DEFAULT_PATH = "/Applications/UTM.app/Contents/MacOS/utmctl"
DHCPD_LEASES_PATH = "/var/db/dhcpd_leases"
UTM_DOCUMENTS_DIR = "~/Library/Containers/com.utmapp.UTM/Data/Documents"
VIRTIOFS_SHARE_TAG = "share"
UTM_GUEST_MOUNT_POINT = "/Volumes/dotfiles"

_STOP_MODES = frozenset({"request", "force", "kill"})
StopMode = Literal["request", "force", "kill"]


@dataclass(frozen=True)
class DhcpLease:
    """One `{ ... }` block of `/var/db/dhcpd_leases` (spike B capture,
    `tests/fixtures/utm/dhcpd_leases_sample.txt`)."""

    name: str
    ip_address: str
    hw_address: str
    lease: str


@dataclass(frozen=True)
class UtmVm:
    """One row of `utmctl list` output. `name` may contain spaces."""

    uuid: str
    status: str
    name: str


def normalize_mac(mac: str) -> str:
    """Lowercase, per-octet `f"{int(x,16):x}"` -- `dhcpd_leases`/`arp -an` both drop each octet's
    leading zero rather than zero-padding to two hex digits (spike B capture: `hw_address=1,
    7e:53:c6:f7:88:0`, not `...:88:00`).
    """
    octets = mac.strip().lower().split(":")
    return ":".join(f"{int(o, 16):x}" for o in octets)


def parse_dhcpd_leases(text: str) -> list[DhcpLease]:
    """Parses `{ ... }` blocks of `key=value` lines. `hw_address`/`identifier` carry a `"1,"`
    hardware-type prefix (spike B capture) that is stripped here.
    """
    leases: list[DhcpLease] = []
    block: dict[str, str] = {}
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "{":
            block = {}
            in_block = True
            continue
        if stripped == "}":
            if in_block:
                hw_address = block.get("hw_address", "")
                if hw_address.startswith("1,"):
                    hw_address = hw_address[2:]
                leases.append(
                    DhcpLease(
                        name=block.get("name", ""),
                        ip_address=block.get("ip_address", ""),
                        hw_address=hw_address,
                        lease=block.get("lease", ""),
                    )
                )
            in_block = False
            continue
        if in_block and "=" in stripped:
            key, _, value = stripped.partition("=")
            block[key.strip()] = value.strip()
    return leases


def find_ip_for_mac(leases_text: str, mac: str) -> str | None:
    """Newest lease wins: `lease` is a hex counter (spike B capture, e.g. `0x6a517572`) that only
    increases across renewals, so the numerically-largest match for a given MAC is the current one.
    """
    target = normalize_mac(mac)
    matches = [
        lease
        for lease in parse_dhcpd_leases(leases_text)
        if normalize_mac(lease.hw_address) == target
    ]
    if not matches:
        return None

    def _lease_value(lease: DhcpLease) -> int:
        try:
            return int(lease.lease, 16)
        except ValueError:
            return 0

    return max(matches, key=_lease_value).ip_address


def find_ip_for_mac_arp(arp_output: str, mac: str) -> str | None:
    """Fallback over `arp -an` (spike B capture,
    `tests/fixtures/utm/arp-an-sample.txt`): `? (192.168.3.1) at 74:ac:b9:1a:a8:9 on en0 ifscope
    [ethernet]`.
    """
    target = normalize_mac(mac)
    for line in arp_output.splitlines():
        stripped = line.strip()
        if "(" not in stripped or ") at " not in stripped:
            continue
        ip_address = stripped.split("(", 1)[1].split(")", 1)[0]
        after_at = stripped.split(" at ", 1)[1]
        mac_part = after_at.split(" ", 1)[0]
        if mac_part.lower() == "(incomplete)":
            continue
        if normalize_mac(mac_part) == target:
            return ip_address
    return None


def extract_macs_from_config_plist(data: bytes) -> list[str]:
    """`plistlib.loads` autodetects XML vs binary. Recursive walk collecting every `MacAddress`
    string value -- defensive against UTM config-schema drift across versions rather than
    hardcoding a key path (spike B open risk #5: "config.plist MAC key path may vary by UTM
    version").
    """
    root = cast(object, plistlib.loads(data))
    found: list[str] = []

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in cast(dict[str, object], node).items():
                if key == "MacAddress" and isinstance(value, str):
                    found.append(normalize_mac(value))
                else:
                    _walk(value)
        elif isinstance(node, list):
            for item in cast(list[object], node):
                _walk(item)

    _walk(root)
    return found


def bundle_config_path(documents_dir: str, vm_name: str) -> str:
    return f"{documents_dir}/{vm_name}.utm/config.plist"


def list_argv(*, utmctl: str = UTMCTL_DEFAULT_PATH) -> list[str]:
    return [utmctl, "list"]


def status_argv(name: str, *, utmctl: str = UTMCTL_DEFAULT_PATH) -> list[str]:
    return [utmctl, "status", name]


def start_argv(
    name: str,
    *,
    recovery: bool = False,
    hide: bool = False,
    utmctl: str = UTMCTL_DEFAULT_PATH,
) -> list[str]:
    """No `--hide` by default -- the window is the product (this lane exists to look at the GUI)."""
    argv = [utmctl, "start"]
    if hide:
        argv.append("--hide")
    argv.append(name)
    if recovery:
        argv.append("--recovery")
    return argv


def stop_argv(
    name: str, *, mode: StopMode = "request", utmctl: str = UTMCTL_DEFAULT_PATH
) -> list[str]:
    if mode not in _STOP_MODES:
        raise ValueError(f"unknown stop mode {mode!r}, expected one of {sorted(_STOP_MODES)}")
    return [utmctl, "stop", name, f"--{mode}"]


def clone_argv(
    source: str, *, name: str | None = None, utmctl: str = UTMCTL_DEFAULT_PATH
) -> list[str]:
    argv = [utmctl, "clone", source]
    if name is not None:
        argv += ["--name", name]
    return argv


def delete_argv(name: str, *, utmctl: str = UTMCTL_DEFAULT_PATH) -> list[str]:
    return [utmctl, "delete", name]


def attach_argv(
    name: str, *, index: int | None = None, utmctl: str = UTMCTL_DEFAULT_PATH
) -> list[str]:
    argv = [utmctl, "attach", name]
    if index is not None:
        argv += ["--index", str(index)]
    return argv


def parse_utmctl_list(text: str) -> list[UtmVm]:
    """Skips the header row; `name` is parsed with `split(maxsplit=2)` because it may contain
    spaces.
    """
    vms: list[UtmVm] = []
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue
        uuid, status, name = parts
        vms.append(UtmVm(uuid=uuid, status=status, name=name))
    return vms


def virtiofs_mount_commands(
    mount_point: str = UTM_GUEST_MOUNT_POINT, tag: str = VIRTIOFS_SHARE_TAG
) -> list[str]:
    """guest-support/macos/#shared-directories: `mkdir -m 777 -p <mnt>` then
    `mount_virtiofs <tag> <mnt>`, run in the guest.
    """
    quoted = shlex.quote(mount_point)
    return [
        f"mkdir -m 777 -p {quoted}",
        f"mount_virtiofs {tag} {quoted}",
    ]


def build_screencapture_argv(
    path: str, *, window_id: int | None = None, full: bool = False
) -> list[str]:
    """`utm shot`'s capture step (spec mvp.md A1). `-x`: no sound; `-o`: no window shadow. A
    `window_id` targets one window by CGWindowID unless `full` overrides it to whole-display.
    """
    argv = ["/usr/sbin/screencapture", "-x", "-o"]
    if window_id is not None and not full:
        argv += ["-l", str(window_id)]
    argv.append(path)
    return argv


def manual_apply_script(*, source: str, version_manager: str = "mise") -> str:
    """The paste-into-iTerm2 block: VirtioFS mount, then the `~/.local/share/chezmoi` symlink
    (same rationale as `harness.py::_bootstrap_chezmoi_source_symlink` -- `plugins.toml`'s
    `[plugins.bossaliases]` hardcodes that conventional path), then the same `chezmoi_argv` shape
    the tart lane uses (spec 08(b)). SSH is the feedback channel, not the applier -- the human runs
    this block by hand.
    """
    symlink_command = (
        f"mkdir -p ~/.local/share && ln -sfn {shlex.quote(source)} ~/.local/share/chezmoi"
    )
    apply_command = shlex.join(chezmoi_argv(source=source, version_manager=version_manager))
    return "\n".join([*virtiofs_mount_commands(), symlink_command, apply_command])
