import json
from pathlib import Path

import pytest
from pytest_subprocess import FakeProcess

from macos_ci import doctor
from macos_ci._doctor_core import DoctorFacts

GOOD_FACTS = DoctorFacts(
    tool_versions={
        "tart": "2.32.1",
        "packer": "1.15.4",
        "just": "1.42.4",
        "uv": "0.11.14",
        "cirrus": "1.0.0-1769788",
        "sshpass": "1.10",
    },
    arch="arm64",
    macos_version="15.6.1",
    login_keychain_unlocked=True,
    zsh_dotfiles_path="/tmp/zsh-dotfiles",
    zsh_dotfiles_path_exists=True,
    free_disk_space_gb=200.0,
)


def _with(facts: DoctorFacts, **overrides):
    return facts.__class__(**{**facts.__dict__, **overrides})


def test_run_exits_0_when_everything_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor, "collect_facts", lambda: GOOD_FACTS)

    exit_code = doctor.run(json_output=True, run_id="test-run-good")

    assert exit_code == 0
    written = json.loads((tmp_path / "artifacts" / "test-run-good" / "doctor.json").read_text())
    assert all(row["ok"] for row in written if row["tool"] != "fleet-ceiling")


def test_run_exits_2_on_missing_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    bad_facts = _with(GOOD_FACTS, tool_versions={**GOOD_FACTS.tool_versions, "packer": None})
    monkeypatch.setattr(doctor, "collect_facts", lambda: bad_facts)

    exit_code = doctor.run(json_output=True, run_id="test-run-bad")

    assert exit_code == 2
    written = json.loads((tmp_path / "artifacts" / "test-run-bad" / "doctor.json").read_text())
    packer_row = next(r for r in written if r["tool"] == "packer")
    assert packer_row["ok"] is False
    assert packer_row["found"] is None


def test_run_writes_fleet_ceiling_report_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor, "collect_facts", lambda: GOOD_FACTS)

    doctor.run(json_output=True, run_id="test-run-ceiling")

    written = json.loads((tmp_path / "artifacts" / "test-run-ceiling" / "doctor.json").read_text())
    row = next(r for r in written if r["tool"] == "fleet-ceiling")
    assert "3 host" in row["found"]
    assert "100" in row["found"]
    assert row["ok"] is True


def test_tool_version_none_when_binary_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda tool: None)
    assert doctor._tool_version("packer") is None


def test_tool_version_parses_version_string(
    fake_process: FakeProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_process.register(["just", "--version"], stdout="just 1.42.4\n")
    monkeypatch.setattr(doctor.shutil, "which", lambda tool: "/opt/homebrew/bin/just")

    assert doctor._tool_version("just") == "1.42.4"


def test_tool_version_uses_sshpass_capital_v_not_double_dash_version(
    fake_process: FakeProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    # OQ-08: sshpass has no `--version` flag (it errors: "illegal option"); only `-V` reports the
    # version. `doctor.py::_tool_version()` must special-case it or `just doctor` reports sshpass
    # as missing even when it's installed.
    fake_process.register(["sshpass", "-V"], stdout="sshpass 1.10\n(C) 2006-2011 ...\n")
    monkeypatch.setattr(doctor.shutil, "which", lambda tool: "/opt/homebrew/bin/sshpass")

    assert doctor._tool_version("sshpass") == "1.10"
