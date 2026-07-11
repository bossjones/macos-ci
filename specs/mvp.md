# MVP: ship the real iTerm2-in-UTM hero screenshot

Owner: 🖥 utm + 📸 docs · Status: ready to execute (Phase B is human-in-the-loop, macOS/Apple-Silicon
only) · Created 2026-07-11.

This is the **execution spec** for replacing the README's placeholder screenshot with a real capture. It
restates [`enhance-readme.md`](enhance-readme.md) as a tight, self-contained checklist a fresh session can
run end-to-end; that doc holds the rationale (why the UTM manual lane, why not the Tart VNC path), and
this one does not contradict it.

**Prerequisite**: Phase B needs a bootable `dotfiles-golden-utm`; creating one from the Tart golden
hit a machine-identity boot hang (observed 2026-07-11) — recovery is specified in
[`prereq-mvp.md`](prereq-mvp.md).

**Scope**: the README-screenshot MVP only — Phase A (code), Phase B (live capture), Phase C (README swap).
It does **not** cover [`utm-improvements.md`](utm-improvements.md)'s live spikes A/B, the 7-item UX
checklist run, or `<!-- UNVERIFIED -->` burn-down; the UTM lane is already code-complete and that
validation is a separate effort.

**Definition of done**: the real image is committed at `docs/images/iterm2-utm-guest.png`, the README
`<img>` renders it, and `just check` is green.

## Phase A — implement `utm shot` (pure code, TDD, no VM)

Test-first, mirroring the existing pure-core (`_utm_core.py`) / impure-shell (`utm.py`) split. Gate after
this phase: `just lint && just typecheck && just check-pyrefly && just test && just check`.

### A1. Pure core + tests

Write the tests first in [`tests/unit/test_utm_core.py`](../tests/unit/test_utm_core.py) (bare asserts on
exact argv lists, the file's existing style):

- `test_build_screencapture_argv_full` — `full=True` (or no `window_id`) yields the whole-display argv.
- `test_build_screencapture_argv_window_id` — a `window_id` adds `-l <id>`.
- `test_build_screencapture_argv_default_is_full_display` — with neither, no `-l`.

Then add to [`src/macos_ci/_utm_core.py`](../src/macos_ci/_utm_core.py):

```python
def build_screencapture_argv(path: str, *, window_id: int | None = None, full: bool = False) -> list[str]:
    argv = ["/usr/sbin/screencapture", "-x", "-o"]      # -x: no sound; -o: no window shadow
    if window_id is not None and not full:
        argv += ["-l", str(window_id)]                   # target one window by CGWindowID
    argv.append(path)
    return argv
```

### A2. Impure shell + tests

Write shell tests first in [`tests/unit/test_utm.py`](../tests/unit/test_utm.py) (pytest-subprocess
`FakeProcess` + `tmp_path`, the file's style): the command computes the right output path under a fake
run's `screenshots` dir and shells `screencapture` — no real VM, no real `utmctl`, no UTM.app launch.

Then add a `shot` command to [`src/macos_ci/utm.py`](../src/macos_ci/utm.py):

- **Resolve the current run** the way the lane already does: `up_impl` writes `state.json` via the
  `artifacts` writer keyed by a `run_id` (see [`src/macos_ci/utm.py`](../src/macos_ci/utm.py) `up_impl`).
  Read the latest `state.json`, take its `run_id`, and target
  `_harness_core.artifact_paths(run_id).screenshots_dir` (`artifacts/<run-id>/screenshots`). If no live
  run exists, raise `UtmError` with a clear "run `just utm-up` first" message.
- **Filename** via the existing helpers — do not reinvent: `next_screenshot_sequence(existing)` then
  `screenshot_filename(seq, label)` (both in [`src/macos_ci/_gui_core.py`](../src/macos_ci/_gui_core.py)),
  producing `NN-<slug>.png`.
- **Capture**: foreground UTM (`open -a UTM`), resolve the UTM window id **best-effort** (dependency-free
  `osascript`/CGWindowList probe); on any failure fall back to `--full` whole-display capture. Run
  `build_screencapture_argv(...)` and print the saved path.
- **Wiring** mirrors the file: `@app.command("shot")`, `label: str` positional,
  `vm: str = typer.Option(_UTM_VM_DEFAULT, "--vm")`, `full: bool = typer.Option(False, "--full")`.

> **Honest design note.** Targeting the exact UTM window without a Quartz/pyobjc dependency is awkward, and
> this repo values no-new-deps (see [`CLAUDE.md`](../CLAUDE.md)). So `--full` is the always-works path and
> window-targeting is best-effort — worst case `just utm-shot hero` captures the full display and the
> human crops, still a real, honest capture. The unit-tested contract is `build_screencapture_argv`; the
> window-id resolver is impure and may degrade to full.

### A3. Justfile recipe

Append to the Justfile's UTM group (append-only — existing ledger claims pin line numbers):

```
utm-shot LABEL:
    @uv run macos-ci utm shot {{LABEL}} --vm {{utm_vm}}
```

### A4. Ledger claim

Append one positive control to [`.team/claims.jsonl`](../.team/claims.jsonl) (not `local_only`, so
`just verify-claims` runs it in CI too):

```json
{"id": "macos-ci-utm-shot-command-exists", "kind": "cli-help", "file": "specs/mvp.md", "argv": ["uv", "run", "macos-ci", "utm", "shot", "--help"], "expect": "Usage: macos-ci utm shot", "claim": "the `utm shot` command backing `just utm-shot` is wired (host-side screencapture of the UTM window); distinct from the still-stubbed Tart-lane `gui shot`/`gui vnc` (14 sect 2/3)"}
```

This does not touch or invert the two gap claims for the Tart-lane `gui vnc`/`gui shot`
(`justfile-vnc-recipe-calls-nonexistent-command`, `gui-shot-is-an-unimplemented-stub`) — those stay as-is
([`14-known-discrepancies.md`](macos-ci/14-known-discrepancies.md) §2/§3).

## Phase B — capture the hero shot (live, human-in-the-loop, macOS/Apple-Silicon)

Runs on your Apple-Silicon Mac with UTM installed; no headless job can produce this frame.

1. `just utm-up` → `just utm-gui`. Over SSH (`just utm-ssh`), `brew install --cask iterm2` if it is not
   already present in the guest — a documented step, not a golden-image or `zsh-dotfiles` change.
2. In the guest window, open iTerm2, paste the `just utm-bootstrap-dotfiles` block, run `chezmoi apply`,
   then open a fresh shell so the prompt renders (git-branch glyph, sheldon syntax highlighting, 24-bit
   color). These are checklist items 1/2/5 from
   [`tests/manual/test_utm_ux.py`](../tests/manual/test_utm_ux.py).
3. `just utm-shot hero` — captures the UTM window into `artifacts/<run-id>/screenshots/`.
4. Copy the chosen PNG to `docs/images/iterm2-utm-guest.png`. Then `just utm-destroy`.

## Phase C — swap the README placeholder (code; only after Phase B's PNG exists)

Replace the placeholder block under `#### 📸 Screenshot: iTerm2 inside the UTM guest` in
[`README.md`](../README.md) (keep the heading) with an honest caption and the real image, matching the
repo's centered-`<img>` convention:

```html
#### 📸 Screenshot: iTerm2 inside the UTM guest

Captured from a real UTM manual-lane session (`just utm-up` → open iTerm2 in the guest → paste the
`just utm-bootstrap-dotfiles` block → `chezmoi apply`): the `zsh-dotfiles` prompt with its git-branch
glyph, sheldon syntax highlighting, and 24-bit color, rendered in a genuine windowed macOS guest — what a
headless SSH run can't show you.

<p align="center">
  <img src="docs/images/iterm2-utm-guest.png" alt="iTerm2 inside a UTM macOS guest window: the zsh-dotfiles prompt rendering a git-branch glyph, sheldon syntax highlighting, and 24-bit color" width="720">
</p>
```

Add one row to the README's Recipe Reference "UTM" table:

```
| `utm-shot LABEL` | Host-side `screencapture` of the UTM window into `artifacts/<run-id>/screenshots/`. The only capture path for an Apple-backend guest — no VNC framebuffer, no in-guest screencapture over SSH. |
```

## Verification

- `uv run macos-ci utm shot --help` — the command is wired (Phase A).
- `uv run pytest tests/unit -k screencapture` — the argv-builder unit test passes (Phase A).
- `just lint && just typecheck && just check-pyrefly && just test` — gates green (Phase A).
- `just link-check` — after Phase C, the `docs/images/iterm2-utm-guest.png` `<img src>` resolves.
- `just check` — the full truth gate (`link-check` + `verify-claims` + `unverified-count`) green: the new
  cli-help claim passes and nothing else regresses.
- Visual: the image renders in the README on GitHub after commit.

## Honesty handling

- **No fabricated image.** The README `<img>` is swapped in **only after** `docs/images/iterm2-utm-guest.png`
  is a real capture and committed, because lychee's `file` scheme checks the `src`. If a session can't
  capture the shot, the labeled placeholder **stays** — Phase C simply does not happen, and `just check`
  stays green on the unchanged placeholder.
- This spec cites the future PNG as a **backticked path** (`docs/images/iterm2-utm-guest.png`), never as a
  markdown link or `<img>`, because the file does not exist yet — so lychee has nothing to flag here.
- **No new `<!-- UNVERIFIED -->` markers.** The one load-bearing new assertion (the `utm shot` command
  exists) is the machine-checked ledger claim above, not prose.
