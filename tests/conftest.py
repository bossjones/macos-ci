"""Shared fixtures across the `vm`/`pty`/`gui` tiers: reading `artifacts/latest/state.json` and
the harness's throwaway SSH key path (OQ-05, `harness/ssh/`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

HARNESS_KEY_PATH = Path("harness/ssh/id_ed25519_harness")
SSH_OPTS = (
    "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "
    "-o ConnectTimeout=8 -o BatchMode=yes "
    # OQ-09: detects a connection that goes dead after the handshake (host sleep, network drop) --
    # ConnectTimeout alone only bounds the handshake itself. Kept in sync with
    # `_harness_core._BASE_SSH_OPTS`.
    "-o ServerAliveInterval=15 -o ServerAliveCountMax=3 "
    f"-i {HARNESS_KEY_PATH.resolve()}"
)


@pytest.fixture(scope="session")
def vm_state() -> dict[str, Any]:
    state_path = Path("artifacts/latest/state.json")
    if not state_path.exists():
        pytest.skip("no artifacts/latest/state.json -- run `just up` first")
    data: dict[str, Any] = json.loads(state_path.read_text())
    return data
