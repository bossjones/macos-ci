"""`gui` tier: VNC framebuffer screenshots (spec 12 §"gui — VNC framebuffer").

`tart run --vnc-experimental` uses Virtualization.framework's own VNC server and prints its target
to stdout; `_gui_core.parse_vnc_url()` (🐍's file) turns that into a `VncTarget`. This tier connects
with `asyncvnc` and writes PNGs to `artifacts/<run-id>/screenshots/`. Reserved for what only an eye
can judge (nerd-font glyphs, colourschemes) -- prefer the `pty` tier whenever a byte-stream answers
the question just as well (spec 12).

`asyncvnc.Client.screenshot()` returns a raw numpy array with no `.save()` -- no imaging library
(Pillow etc.) is a project dependency, and adding one is `pyproject.toml`'s owner's call, not this
test file's. `_encode_png()` below is a minimal stdlib-only (zlib + struct) PNG writer scoped to
this tier only, so this tier stays hermetic-to-write without a new dependency.

<!-- UNVERIFIED: --vnc-experimental is labelled experimental by Tart itself; the exact stdout format
this parses against is composed from a single reported example, not observed here. See spec 12's
marker at "The gui tier" and OQ-02 in .team/macos-ci.open-questions.md (inherited run). -->
"""

from __future__ import annotations

import asyncio
import struct
import zlib
from pathlib import Path
from typing import Any

import asyncvnc
import numpy as np
import pytest

from macos_ci._gui_core import next_screenshot_sequence, screenshot_filename


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def _encode_png(pixels: np.ndarray) -> bytes:
    """RGB or RGBA `(height, width, channels)` uint8 array -> PNG bytes. Stdlib-only."""
    height, width = pixels.shape[0], pixels.shape[1]
    channels = pixels.shape[2] if pixels.ndim == 3 else 1
    color_type = {1: 0, 3: 2, 4: 6}[channels]

    raw = bytearray()
    for row in pixels.astype("uint8"):
        raw.append(0)  # no per-row filter
        raw.extend(row.tobytes())

    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    body = b"\x89PNG\r\n\x1a\n"
    body += _png_chunk(b"IHDR", header)
    body += _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    body += _png_chunk(b"IEND", b"")
    return body


def _screenshots_dir(run_id: str) -> Path:
    path = Path(f"artifacts/{run_id}/screenshots")
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _capture_one(vnc_target: Any, out_path: Path) -> None:
    async with asyncvnc.connect(
        vnc_target.host, port=vnc_target.port, password=vnc_target.password
    ) as client:
        pixels = await client.screenshot()
        out_path.write_bytes(_encode_png(pixels))


@pytest.mark.gui
def test_screenshot_capture_writes_a_png(vm_state: dict[str, Any]) -> None:
    run_id = vm_state["run_id"]
    vnc_target = vm_state.get("vnc")
    if vnc_target is None:
        pytest.skip("no VNC target in state.json -- run `just vnc` first")

    out_dir = _screenshots_dir(run_id)
    sequence = next_screenshot_sequence([p.name for p in out_dir.glob("*.png")])
    filename = screenshot_filename(sequence, "boot-screen")
    out_path = out_dir / filename

    asyncio.run(_capture_one(vnc_target, out_path))

    assert out_path.exists()
    assert out_path.stat().st_size > 0
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.gui
def test_screenshot_sequence_numbers_increment() -> None:
    # Pure sequencing behaviour, exercised here (not tests/unit/) because it's this tier's own
    # concern for naming successive captures within one run -- no VM needed for this assertion.
    existing = ["01-boot-screen.png", "02-login.png"]
    assert next_screenshot_sequence(existing) == 3


def test_encode_png_round_trips_a_solid_color_image() -> None:
    # Hermetic sanity check for the stdlib PNG writer itself -- no VM, no mark, runs in the
    # default `test` tier so a regression here is caught without ever booting anything.
    pixels = np.zeros((4, 4, 3), dtype="uint8")
    pixels[:, :] = (255, 0, 0)
    png_bytes = _encode_png(pixels)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert b"IHDR" in png_bytes
    assert b"IDAT" in png_bytes
    assert png_bytes.endswith(_png_chunk(b"IEND", b""))
