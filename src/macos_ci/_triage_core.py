"""Pure failure-signature matching over macOS/tart log text (spec 12 §"Seed failure signatures").

Stdlib-only. `vm_debug.py` sweeps the guest's log sources over `ssh` and hands the resulting
lines to `match()` here -- no subprocess, socket, or filesystem access happens in this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Signature:
    name: str
    pattern: re.Pattern[str]
    cause: str


@dataclass(frozen=True)
class Finding:
    signature: str
    cause: str
    line: str
    line_number: int


# Seed table, spec 12 §"Seed failure signatures" -- grown from real Phase-1 failures, not invented.
SIGNATURES: tuple[Signature, ...] = (
    Signature(
        name="tart-ip-never-returns",
        pattern=re.compile(r"tart ip .*(timed out|timeout|never returns)", re.IGNORECASE),
        cause="Guest never got DHCP. Check the softnet/bridged networking mode.",
    ),
    Signature(
        name="clt-gui-prompt-non-interactive",
        pattern=re.compile(r"xcode-select: note: install requested"),
        cause=(
            "The CLT GUI prompt fired inside a non-TTY run. The golden image must install CLT "
            "non-interactively via `softwareupdate --install <label>`."
        ),
    ),
    Signature(
        name="rosetta-homebrew-path-mismatch",
        pattern=re.compile(
            r"Cannot install under Rosetta 2|/usr/local(/bin/brew|/Cellar| is not writable)"
        ),
        cause="Architecture mismatch. The VM is arm64; Homebrew must live at /opt/homebrew.",
    ),
    Signature(
        name="login-keychain-locked",
        pattern=re.compile(r"The specified item could not be found in the keychain"),
        cause="The login keychain is locked. This is G8 -- see 01-tart-core.md.",
    ),
    Signature(
        name="chezmoi-template-render-error",
        pattern=re.compile(r"chezmoi: template:"),
        cause="Template render error. The run must fail here, before apply.",
    ),
    Signature(
        name="asdf-shims-precede-mise",
        pattern=re.compile(r"\.asdf/shims/"),
        cause="asdf shims precede mise on PATH. See 09-dotfiles-under-test.md.",
    ),
)


def match(log_lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(log_lines, start=1):
        for signature in SIGNATURES:
            if signature.pattern.search(line):
                findings.append(
                    Finding(
                        signature=signature.name,
                        cause=signature.cause,
                        line=line,
                        line_number=line_number,
                    )
                )
    return findings
