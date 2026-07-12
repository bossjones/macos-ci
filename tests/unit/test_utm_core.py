"""Unit coverage for `_utm_core.py`'s pure argv builders and parsers (spec 05 §4.5, spec 06
§"VirtioFS shared directories" / §"Importing the tart golden disk";
`specs/utm-improvements.md` step 3).

Bare asserts on exact argv lists / parsed values, style of `test_tart_core.py`. Fixtures under
`tests/fixtures/utm/` are real captures from this host (2026-07-10): `utmctl --help` variants
(pgrep-confirmed not to launch UTM.app) and real `/var/db/dhcpd_leases` blocks -- see
`tests/fixtures/utm/spike-a-disk-format.md` for the capture notes.
"""

from __future__ import annotations

import plistlib
import shlex
from pathlib import Path

from macos_ci._harness_core import chezmoi_argv
from macos_ci._utm_core import (
    UTM_DOCUMENTS_DIR,
    UTM_GUEST_MOUNT_POINT,
    UTMCTL_DEFAULT_PATH,
    VIRTIOFS_SHARE_TAG,
    DhcpLease,
    UtmVm,
    attach_argv,
    build_screencapture_argv,
    build_window_id_jxa_argv,
    bundle_config_path,
    clone_argv,
    delete_argv,
    extract_macs_from_config_plist,
    find_ip_for_mac,
    find_ip_for_mac_arp,
    list_argv,
    manual_apply_script,
    normalize_mac,
    parse_dhcpd_leases,
    parse_utmctl_list,
    start_argv,
    status_argv,
    stop_argv,
    virtiofs_mount_commands,
)

_FIXTURES = Path(__file__).parent.parent / "fixtures" / "utm"


def test_normalize_mac_lowercases_and_strips_octet_zero_padding() -> None:
    # Real capture (tests/fixtures/utm/dhcpd_leases_sample.txt block 3): hw_address=1,7e:53:c6:f7:88:0
    # -- dhcpd_leases drops each octet's leading zero rather than zero-padding to two hex digits.
    assert normalize_mac("7E:53:C6:F7:88:00") == "7e:53:c6:f7:88:0"
    assert normalize_mac("7e:53:c6:f7:88:0") == "7e:53:c6:f7:88:0"


def test_parse_dhcpd_leases_single_block() -> None:
    text = _FIXTURES.joinpath("dhcpd_leases_sample.txt").read_text()
    leases = parse_dhcpd_leases(text)
    assert leases[0] == DhcpLease(
        name="ManagedlMachine",
        ip_address="192.168.252.186",
        hw_address="ba:50:91:fd:a5:99",
        lease="0x6a517572",
    )
    # 3 verbatim blocks captured -- confirms multi-block parsing, not just the first.
    assert len(leases) == 3


def test_find_ip_for_mac_prefers_newest_lease() -> None:
    # Synthetic (not a fixture): two leases for the same MAC, different lease/ip -- proves the
    # newest-wins tie-break, which no single real capture demonstrates on its own.
    text = """\
{
\tname=old
\tip_address=192.168.1.10
\thw_address=1,aa:bb:cc:dd:ee:ff
\tidentifier=1,aa:bb:cc:dd:ee:ff
\tlease=0x1
}
{
\tname=new
\tip_address=192.168.1.20
\thw_address=1,aa:bb:cc:dd:ee:ff
\tidentifier=1,aa:bb:cc:dd:ee:ff
\tlease=0x99
}
"""
    assert find_ip_for_mac(text, "AA:BB:CC:DD:EE:FF") == "192.168.1.20"


def test_find_ip_for_mac_returns_none_when_absent() -> None:
    text = _FIXTURES.joinpath("dhcpd_leases_sample.txt").read_text()
    assert find_ip_for_mac(text, "00:00:00:00:00:00") is None


def test_find_ip_for_mac_arp() -> None:
    text = _FIXTURES.joinpath("arp-an-sample.txt").read_text()
    # Real capture line: "? (192.168.3.1) at 74:ac:b9:1a:a8:9 on en0 ifscope [ethernet]" -- query
    # with a zero-padded form to prove find_ip_for_mac_arp normalizes both sides.
    assert find_ip_for_mac_arp(text, "74:ac:b9:1a:a8:09") == "192.168.3.1"


def test_find_ip_for_mac_arp_returns_none_when_absent() -> None:
    text = _FIXTURES.joinpath("arp-an-sample.txt").read_text()
    assert find_ip_for_mac_arp(text, "00:00:00:00:00:00") is None


def _plist_bytes(fmt: plistlib.PlistFormat) -> bytes:
    # A UTM config.plist is schema-unstable across versions (spike B open risk #5) -- nest
    # MacAddress at more than one depth to prove the walk is recursive, not a fixed key path.
    data = {
        "Backend": "Apple",
        "Network": [
            {"Interface": "en0", "MacAddress": "AA:BB:CC:00:11:22"},
        ],
        "Display": {"Nested": {"MacAddress": "de:ad:be:ef:00:01"}},
    }
    return plistlib.dumps(data, fmt=fmt)


def test_extract_macs_from_config_plist_xml() -> None:
    # plistlib.dumps sort_keys=True (its default) reorders top-level keys alphabetically, so
    # "Display" (nested) sorts before "Network" (list) -- assert as a set, order isn't load-bearing.
    data = _plist_bytes(plistlib.FMT_XML)
    assert sorted(extract_macs_from_config_plist(data)) == ["aa:bb:cc:0:11:22", "de:ad:be:ef:0:1"]


def test_extract_macs_from_config_plist_binary() -> None:
    data = _plist_bytes(plistlib.FMT_BINARY)
    assert sorted(extract_macs_from_config_plist(data)) == ["aa:bb:cc:0:11:22", "de:ad:be:ef:0:1"]


def test_bundle_config_path() -> None:
    assert bundle_config_path(UTM_DOCUMENTS_DIR, "dotfiles-utm") == (
        f"{UTM_DOCUMENTS_DIR}/dotfiles-utm.utm/config.plist"
    )


def test_start_argv_shows_window_by_default() -> None:
    # "the window is the product" -- no --hide unless explicitly requested.
    assert start_argv("dotfiles-utm") == [UTMCTL_DEFAULT_PATH, "start", "dotfiles-utm"]


def test_start_argv_hide() -> None:
    assert start_argv("dotfiles-utm", hide=True) == [
        UTMCTL_DEFAULT_PATH,
        "start",
        "--hide",
        "dotfiles-utm",
    ]


def test_start_argv_recovery() -> None:
    assert start_argv("dotfiles-utm", recovery=True) == [
        UTMCTL_DEFAULT_PATH,
        "start",
        "dotfiles-utm",
        "--recovery",
    ]


def test_stop_argv_modes() -> None:
    # Real capture (tests/fixtures/utm/utmctl-stop-help.txt): --force / --kill / --request.
    assert stop_argv("dotfiles-utm", mode="request") == [
        UTMCTL_DEFAULT_PATH,
        "stop",
        "dotfiles-utm",
        "--request",
    ]
    assert stop_argv("dotfiles-utm", mode="force")[-1] == "--force"
    assert stop_argv("dotfiles-utm", mode="kill")[-1] == "--kill"


def test_clone_argv_shape() -> None:
    # Pinned to tests/fixtures/utm/utmctl-clone-help.txt: `utmctl clone <identifier> [--name <name>]`.
    assert clone_argv("dotfiles-golden-utm") == [
        UTMCTL_DEFAULT_PATH,
        "clone",
        "dotfiles-golden-utm",
    ]
    assert clone_argv("dotfiles-golden-utm", name="dotfiles-utm") == [
        UTMCTL_DEFAULT_PATH,
        "clone",
        "dotfiles-golden-utm",
        "--name",
        "dotfiles-utm",
    ]


def test_delete_argv() -> None:
    assert delete_argv("dotfiles-utm") == [UTMCTL_DEFAULT_PATH, "delete", "dotfiles-utm"]


def test_status_argv() -> None:
    assert status_argv("dotfiles-utm") == [UTMCTL_DEFAULT_PATH, "status", "dotfiles-utm"]


def test_list_argv() -> None:
    assert list_argv() == [UTMCTL_DEFAULT_PATH, "list"]


def test_attach_argv_index() -> None:
    # Real capture (tests/fixtures/utm/utmctl-attach-help.txt): `--index <index>`.
    assert attach_argv("dotfiles-utm") == [UTMCTL_DEFAULT_PATH, "attach", "dotfiles-utm"]
    assert attach_argv("dotfiles-utm", index=1) == [
        UTMCTL_DEFAULT_PATH,
        "attach",
        "dotfiles-utm",
        "--index",
        "1",
    ]


def test_parse_utmctl_list_name_with_spaces() -> None:
    text = (
        "UUID                                 Status   Name\n"
        "12345678-ABCD-1234-ABCD-1234567890AB stopped  dotfiles golden utm\n"
    )
    assert parse_utmctl_list(text) == [
        UtmVm(
            uuid="12345678-ABCD-1234-ABCD-1234567890AB",
            status="stopped",
            name="dotfiles golden utm",
        )
    ]


def test_parse_utmctl_list_empty() -> None:
    # Real capture (tests/fixtures/utm/utmctl-list-output.txt): header only, no VMs registered yet
    # on this host -- confirms the header-skip doesn't choke on zero rows.
    text = _FIXTURES.joinpath("utmctl-list-output.txt").read_text()
    assert parse_utmctl_list(text) == []


def test_virtiofs_mount_commands() -> None:
    # guest-support/macos/#shared-directories: `mkdir -m 777 -p <mnt>` then `mount_virtiofs share <mnt>`.
    assert virtiofs_mount_commands() == [
        f"mkdir -m 777 -p {shlex.quote(UTM_GUEST_MOUNT_POINT)}",
        f"mount_virtiofs {VIRTIOFS_SHARE_TAG} {shlex.quote(UTM_GUEST_MOUNT_POINT)}",
    ]


def test_virtiofs_mount_commands_custom_args() -> None:
    assert virtiofs_mount_commands(mount_point="/Volumes/x", tag="other") == [
        "mkdir -m 777 -p /Volumes/x",
        "mount_virtiofs other /Volumes/x",
    ]


def test_manual_apply_script_embeds_chezmoi_argv() -> None:
    script = manual_apply_script(source=UTM_GUEST_MOUNT_POINT, version_manager="mise")
    expected_apply = shlex.join(chezmoi_argv(source=UTM_GUEST_MOUNT_POINT, version_manager="mise"))
    assert expected_apply in script
    # The VirtioFS mount and the hardcoded-source symlink (harness.py's
    # _bootstrap_chezmoi_source_symlink rationale) both precede the apply line.
    assert "mount_virtiofs" in script
    assert "ln -sfn" in script
    assert "~/.local/share/chezmoi" in script
    assert script.index("mount_virtiofs") < script.index(expected_apply)


def test_build_screencapture_argv_default_is_full_display() -> None:
    # Neither window_id nor full given -- no -l flag (whole-display capture).
    assert build_screencapture_argv("/tmp/hero.png") == [
        "/usr/sbin/screencapture",
        "-x",
        "-o",
        "/tmp/hero.png",
    ]


def test_build_screencapture_argv_window_id() -> None:
    assert build_screencapture_argv("/tmp/hero.png", window_id=42) == [
        "/usr/sbin/screencapture",
        "-x",
        "-o",
        "-l",
        "42",
        "/tmp/hero.png",
    ]


def test_build_screencapture_argv_full() -> None:
    # full=True wins over a passed window_id -- whole-display capture, no -l.
    assert build_screencapture_argv("/tmp/hero.png", window_id=42, full=True) == [
        "/usr/sbin/screencapture",
        "-x",
        "-o",
        "/tmp/hero.png",
    ]


def test_build_window_id_jxa_argv_shape() -> None:
    argv = build_window_id_jxa_argv("dotfiles-utm")
    assert argv[:4] == ["osascript", "-l", "JavaScript", "-e"]
    assert len(argv) == 5
    script = argv[4]
    assert "CGWindowListCopyWindowInfo" in script
    assert "kCGWindowNumber" in script
    assert '"dotfiles-utm"' in script


def test_build_window_id_jxa_argv_quotes_vm_name() -> None:
    # A hostile VM name must land as a JS string literal, not injected syntax.
    script = build_window_id_jxa_argv('x").includes("')[-1]
    assert '"x\\").includes(\\""' in script
