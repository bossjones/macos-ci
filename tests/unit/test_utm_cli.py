"""Typer wiring for the UTM lane (`specs/utm-improvements.md` step 5): `cli.py` mounts `utm.app`,
and its commands wrap the `utm.py` shell functions. `CliRunner` + monkeypatch -- no real
`utmctl`/`tart`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from macos_ci import utm
from macos_ci._utm_core import UtmVm
from macos_ci.cli import app as cli_app

runner = CliRunner()


def test_cli_mounts_utm_subapp() -> None:
    result = runner.invoke(cli_app, ["utm", "--help"])
    assert result.exit_code == 0
    assert "bootstrap-dotfiles" in result.output


def test_utm_bootstrap_dotfiles_prints_mount_and_apply() -> None:
    result = runner.invoke(utm.app, ["bootstrap-dotfiles"])
    assert result.exit_code == 0
    assert "mount_virtiofs" in result.output
    assert "chezmoi" in result.output


def test_utm_up_impl_clones_when_missing_and_writes_lane_utm_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    calls: dict[str, Any] = {}
    monkeypatch.setattr(utm, "list_vms", lambda: [])
    monkeypatch.setattr(
        utm, "clone", lambda source, *, name=None: calls.setdefault("clone", (source, name))
    )
    monkeypatch.setattr(utm, "start", lambda name, **_kw: calls.setdefault("start", name))
    monkeypatch.setattr(utm, "wait_for_ip", lambda name, **_kw: "192.168.64.9")
    monkeypatch.setattr(
        utm, "_bootstrap_key_trust", lambda ip_addr: calls.setdefault("key_trust", ip_addr)
    )
    monkeypatch.setattr(
        utm, "_wait_for_ssh", lambda ip_addr, **_kw: calls.setdefault("wait_ssh", ip_addr)
    )

    state = utm.up_impl(vm="dotfiles-utm", golden="dotfiles-golden-utm")

    assert calls["clone"] == ("dotfiles-golden-utm", "dotfiles-utm")
    assert calls["start"] == "dotfiles-utm"
    assert calls["key_trust"] == "192.168.64.9"
    assert calls["wait_ssh"] == "192.168.64.9"
    assert state["vm"] == "dotfiles-utm"
    assert state["ip"] == "192.168.64.9"
    assert state["lane"] == "utm"
    written = json.loads((tmp_path / "artifacts" / state["run_id"] / "state.json").read_text())
    assert written["lane"] == "utm"


def test_utm_up_impl_skips_clone_when_vm_already_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        utm, "list_vms", lambda: [UtmVm(uuid="x", status="stopped", name="dotfiles-utm")]
    )
    cloned = {"called": False}
    monkeypatch.setattr(utm, "clone", lambda *_a, **_kw: cloned.__setitem__("called", True))
    monkeypatch.setattr(utm, "start", lambda name, **_kw: None)
    monkeypatch.setattr(utm, "wait_for_ip", lambda name, **_kw: "192.168.64.9")
    monkeypatch.setattr(utm, "_bootstrap_key_trust", lambda ip_addr: None)
    monkeypatch.setattr(utm, "_wait_for_ssh", lambda ip_addr, **_kw: None)

    utm.up_impl(vm="dotfiles-utm", golden="dotfiles-golden-utm")

    assert cloned["called"] is False


def test_utm_doctor_impl_reports_three_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(utm, "utm_app_version", lambda: "4.6.5")
    monkeypatch.setenv("MACOS_CI_UTM_DIR", str(tmp_path))
    bundle = tmp_path / "dotfiles-golden-utm.utm"
    bundle.mkdir()
    (bundle / "config.plist").write_bytes(b"")
    leases = tmp_path / "dhcpd_leases"
    leases.write_text("")

    rows = utm.doctor_impl(golden="dotfiles-golden-utm", leases_path=str(leases))

    by_tool = {row["tool"]: row for row in rows}
    assert set(by_tool) == {"utm", "utm-golden-bundle", "dhcpd-leases-readable"}
    assert by_tool["utm"]["ok"] is True
    assert by_tool["utm-golden-bundle"]["ok"] is True
    assert by_tool["dhcpd-leases-readable"]["ok"] is True


def test_utm_doctor_impl_reports_missing_golden_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(utm, "utm_app_version", lambda: None)
    monkeypatch.setenv("MACOS_CI_UTM_DIR", str(tmp_path))
    leases = tmp_path / "dhcpd_leases"
    leases.write_text("")

    rows = utm.doctor_impl(golden="dotfiles-golden-utm", leases_path=str(leases))

    by_tool = {row["tool"]: row for row in rows}
    assert by_tool["utm"]["ok"] is False
    assert by_tool["utm-golden-bundle"]["ok"] is False


def test_utm_doctor_never_fails_when_utm_missing_matches_optional_row_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # doctor_impl itself may report ok=False rows (used by `macos-ci utm doctor`'s own exit code);
    # the *main* `macos-ci doctor`'s optional row (step 6) is what must never fail overall_ok --
    # this only pins doctor_impl's row shape, which that row is built from.
    monkeypatch.setattr(utm, "utm_app_version", lambda: None)
    monkeypatch.setenv("MACOS_CI_UTM_DIR", str(tmp_path))
    leases = tmp_path / "dhcpd_leases"
    leases.write_text("")
    rows = utm.doctor_impl(golden="dotfiles-golden-utm", leases_path=str(leases))
    assert all("tool" in row and "found" in row and "ok" in row for row in rows)


def test_import_golden_impl_clones_scratch_and_stages_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv_calls: list[list[str]] = []

    class _FakeResult:
        returncode = 0

    def _fake_run(argv: list[str], **_kwargs: object) -> _FakeResult:
        argv_calls.append(argv)
        return _FakeResult()

    copy_calls: list[tuple[Path, Path]] = []

    monkeypatch.setattr(utm.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        utm.shutil, "copy2", lambda src, dst: copy_calls.append((Path(src), Path(dst)))
    )

    dest = utm.import_golden_impl(
        tart_vm="dotfiles-golden",
        scratch_vm="utm-export-scratch",
        dest_dir=tmp_path / "stage",
    )

    assert argv_calls[0] == ["tart", "clone", "dotfiles-golden", "utm-export-scratch"]
    assert argv_calls[-1] == ["tart", "delete", "utm-export-scratch"]
    assert dest == tmp_path / "stage" / "disk.img"
    assert copy_calls[0][1] == dest
