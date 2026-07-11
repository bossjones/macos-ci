"""Unit coverage for `utm.py`'s I/O shell (spec 05 §4.5; `specs/utm-improvements.md` step 4).

pytest-subprocess (`FakeProcess`) + `tmp_path`, style of `test_harness.py` -- no real `utmctl`, no
real leases file, no UTM.app.
"""

from __future__ import annotations

import plistlib
from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess

from macos_ci import utm
from macos_ci._utm_core import UTMCTL_DEFAULT_PATH, UtmVm


def test_list_vms_invokes_no_real_utmctl(fake_process: FakeProcess) -> None:
    fake_process.register(
        [UTMCTL_DEFAULT_PATH, "list"],
        stdout=(
            "UUID                                 Status   Name\n"
            "12345678-ABCD-1234-ABCD-1234567890AB stopped  dotfiles-utm\n"
        ),
    )

    vms = utm.list_vms()

    assert vms == [
        UtmVm(uuid="12345678-ABCD-1234-ABCD-1234567890AB", status="stopped", name="dotfiles-utm")
    ]
    assert list(fake_process.calls)[-1] == [UTMCTL_DEFAULT_PATH, "list"]


def test_ip_reads_leases_file_not_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(utm, "mac_for_vm", lambda name: "aa:bb:cc:dd:ee:ff")
    leases_path = tmp_path / "dhcpd_leases"
    leases_path.write_text(
        "{\n"
        "\tname=dotfiles-utm\n"
        "\tip_address=192.168.64.9\n"
        "\thw_address=1,aa:bb:cc:dd:ee:ff\n"
        "\tidentifier=1,aa:bb:cc:dd:ee:ff\n"
        "\tlease=0x1\n"
        "}\n"
    )

    result = utm.ip("dotfiles-utm", leases_path=str(leases_path))

    assert result == "192.168.64.9"


def test_ip_falls_back_to_arp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_process: FakeProcess
) -> None:
    monkeypatch.setattr(utm, "mac_for_vm", lambda name: "aa:bb:cc:dd:ee:ff")
    leases_path = tmp_path / "dhcpd_leases"
    leases_path.write_text("")  # no lease for this MAC -- forces the arp fallback
    fake_process.register(
        ["arp", "-an"],
        stdout="? (192.168.64.20) at aa:bb:cc:dd:ee:ff on bridge100 ifscope [ethernet]\n",
    )

    result = utm.ip("dotfiles-utm", leases_path=str(leases_path))

    assert result == "192.168.64.20"


def test_ip_returns_none_when_neither_source_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_process: FakeProcess
) -> None:
    monkeypatch.setattr(utm, "mac_for_vm", lambda name: "aa:bb:cc:dd:ee:ff")
    leases_path = tmp_path / "dhcpd_leases"
    leases_path.write_text("")
    fake_process.register(["arp", "-an"], stdout="")

    assert utm.ip("dotfiles-utm", leases_path=str(leases_path)) is None


def test_mac_for_vm_reads_bundle_plist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MACOS_CI_UTM_DIR", str(tmp_path))
    bundle = tmp_path / "dotfiles-utm.utm"
    bundle.mkdir()
    (bundle / "config.plist").write_bytes(
        plistlib.dumps({"Network": [{"MacAddress": "AA:BB:CC:00:11:02"}]})
    )

    assert utm.mac_for_vm("dotfiles-utm") == "aa:bb:cc:0:11:2"


def test_mac_for_vm_raises_utm_error_when_no_mac_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MACOS_CI_UTM_DIR", str(tmp_path))
    bundle = tmp_path / "dotfiles-utm.utm"
    bundle.mkdir()
    (bundle / "config.plist").write_bytes(plistlib.dumps({"Backend": "Apple"}))

    with pytest.raises(utm.UtmError) as exc_info:
        utm.mac_for_vm("dotfiles-utm")
    assert exc_info.value.phase == "mac-for-vm"


def test_wait_for_ip_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utm, "ip", lambda name, **_kwargs: None)
    times = iter([0.0, 0.0, 5.0])
    monkeypatch.setattr(utm.time, "monotonic", lambda: next(times, 999.0))
    monkeypatch.setattr(utm.time, "sleep", lambda _seconds: None)

    with pytest.raises(utm.UtmError) as exc_info:
        utm.wait_for_ip("dotfiles-utm", timeout=1.0)
    assert exc_info.value.phase == "wait-for-ip"


def test_wait_for_ip_returns_as_soon_as_ip_resolves(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utm, "ip", lambda name, **_kwargs: "192.168.64.5")
    assert utm.wait_for_ip("dotfiles-utm", timeout=5.0) == "192.168.64.5"


def test_utm_app_version_reads_info_plist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    info_plist = tmp_path / "Info.plist"
    info_plist.write_bytes(plistlib.dumps({"CFBundleShortVersionString": "4.6.5"}))
    monkeypatch.setattr(utm, "_UTM_APP_INFO_PLIST", str(info_plist))

    assert utm.utm_app_version() == "4.6.5"


def test_utm_app_version_returns_none_when_app_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(utm, "_UTM_APP_INFO_PLIST", str(tmp_path / "does-not-exist" / "Info.plist"))
    assert utm.utm_app_version() is None


def test_utm_app_version_never_invokes_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Never `utmctl version` -- unlike `--help` (pgrep-confirmed clean, tests/fixtures/utm/), that
    # subcommand was not captured the same way and the doctor row must never risk launching UTM.app.
    info_plist = tmp_path / "Info.plist"
    info_plist.write_bytes(plistlib.dumps({"CFBundleShortVersionString": "4.6.5"}))
    monkeypatch.setattr(utm, "_UTM_APP_INFO_PLIST", str(info_plist))

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("utm_app_version must never call subprocess")

    monkeypatch.setattr(utm.subprocess, "run", _forbidden)

    assert utm.utm_app_version() == "4.6.5"
