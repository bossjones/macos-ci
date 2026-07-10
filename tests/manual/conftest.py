"""The `manual` tier's `confirm()` fixture (spec 12 §"manual — the human tier"): `pytest.skip()`s
when there's no TTY to prompt on, so even an explicit `-m manual` degrades to skips in a
non-interactive context rather than hanging an agent.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

import pytest


@pytest.fixture
def confirm() -> Callable[[str], bool]:
    def _confirm(question: str) -> bool:
        if not sys.stdin.isatty():
            pytest.skip(f"not a TTY -- cannot ask: {question!r}")
        answer = input(f"{question} [y/N] ").strip().lower()
        return answer in ("y", "yes")

    return _confirm
