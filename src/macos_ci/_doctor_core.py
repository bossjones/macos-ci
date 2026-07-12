"""Pure requirement table, version compare, and verdict logic for `just doctor`.

Stdlib-only. `doctor.py` gathers the raw facts (shutil.which, platform, subprocess probes,
filesystem, keychain state) and hands them to `check()` here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_MIN_VERSIONS: dict[str, str] = {
    "tart": "2.0.0",
    "packer": "1.10.0",
}

REQUIRED_TOOLS: tuple[str, ...] = ("tart", "packer", "just", "uv", "cirrus", "sshpass")

# specs/utm-improvements.md step 6: the UTM manual lane is an optional escape hatch (spec 10 --
# tart is primary). Its absence must never fail `just doctor` on a tart-only host.
OPTIONAL_TOOLS: tuple[str, ...] = ("utm",)

_MIN_MACOS_VERSION = "13.0"  # Tart's floor (spec 01 §"Install")
_MIN_FREE_DISK_GB = 60.0  # matches the preflight's ">> 60 GB free, OK" convention

# G4: Fair Source accepted-risk ceiling — always reported, never silently approved
# (specs/macos-ci/04-tart-licensing-risk.md, README.md "Licensing accepted-risk sign-off (G4)").
FLEET_CEILING_NOTICE = "≤03 hosts / ≤100 combined CPU cores (G4 accepted-risk, see README.md)"


def _parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in re.split(r"[.\-]", version):
        match = re.match(r"\d+", chunk)
        if match is None:
            break
        parts.append(int(match.group()))
    return tuple(parts)


def version_at_least(found: str, minimum: str) -> bool:
    # OQ-01: tuple comparison treats a shorter tuple that is a prefix of a longer one as *less
    # than* it (e.g. (2, 0) < (2, 0, 0)), so a numerically-equal short-form version spuriously
    # failed. Zero-pad both to the longer length before comparing.
    found_parts = _parse_version(found)
    minimum_parts = _parse_version(minimum)
    length = max(len(found_parts), len(minimum_parts))
    found_padded = found_parts + (0,) * (length - len(found_parts))
    minimum_padded = minimum_parts + (0,) * (length - len(minimum_parts))
    return found_padded >= minimum_padded


@dataclass(frozen=True)
class DoctorFacts:
    """Raw, already-collected facts. Collecting them is `doctor.py`'s job, not this module's."""

    tool_versions: dict[str, str | None] = field(default_factory=dict)
    arch: str = "arm64"
    macos_version: str = "0.0"
    login_keychain_unlocked: bool = False
    zsh_dotfiles_path: str | None = None
    zsh_dotfiles_path_exists: bool = False
    free_disk_space_gb: float = 0.0
    optional_tool_versions: dict[str, str | None] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    tool: str
    required: str
    found: str | None
    ok: bool


def check(facts: DoctorFacts) -> list[CheckResult]:
    results: list[CheckResult] = []

    for tool in REQUIRED_TOOLS:
        found = facts.tool_versions.get(tool)
        minimum = _MIN_VERSIONS.get(tool)
        if found is None:
            results.append(
                CheckResult(
                    tool=tool,
                    required=f">={minimum}" if minimum else "present",
                    found=None,
                    ok=False,
                )
            )
        elif minimum is not None:
            results.append(
                CheckResult(
                    tool=tool,
                    required=f">={minimum}",
                    found=found,
                    ok=version_at_least(found, minimum),
                )
            )
        else:
            results.append(CheckResult(tool=tool, required="present", found=found, ok=True))

    results.append(
        CheckResult(
            tool="apple-silicon", required="arm64", found=facts.arch, ok=facts.arch == "arm64"
        )
    )

    results.append(
        CheckResult(
            tool="macos-version",
            required=f">={_MIN_MACOS_VERSION}",
            found=facts.macos_version,
            ok=version_at_least(facts.macos_version, _MIN_MACOS_VERSION),
        )
    )

    results.append(
        CheckResult(
            tool="login-keychain-unlocked",
            required="unlocked",
            found="unlocked" if facts.login_keychain_unlocked else "locked",
            ok=facts.login_keychain_unlocked,
        )
    )

    results.append(
        CheckResult(
            tool="ZSH_DOTFILES",
            required="exists",
            found=facts.zsh_dotfiles_path if facts.zsh_dotfiles_path_exists else None,
            ok=facts.zsh_dotfiles_path_exists,
        )
    )

    results.append(
        CheckResult(
            tool="free-disk-space",
            required=f">={_MIN_FREE_DISK_GB:g}GB",
            found=f"{facts.free_disk_space_gb:g}GB",
            ok=facts.free_disk_space_gb >= _MIN_FREE_DISK_GB,
        )
    )

    # Report-only: G4 must never be silently approved as a pass/fail gate.
    results.append(
        CheckResult(
            tool="fleet-ceiling", required="report-only", found=FLEET_CEILING_NOTICE, ok=True
        )
    )

    # specs/utm-improvements.md step 6: optional rows never gate -- ok=True unconditionally, so a
    # tart-only host with no UTM installed never fails `just doctor`.
    for tool in OPTIONAL_TOOLS:
        results.append(
            CheckResult(
                tool=tool,
                required="optional",
                found=facts.optional_tool_versions.get(tool),
                ok=True,
            )
        )

    return results


def overall_ok(results: list[CheckResult]) -> bool:
    return all(r.ok for r in results)
