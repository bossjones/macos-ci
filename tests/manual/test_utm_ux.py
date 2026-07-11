"""`manual` tier for the UTM lane (spec 12 §"manual -- the human tier";
`specs/utm-improvements.md` step 8): the recorded iTerm2 UX checklist. Every test goes through the
`confirm()` fixture -- never a bare `input()` -- so a non-interactive run degrades to a skip
instead of hanging.

Assumes `just utm-up` already booted a windowed UTM clone and the human has pasted
`just utm-bootstrap-dotfiles`'s block into the guest's iTerm2; this tier only asks about what's on
screen, it does not drive the apply itself -- that's the human's job (spec: "the human drives the
dotfiles").
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture
def utm_session(vm_state: dict[str, Any]) -> dict[str, Any]:
    """Skips unless the latest run was the UTM lane -- a tart-lane `state.json` (or none at all)
    means there is no UTM window to look at.
    """
    if vm_state.get("lane") != "utm":
        pytest.skip("no UTM session in artifacts/latest/state.json -- run `just utm-up` first")
    return vm_state


@pytest.mark.manual
def test_iterm2_prompt_renders_with_glyphs(
    utm_session: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: does the prompt show a git branch "
        "glyph and no tofu/replacement-character boxes?"
    )


@pytest.mark.manual
def test_sheldon_plugins_active(
    utm_session: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: typing a command shows syntax "
        "highlighting and ghost-text autosuggestion (sheldon plugins active)?"
    )


@pytest.mark.manual
def test_keybindings_history_search(
    utm_session: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: does Ctrl-R open the configured "
        "history search?"
    )


@pytest.mark.manual
def test_tab_completion_menu_renders(
    utm_session: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: does Tab draw a navigable completion "
        "menu (not a flat list dump)?"
    )


@pytest.mark.manual
def test_colorscheme_and_profile(
    utm_session: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: do colors look correct (not washed "
        "out or inverted), and does a 24-bit color test strip render smooth?"
    )


@pytest.mark.manual
def test_no_first_run_warnings(utm_session: dict[str, Any], confirm: Callable[[str], bool]) -> None:
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: opening a new shell shows no "
        "compaudit/'insecure directories'/command-not-found noise?"
    )


@pytest.mark.manual
def test_keyboard_input_fidelity(
    utm_session: dict[str, Any], confirm: Callable[[str], bool]
) -> None:
    # A GUI-only signal -- SSH's steady-state, non-interactive transport (G11) never exercises
    # Option/arrow word-motion the way a real keyboard in the UTM window does.
    assert confirm(
        f"On UTM VM {utm_session.get('vm', '?')}'s iTerm2: does Option+Left/Right move by word "
        "in the shell, and do arrow keys navigate history/cursor correctly?"
    )
