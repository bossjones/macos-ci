from macos_ci._doctor_core import DoctorFacts, check, overall_ok

GOOD_FACTS = DoctorFacts(
    tool_versions={
        "tart": "2.32.1",
        "packer": "1.15.4",
        "just": "1.42.4",
        "uv": "0.11.14",
        "cirrus": "1.0.0-1769788",
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
    facts = GOOD_FACTS.__class__(
        **{**GOOD_FACTS.__dict__, "tool_versions": {**GOOD_FACTS.tool_versions, "packer": None}}
    )
    results = check(facts)
    row = _row(results, "packer")
    assert row.found is None
    assert row.ok is False
    assert overall_ok(results) is False


def test_check_reports_version_below_minimum():
    facts = GOOD_FACTS.__class__(
        **{**GOOD_FACTS.__dict__, "tool_versions": {**GOOD_FACTS.tool_versions, "tart": "1.0.0"}}
    )
    results = check(facts)
    row = _row(results, "tart")
    assert row.found == "1.0.0"
    assert row.ok is False


def test_check_fails_on_non_apple_silicon():
    facts = GOOD_FACTS.__class__(**{**GOOD_FACTS.__dict__, "arch": "x86_64"})
    results = check(facts)
    row = _row(results, "apple-silicon")
    assert row.ok is False


def test_check_fails_on_locked_login_keychain():
    facts = GOOD_FACTS.__class__(**{**GOOD_FACTS.__dict__, "login_keychain_unlocked": False})
    results = check(facts)
    row = _row(results, "login-keychain-unlocked")
    assert row.ok is False


def test_check_fails_when_zsh_dotfiles_missing():
    facts = GOOD_FACTS.__class__(**{**GOOD_FACTS.__dict__, "zsh_dotfiles_path_exists": False})
    results = check(facts)
    row = _row(results, "ZSH_DOTFILES")
    assert row.ok is False


def test_check_fails_on_low_disk_space():
    facts = GOOD_FACTS.__class__(**{**GOOD_FACTS.__dict__, "free_disk_space_gb": 1.0})
    results = check(facts)
    row = _row(results, "free-disk-space")
    assert row.ok is False


def test_check_always_reports_fleet_ceiling_never_gates_it():
    results = check(GOOD_FACTS)
    row = _row(results, "fleet-ceiling")
    assert "3 host" in row.found
    assert "100" in row.found
    assert row.ok is True  # report-only: never silently approved as a pass/fail gate
