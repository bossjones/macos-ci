from dataclasses import replace

from macos_ci._doctor_core import DoctorFacts, check, overall_ok, version_at_least

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
    zsh_dotfiles_path="/Users/bossjones/dev/bossjones/zsh-dotfiles",
    zsh_dotfiles_path_exists=True,
    free_disk_space_gb=120.0,
)


def _row(results, tool):
    return next(r for r in results if r.tool == tool)


def test_check_all_present_is_ok():
    results = check(GOOD_FACTS)
    assert overall_ok(results) is True
    assert all(r.ok for r in results if r.tool != "fleet-ceiling")


def test_check_reports_missing_packer():
    facts = replace(GOOD_FACTS, tool_versions={**GOOD_FACTS.tool_versions, "packer": None})
    results = check(facts)
    row = _row(results, "packer")
    assert row.found is None
    assert row.ok is False
    assert overall_ok(results) is False


def test_check_reports_version_below_minimum():
    facts = replace(GOOD_FACTS, tool_versions={**GOOD_FACTS.tool_versions, "tart": "1.0.0"})
    results = check(facts)
    row = _row(results, "tart")
    assert row.found == "1.0.0"
    assert row.ok is False


def test_check_fails_on_non_apple_silicon():
    facts = replace(GOOD_FACTS, arch="x86_64")
    results = check(facts)
    row = _row(results, "apple-silicon")
    assert row.ok is False


def test_check_fails_on_locked_login_keychain():
    facts = replace(GOOD_FACTS, login_keychain_unlocked=False)
    results = check(facts)
    row = _row(results, "login-keychain-unlocked")
    assert row.ok is False


def test_check_fails_when_zsh_dotfiles_missing():
    facts = replace(GOOD_FACTS, zsh_dotfiles_path_exists=False)
    results = check(facts)
    row = _row(results, "ZSH_DOTFILES")
    assert row.ok is False


def test_check_fails_on_low_disk_space():
    facts = replace(GOOD_FACTS, free_disk_space_gb=1.0)
    results = check(facts)
    row = _row(results, "free-disk-space")
    assert row.ok is False


def test_check_always_reports_fleet_ceiling_never_gates_it():
    results = check(GOOD_FACTS)
    row = _row(results, "fleet-ceiling")
    assert "3 host" in row.found
    assert "100" in row.found
    assert row.ok is True  # report-only: never silently approved as a pass/fail gate


def test_version_at_least_treats_a_short_form_as_equal_when_numerically_equal():
    # OQ-01: tuple comparison without zero-padding treats a shorter tuple that is a prefix of a
    # longer one as *less than* it, so "2.0" spuriously failed against a "2.0.0" minimum.
    assert version_at_least("2.0", "2.0.0") is True


def test_version_at_least_still_rejects_a_genuinely_lower_short_form():
    assert version_at_least("1.9", "2.0.0") is False


def test_version_at_least_baseline_equal_length_still_passes():
    assert version_at_least("2.0.0", "2.0.0") is True


def test_check_requires_sshpass_for_the_ssh_bootstrap_phase():
    # OQ-08: `just up` needs sshpass on the HOST for OQ-05's password-authenticated bootstrap
    # connection (_harness_core.bootstrap_ssh_argv). Its absence blocked a real run entirely and
    # was only caught mid-`up`, not by `just doctor` -- `just doctor` must catch it first.
    facts = replace(GOOD_FACTS, tool_versions={**GOOD_FACTS.tool_versions, "sshpass": None})
    results = check(facts)
    row = _row(results, "sshpass")
    assert row.found is None
    assert row.ok is False
    assert overall_ok(results) is False


def test_check_passes_when_sshpass_is_present():
    facts = replace(GOOD_FACTS, tool_versions={**GOOD_FACTS.tool_versions, "sshpass": "1.10"})
    row = _row(check(facts), "sshpass")
    assert row.ok is True
