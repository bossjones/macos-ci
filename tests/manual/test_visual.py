"""`manual` tier (spec 12 §"manual — the human tier"): real test functions, so verdicts land in
the same JSON report as everything else. Every test here must go through the `confirm()` fixture --
never a bare `input()` -- so a non-interactive run degrades to a skip instead of hanging.

Assumes `just gui` (or `just up` followed by opening the VM's window by hand) already gave the
human something to look at; this tier only asks about what's on screen, it does not open windows
itself -- that's `gui.py`'s automation surface (🐍's file), not this test file's job.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest


@pytest.mark.manual
def test_prompt_renders_with_glyphs(
    vm_state: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On VM {vm_state.get('vm', '?')}: does the terminal prompt show a git branch glyph "
        "and no tofu/replacement-character boxes?"
    )


@pytest.mark.manual
def test_colorscheme_looks_correct(
    vm_state: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On VM {vm_state.get('vm', '?')}: does the terminal colorscheme look right "
        "(no washed-out or inverted colors)?"
    )
