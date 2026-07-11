from macos_ci._triage_core import Finding, match

# Seed failure signatures, verbatim from spec 12 §"Seed failure signatures".


def test_match_finds_nothing_in_a_clean_log() -> None:
    assert match(["Booting...", "chezmoi apply: OK", "all tests passed"]) == []


def test_match_tart_ip_never_returns() -> None:
    findings = match(
        [
            "tart run dotfiles-test-abc123 --no-graphics &",
            "ERROR: tart ip dotfiles-test-abc123 timed out after 120s waiting for an address",
        ]
    )
    assert any(f.signature == "tart-ip-never-returns" for f in findings)
    assert "DHCP" in _cause_for(findings, "tart-ip-never-returns")


def test_match_clt_gui_prompt_fired_non_interactively() -> None:
    findings = match(["xcode-select: note: install requested for command line developer tools"])
    assert len(findings) == 1
    finding = findings[0]
    assert finding.signature == "clt-gui-prompt-non-interactive"
    assert "softwareupdate" in finding.cause
    assert isinstance(finding, Finding)


def test_match_rosetta_homebrew_path_mismatch_literal() -> None:
    findings = match(["Cannot install under Rosetta 2 on Apple Silicon"])
    assert any(f.signature == "rosetta-homebrew-path-mismatch" for f in findings)


def test_match_rosetta_homebrew_path_mismatch_prefix() -> None:
    findings = match(["==> /usr/local/bin/brew doctor", "Warning: /usr/local is not writable"])
    assert any(f.signature == "rosetta-homebrew-path-mismatch" for f in findings)


def test_match_locked_login_keychain() -> None:
    findings = match(
        [
            "Headless boot failed",
            "The specified item could not be found in the keychain",
        ]
    )
    assert any(f.signature == "login-keychain-locked" for f in findings)
    assert "G8" in _cause_for(findings, "login-keychain-locked")


def test_match_chezmoi_template_render_error() -> None:
    findings = match(
        [
            "chezmoi: template: .chezmoiscripts/run_once_before_install.sh.tmpl:12:3: "
            "executing at <.Foo>: nil pointer evaluating interface {}.Foo"
        ]
    )
    assert any(f.signature == "chezmoi-template-render-error" for f in findings)


def test_match_asdf_shims_precede_mise() -> None:
    findings = match(["/Users/admin/.asdf/shims/node"])
    assert any(f.signature == "asdf-shims-precede-mise" for f in findings)


def test_match_reports_line_number_and_text() -> None:
    findings = match(["line one", "xcode-select: note: install requested"])
    finding = next(f for f in findings if f.signature == "clt-gui-prompt-non-interactive")
    assert finding.line_number == 2
    assert finding.line == "xcode-select: note: install requested"


def test_match_finds_multiple_signatures_in_one_log() -> None:
    findings = match(
        [
            "The specified item could not be found in the keychain",
            "xcode-select: note: install requested",
        ]
    )
    signatures = {f.signature for f in findings}
    assert signatures == {"login-keychain-locked", "clt-gui-prompt-non-interactive"}


def _cause_for(findings: list[Finding], signature: str) -> str:
    return next(f.cause for f in findings if f.signature == signature)
