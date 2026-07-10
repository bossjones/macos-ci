"""I/O shell: executes argv built by `_tart_core` and parses `tart` output."""

from __future__ import annotations

import subprocess

from macos_ci._tart_core import DirMount, clone_argv, delete_argv, ip_argv, run_argv


def clone(source: str, name: str) -> None:
    subprocess.run(clone_argv(source, name), check=True)


def run(
    name: str,
    *,
    headless: bool = True,
    dirs: list[DirMount] | None = None,
    vnc_experimental: bool = False,
    net_bridged: str | None = None,
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        run_argv(
            name,
            headless=headless,
            dirs=dirs,
            vnc_experimental=vnc_experimental,
            net_bridged=net_bridged,
        )
    )


def ip(name: str, *, resolver: str = "dhcp") -> str:
    result = subprocess.run(
        ip_argv(name, resolver=resolver), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def delete(name: str) -> None:
    subprocess.run(delete_argv(name), check=True)
