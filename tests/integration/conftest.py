"""Session-scoped testinfra host fixture for the `-m vm` tier (spec 12 §"vm — pytest-testinfra
over SSH"). Shape follows `multipass-lab/clusters/*/tests/testinfra/conftest.py`.

Connects with the harness's throwaway keypair (OQ-05, `harness/ssh/`) -- the golden image only
configures password auth, so `harness.py up` bootstraps key trust once per clone before this fixture
ever runs. `just verify` assumes `just up` already happened; it does not boot a VM itself.

`vm_state` is shared across the vm/pty/gui tiers -- see `tests/conftest.py`.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest
import testinfra

# Duplicated from tests/conftest.py rather than imported: `tests/` isn't a package (no
# __init__.py, deliberately -- pytest's rootdir-prepend import mode already makes every
# conftest.py's fixtures cascade down without imports), and basedpyright can't resolve a
# `tests.conftest` import under that layout.
_KEY_PATH = Path("harness/ssh/id_ed25519_harness")
_CONNECT_TIMEOUT = 180  # spec 12's given fixture uses 180s


@pytest.fixture(scope="session")
def ssh_config_file(tmp_path_factory: pytest.TempPathFactory) -> str:
    cfg = tmp_path_factory.mktemp("ssh") / "config"
    cfg.write_text(
        "Host *\n"
        "  StrictHostKeyChecking no\n"
        "  UserKnownHostsFile /dev/null\n"
        "  LogLevel ERROR\n"
        "  ConnectTimeout 8\n"
        "  BatchMode yes\n"
        # OQ-09: detects a connection that goes dead post-handshake; not a substitute for a
        # per-command timeout on the remote side. Kept in sync with `_harness_core._BASE_SSH_OPTS`.
        "  ServerAliveInterval 15\n"
        "  ServerAliveCountMax 3\n"
        f"  IdentityFile {_KEY_PATH.resolve()}\n"
        "  User admin\n"
    )
    return str(cfg)


@pytest.fixture(scope="session")
def vm(vm_state: dict[str, Any], ssh_config_file: str):
    host = testinfra.get_host(f"ssh://admin@{vm_state['ip']}", ssh_config=ssh_config_file)
    deadline = time.monotonic() + _CONNECT_TIMEOUT
    while True:
        try:
            if host.run("true").rc == 0:
                return host
        except Exception:  # noqa: BLE001 - retry until reachable or timeout
            pass
        if time.monotonic() >= deadline:
            raise TimeoutError(f"VM {vm_state['ip']} not SSH-reachable after {_CONNECT_TIMEOUT}s")
        time.sleep(3)
