"""Pure parsing for the `gui` tier: `tart run --vnc-experimental` stdout -> VncTarget.

Stdlib-only. No subprocess, socket, filesystem, or clock access — see spec 12
§"The pure/impure boundary".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# "Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415..." (spec 12 §"gui")
_VNC_URL_RE = re.compile(r"vnc://:(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)")


@dataclass(frozen=True)
class VncTarget:
    host: str
    port: int
    password: str


def parse_vnc_url(line: str) -> VncTarget:
    match = _VNC_URL_RE.search(line)
    if match is None:
        raise ValueError(f"no vnc:// URL found in: {line!r}")
    return VncTarget(
        host=match.group("host"),
        port=int(match.group("port")),
        password=match.group("password"),
    )


# `artifacts/<run-id>/screenshots/NN-<label>.png` (spec 12 §"gui").
_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")
_SEQUENCE_PREFIX_RE = re.compile(r"^(\d+)-")


def screenshot_filename(sequence: int, label: str) -> str:
    slug = _SLUG_RE.sub("-", label).strip("-").lower()
    if not slug:
        raise ValueError(f"label produces an empty slug: {label!r}")
    return f"{sequence:02d}-{slug}.png"


def next_screenshot_sequence(existing_filenames: list[str]) -> int:
    highest = 0
    for name in existing_filenames:
        match = _SEQUENCE_PREFIX_RE.match(name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1
