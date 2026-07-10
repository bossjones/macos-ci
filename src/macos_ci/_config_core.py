"""Pure validation of `macos-versions.toml` (spec 12 §"macos-versions.toml").

Stdlib-only. Takes already-parsed TOML data; `config.py` owns reading the file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_VALID_SOURCES = frozenset({"oci", "ipsw"})


class ConfigError(ValueError):
    """`macos-versions.toml` fails validation."""


@dataclass(frozen=True)
class Image:
    name: str
    source: str
    ref: str | None = None
    url: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class Config:
    default: str
    images: dict[str, Image]


def load(raw: dict[str, Any]) -> Config:
    default = raw.get("default")
    if not isinstance(default, str):
        raise ConfigError("'default' must be a string naming an [image.<name>] table")

    images: dict[str, Image] = {}
    for name, entry in raw.get("image", {}).items():
        source = entry.get("source")
        if source not in _VALID_SOURCES:
            raise ConfigError(
                f"image {name!r}: unknown source {source!r}, expected one of {sorted(_VALID_SOURCES)}"
            )

        if source == "ipsw" and not entry.get("sha256"):
            raise ConfigError(f"image {name!r}: ipsw source requires 'sha256'")

        images[name] = Image(
            name=name,
            source=source,
            ref=entry.get("ref"),
            url=entry.get("url"),
            sha256=entry.get("sha256"),
        )

    if default not in images:
        raise ConfigError(
            f"default {default!r} names an image that does not exist in {sorted(images)}"
        )

    return Config(default=default, images=images)
