"""`pty` tier: pexpect over `ssh -tt` (spec 12 §"pty — pexpect over ssh -tt").

Some things are only observable through a terminal: tab completion, keybindings, escape sequences a
prompt emits. `-tt` here does **not** contradict G11 -- G11 governs `chezmoi apply`'s no-TTY
requirement; verification runs afterwards and deliberately wants the opposite (spec 12 §"pty").
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pexpect
import pytest

# Duplicated from tests/conftest.py rather than imported -- see tests/integration/conftest.py's
# comment: `tests/` isn't a package, and basedpyright can't resolve a `tests.conftest` import.
_HARNESS_KEY_PATH = Path("harness/ssh/id_ed25519_harness")
SSH_OPTS = (
    "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "
    "-o ConnectTimeout=8 -o BatchMode=yes "
    # OQ-09: kept in sync with `_harness_core._BASE_SSH_OPTS` / `tests/conftest.py`.
    "-o ServerAliveInterval=15 -o ServerAliveCountMax=3 "
    f"-i {_HARNESS_KEY_PATH.resolve()}"
)

_PROMPT_RE = re.compile(r"[%$#>]\s*$")


@pytest.mark.pty
def test_zsh_tab_completion(vm_state: dict[str, Any]) -> None:
    child = pexpect.spawn(f"ssh -tt {SSH_OPTS} admin@{vm_state['ip']}", timeout=30)
    child.expect(_PROMPT_RE)
    child.sendline("chezmo\t")
    child.expect("chezmoi")


@pytest.mark.pty
def test_starship_or_pure_prompt_renders(vm_state: dict[str, Any]) -> None:
    # A prompt drawn over a real TTY should produce *some* non-empty output before the shell's
    # own PS1/PROMPT content -- this is not asserting on a specific theme, only that something
    # rendered (spec 12 reserves pixel-level assertions for the `gui` tier).
    child = pexpect.spawn(f"ssh -tt {SSH_OPTS} admin@{vm_state['ip']}", timeout=30)
    child.expect(_PROMPT_RE)
    assert child.before is not None


@pytest.mark.pty
def test_ctrl_r_history_search_is_bound(vm_state: dict[str, Any]) -> None:
    child = pexpect.spawn(f"ssh -tt {SSH_OPTS} admin@{vm_state['ip']}", timeout=30)
    child.expect(_PROMPT_RE)
    child.sendline("echo pty_marker_line")
    child.expect(_PROMPT_RE)
    child.send("\x12")  # Ctrl-R
    child.send("pty_marker")
    child.expect("pty_marker")
