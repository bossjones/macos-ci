"""Pure argv builders for the `tart` CLI (spec 01 §"Core CLI commands", §"Shared directories").

Stdlib-only. No subprocess execution — `tart.py` owns that.
"""

from __future__ import annotations

from dataclasses import dataclass

_RESOLVERS = frozenset({"dhcp", "arp", "agent"})


@dataclass(frozen=True)
class DirMount:
    """A `--dir=name:/path/on/host[:ro]` share (spec 01 §"Shared directories")."""

    name: str
    path: str
    read_only: bool = False

    def to_flag(self) -> str:
        flag = f"--dir={self.name}:{self.path}"
        if self.read_only:
            flag += ":ro"
        return flag


def clone_argv(source: str, name: str) -> list[str]:
    return ["tart", "clone", source, name]


def run_argv(
    name: str,
    *,
    headless: bool = True,
    dirs: list[DirMount] | None = None,
    vnc_experimental: bool = False,
    net_bridged: str | None = None,
) -> list[str]:
    argv = ["tart", "run", name]
    if headless:
        argv.append("--no-graphics")
    if vnc_experimental:
        argv.append("--vnc-experimental")
    if net_bridged:
        argv.append(f"--net-bridged={net_bridged}")
    for mount in dirs or []:
        argv.append(mount.to_flag())
    return argv


def ip_argv(name: str, *, resolver: str = "dhcp") -> list[str]:
    if resolver not in _RESOLVERS:
        raise ValueError(f"unknown resolver {resolver!r}, expected one of {sorted(_RESOLVERS)}")
    return ["tart", "ip", name, "--resolver", resolver]


def delete_argv(name: str) -> list[str]:
    return ["tart", "delete", name]
