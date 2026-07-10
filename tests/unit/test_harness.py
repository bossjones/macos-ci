"""Unit coverage for `harness.py`'s few testable-without-a-VM helpers.

Most of `harness.py` is I/O (subprocess/ssh/tart) and belongs to the `vm`-tier's live exercise, not
here -- but `_resolve_golden_clone_source()` only reads `macos-versions.toml` (always present in
the repo) and is worth a fast regression test after the OQ-07 fix (it used to resolve straight to
the OCI vanilla ref, which would have cloned an unprovisioned VM).
"""

from __future__ import annotations

import macos_ci.harness as harness_module
from macos_ci.harness import (  # noqa: PLC2701
    HarnessError,
    _diff_command,
    _resolve_golden_clone_source,
    destroy_impl,
    run_impl,
)


def test_resolve_golden_clone_source_maps_default_image_to_dotfiles_golden():
    # macos-versions.toml's `default = "sequoia"`, and packer-builder's template hardcodes the
    # built golden VM's name to "dotfiles-golden" regardless of which image built it.
    assert _resolve_golden_clone_source("sequoia") == "dotfiles-golden"


def test_resolve_golden_clone_source_uses_a_forward_looking_convention_for_other_images():
    assert _resolve_golden_clone_source("tahoe") == "dotfiles-golden-tahoe"


def test_resolve_golden_clone_source_rejects_an_undeclared_image():
    try:
        _resolve_golden_clone_source("no-such-image")
    except HarnessError as exc:
        assert exc.phase == "resolve-image"
    else:
        raise AssertionError("expected HarnessError")


def test_diff_command_shell_quotes_a_mount_point_containing_spaces():
    # OQ-08, found live: the `tart --dir` mount point is "/Volumes/My Shared Files/dotfiles" --
    # spaces and all. An earlier unquoted f-string here made a real chezmoi diff stat the
    # shell-split "/Volumes/My" and fail before any real diff ran.
    command = _diff_command("/Volumes/My Shared Files/dotfiles")
    assert command == "chezmoi diff --source='/Volumes/My Shared Files/dotfiles'"


def test_diff_command_is_a_no_op_quote_for_a_path_with_no_spaces():
    assert _diff_command("/tmp/dotfiles") == "chezmoi diff --source=/tmp/dotfiles"


def test_destroy_impl_stops_before_deleting(fake_process):
    # Found live, Steps 7-10: `tart delete` refuses a running VM ("the specified VM ... does not
    # exist" -- a misleading message for "it's running"). `tart stop` must run first, and its
    # failure (VM already stopped, exit 2) must not block the delete that follows.
    fake_process.register(["tart", "stop", "dotfiles-test"], returncode=2)
    fake_process.register(["tart", "delete", "dotfiles-test"], returncode=0)

    destroy_impl(vm="dotfiles-test")

    calls = [list(call) for call in fake_process.calls]
    assert calls == [["tart", "stop", "dotfiles-test"], ["tart", "delete", "dotfiles-test"]]


def test_run_impl_forwards_dotfiles_to_up_impl(monkeypatch):
    # Found live: the Justfile defines a `dotfiles` variable (from $ZSH_DOTFILES) but never passed
    # it to `up`/`run`, and `run_impl`/the `run` typer command didn't even accept a `dotfiles`
    # parameter -- so ZSH_DOTFILES was silently ignored end-to-end. This pins the fix at the
    # run_impl -> up_impl boundary; the Justfile passing --dotfiles is a separate, unverifiable-
    # hermetically layer (see spec 12's own convention of not unit-testing the Justfile itself).
    captured = {}

    def fake_up_impl(*, vm, image, dotfiles=None):
        captured["dotfiles"] = dotfiles
        return {"vm": vm, "run_id": "20260710-000000-000000", "ip": "10.0.0.5"}

    def fake_apply_impl(*, vm, version_manager):
        return {"ok": True}

    monkeypatch.setattr(harness_module, "up_impl", fake_up_impl)
    monkeypatch.setattr(harness_module, "apply_impl", fake_apply_impl)
    monkeypatch.setattr(harness_module, "destroy_impl", lambda *, vm: None)
    monkeypatch.setattr(harness_module.artifacts, "write_json", lambda run_id, name, data: None)

    run_impl(
        vm="dotfiles-test", image="sequoia", version_manager="mise", dotfiles="/scratch/broken"
    )

    assert captured["dotfiles"] == "/scratch/broken"
