"""The assertion layer (spec 08 §(c)): what "the dotfiles installed correctly" decomposes into,
reused from `smoke-test-docker.sh` rather than reinvented (spec 09 §"Assertion vocabulary already
in use upstream"). All of these run against an already-applied VM -- `just up` + `just apply` (or
`just run`) must have completed first; this tier never boots or applies anything itself.
"""

from __future__ import annotations

import json
import re

import pytest
from testinfra.host import Host

# The `tart --dir` mount point (spec 01 §"Shared directories"). Duplicated from
# `harness.py`'s `_MOUNT_POINT` rather than imported -- same reasoning as
# `tests/integration/conftest.py`'s duplicated key path: `tests/` isn't a package.
_MOUNT_POINT = "/Volumes/My Shared Files/dotfiles"

# `.chezmoiscripts/` entries that are NOT `run_once_`/`run_onchange_`-prefixed, so chezmoi lists
# them in every `diff`/`apply` regardless of whether they'd actually change anything (they're
# internally idempotent via `|| true`). Confirmed against the real `zsh-dotfiles` source tree
# (OQ-09, validator). Any OTHER path appearing in the diff is a genuine pending change.
_EXPECTED_ALWAYS_CHANGING_SCRIPTS = frozenset(
    {
        ".chezmoiscripts/after-00-adhoc-macos.sh",
        ".chezmoiscripts/50-mise-install-tools.sh",
    }
)


def _diff_blocks(diff_text: str) -> list[str]:
    """Split unified `git diff`-style output into per-file blocks."""
    if not diff_text.strip():
        return []
    return [
        block
        for block in re.split(r"(?=^diff --git )", diff_text, flags=re.MULTILINE)
        if block.strip()
    ]


def _diff_target_path(block: str) -> str:
    """Extract the `b/<path>` target from a block's `diff --git a/<path> b/<path>` header."""
    match = re.match(r"diff --git a/\S+ b/(?P<target>\S+)", block)
    if match is None:
        raise ValueError(f"not a well-formed git-diff block: {block[:80]!r}")
    return match.group("target")


@pytest.mark.vm
def test_apply_is_idempotent_no_pending_diff(vm: Host) -> None:
    # smoke-test-docker.sh:361-373's exit-0 check, restated post-hoc. `chezmoi verify` cannot be
    # used here -- see 09 §"Pre-apply template validation" -- but `chezmoi diff` is also the
    # correct read-only re-check post-apply. Must pass the SAME --source as the real apply used
    # (OQ-08, found live): chezmoi's persistent state keys entries by source path, so a bare
    # `chezmoi diff` (implicitly `~/.local/share/chezmoi`) diffs a DIFFERENT identity even after
    # the symlink fix.
    #
    # OQ-09 (validator red-team): a bare `stdout == ""` assertion can never pass -- this dotfiles
    # repo ships two always-run `.chezmoiscripts/` entries (`_EXPECTED_ALWAYS_CHANGING_SCRIPTS`)
    # that chezmoi lists in every diff regardless of outcome. Rather than drop stdout inspection
    # entirely, filter those two known blocks out and assert the REMAINDER is empty, so a genuine
    # future content regression still fails this test.
    result = vm.run(f"chezmoi diff --source={_MOUNT_POINT!r}")
    assert result.rc == 0
    assert result.stderr.strip() == ""

    unexpected = [
        block
        for block in _diff_blocks(result.stdout)
        if _diff_target_path(block) not in _EXPECTED_ALWAYS_CHANGING_SCRIPTS
    ]
    assert not unexpected, f"unexpected pending diff after apply: {unexpected}"


@pytest.mark.vm
def test_post_install_hook_succeeds(vm: Host) -> None:
    # smoke-test-docker.sh:376-385, wrapped in retry -t 4 (network-flaky Sheldon/brew fetches).
    result = vm.run("retry -t 4 -- post-install-chezmoi")
    assert result.rc == 0


@pytest.mark.vm
def test_zsh_loads_and_sets_a_prompt(vm: Host) -> None:
    # smoke-test-docker.sh:388-404's canonical "did this actually work" probe, verbatim including
    # its `timeout 10s` wrapper. OQ-09 (validator red-team of OQ-08): `timeout` IS present on this
    # host -- `post-install-chezmoi` (run by `test_post_install_hook_succeeds`, which executes
    # before this test in file order) installs GNU coreutils, which provides
    # `/opt/homebrew/bin/timeout`. The earlier "macOS ships no GNU timeout" classification was
    # wrong: the real original failure was the same PATH gap fixed elsewhere in OQ-08 (a
    # non-interactive SSH session couldn't reach /opt/homebrew/bin at all), not a missing binary.
    # `timeout 10s` is the correct per-command hang backstop -- SSH's ServerAliveInterval (also
    # added per OQ-09) only detects a dead *connection*, not a remote command that hangs while the
    # connection stays healthy (e.g. blocked on a read).
    result = vm.run(
        "timeout 10s zsh -c 'source ~/.zshrc; "
        '[[ -n "$ZSH_VERSION" ]] && echo zsh_ok; '
        '[[ -n "$PROMPT" || -n "$PS1" ]] && echo prompt_ok\''
    )
    assert result.rc == 0
    assert "zsh_ok" in result.stdout
    assert "prompt_ok" in result.stdout


@pytest.mark.vm
def test_login_shell_is_zsh(vm: Host) -> None:
    # macOS-specific -- Linux upstream has no equivalent (spec 08 §(c)).
    result = vm.run("dscl . -read /Users/admin UserShell")
    assert result.rc == 0
    assert "/bin/zsh" in result.stdout


@pytest.mark.vm
def test_sheldon_plugin_sources_resolve(vm: Host) -> None:
    # Mutating, deliberately -- OQ-17, ANSWERED (spec 08 §(c)): the disposable clone this test
    # runs against is destroyed right after, so mutating it costs nothing and tests strictly more
    # than a hypothetical read-only verb would.
    result = vm.run("sheldon lock")
    assert result.rc == 0


@pytest.mark.vm
def test_nvim_headless_sanity(vm: Host) -> None:
    result = vm.run("nvim --headless '+qa'")
    assert result.rc == 0


@pytest.mark.vm
def test_tmux_present(vm: Host) -> None:
    result = vm.run("tmux -V")
    assert result.rc == 0
    assert "tmux" in result.stdout.lower()


@pytest.mark.vm
def test_version_manager_shims_precede_system_path(vm: Host) -> None:
    # spec 09 §"The version_manager selector": mutual exclusion between asdf/mise on PATH,
    # derived from smoke-test-docker.sh:222-283's setup_version_manager.
    # `version_manager` is top-level in `chezmoi data`'s output, not nested under a
    # "zsh_dotfiles" key (found live, OQ-08 -- verified via a real `chezmoi data` dump).
    data = json.loads(vm.run("chezmoi data").stdout)
    manager = data["version_manager"]
    path_result = vm.run("zsh -lc 'echo $PATH'")
    assert path_result.rc == 0

    if manager == "mise":
        assert "/.asdf/shims/" not in path_result.stdout
        which_node = vm.run("zsh -lc 'which node'")
        assert "/.asdf/shims/" not in which_node.stdout
    elif manager == "asdf":
        assert ".asdf/shims" in path_result.stdout
    else:
        pytest.fail(f"unexpected version_manager {manager!r}")


@pytest.mark.vm
def test_homebrew_health_is_non_fatal(vm: Host) -> None:
    # smoke-test-docker.sh:332-338: brew doctor warnings are logged, never fail the stage.
    result = vm.run("brew doctor")
    assert result.rc in (
        0,
        1,
    )  # brew doctor exits non-zero on warnings; never treated as fatal here


@pytest.mark.vm
def test_lean_baseline_feature_toggles_are_all_false(vm: Host) -> None:
    # spec 09 §"Non-TTY default state": a baseline non-TTY run never fires the seven promptBools.
    data = json.loads(vm.run("chezmoi data").stdout)
    for field in ("ruby", "pyenv", "nodejs", "k8s", "cuda", "fnm", "opencv"):
        assert data.get(field) is False, f"{field} should default false on a lean baseline run"


# --- Hermetic coverage for the diff-filtering helpers (OQ-09) -- no VM needed, runs by default. ---

_SAMPLE_DIFF = """diff --git a/.chezmoiscripts/after-00-adhoc-macos.sh b/.chezmoiscripts/after-00-adhoc-macos.sh
new file mode 100755
index 0000000000000000000000000000000000000000..f6d58bc3b3e21553ce342a813fa98f44eaed32a8
--- /dev/null
+++ b/.chezmoiscripts/after-00-adhoc-macos.sh
@@ -0,0 +1,3 @@
+#!/usr/bin/env zsh
+mkdir -p $HOME/.zsh/completion || true
+fpath+="$HOME/.zsh/completion"
diff --git a/.chezmoiscripts/50-mise-install-tools.sh b/.chezmoiscripts/50-mise-install-tools.sh
new file mode 100755
index 0000000000000000000000000000000000000000..d71f1719b8a5f97fc7ceaa523a0f7e7afb13e69f
--- /dev/null
+++ b/.chezmoiscripts/50-mise-install-tools.sh
@@ -0,0 +1,2 @@
+#!/bin/bash
+mise use -g golang@1.25.1 || true
"""


def test_diff_blocks_splits_on_each_git_diff_header() -> None:
    blocks = _diff_blocks(_SAMPLE_DIFF)
    assert len(blocks) == 2
    assert blocks[0].startswith("diff --git a/.chezmoiscripts/after-00-adhoc-macos.sh")
    assert blocks[1].startswith("diff --git a/.chezmoiscripts/50-mise-install-tools.sh")


def test_diff_blocks_returns_empty_list_for_blank_diff() -> None:
    assert _diff_blocks("") == []
    assert _diff_blocks("   \n") == []


def test_diff_target_path_extracts_the_b_side() -> None:
    block = "diff --git a/home/.zshrc b/home/.zshrc\n--- a/home/.zshrc\n+++ b/home/.zshrc\n"
    assert _diff_target_path(block) == "home/.zshrc"


def test_expected_always_changing_scripts_filters_the_known_two_but_not_a_third() -> None:
    blocks = _diff_blocks(_SAMPLE_DIFF)
    unexpected = [
        b for b in blocks if _diff_target_path(b) not in _EXPECTED_ALWAYS_CHANGING_SCRIPTS
    ]
    assert unexpected == []

    regressed = _SAMPLE_DIFF + (
        "diff --git a/home/.zshrc b/home/.zshrc\n--- a/home/.zshrc\n+++ b/home/.zshrc\n"
        "@@ -1 +1 @@\n-old\n+new\n"
    )
    unexpected = [
        b
        for b in _diff_blocks(regressed)
        if _diff_target_path(b) not in _EXPECTED_ALWAYS_CHANGING_SCRIPTS
    ]
    assert len(unexpected) == 1
    assert _diff_target_path(unexpected[0]) == "home/.zshrc"
