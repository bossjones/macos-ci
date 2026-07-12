# Enhance the README: capture the iTerm2-in-UTM hero screenshot

Owner: 🖥 utm + 📸 docs · Status: planned (capture is human-in-the-loop, macOS/Apple-Silicon only) ·
Created 2026-07-11.

The [`README.md`](../README.md) rewrite is complete and passes [`just check`](../CLAUDE.md), but it
deliberately did **not** fabricate a screenshot. The section `#### 📸 Screenshot: iTerm2 inside the UTM
guest` ships a **labeled blockquote placeholder** ("Placeholder — not yet captured") with an interim
diagram (`specs/plans/macos-ci/solution.png`) standing in for the real capture. This spec plans the real
capture and the swap-in, without ever fabricating an image and without turning `just check` red.

**Scope**: one hero screenshot — iTerm2 rendering `zsh-dotfiles` inside a real UTM macOS guest — plus the
minimal host-side command that makes the capture repeatable, plus the exact README edit. It does **not**
fix [`14-known-discrepancies.md`](macos-ci/14-known-discrepancies.md) gaps #2/#3 (the Tart-lane
`gui vnc`/`gui shot` path); those stay documented stubs, and the new `utm shot` command below is a
**distinct, working command**, not a fix for `gui shot`.

## 1. Why the hero shot belongs to the UTM manual lane, and what constrains its capture

The hero shot shows what only an eye can judge — nerd-font glyphs, sheldon syntax highlighting, 24-bit
color — in a genuine windowed macOS guest. A headless SSH/PTY run cannot render it, so it belongs to the
**UTM manual lane**, which a human drives (`just utm-up` → open iTerm2 in the guest → paste the
`just utm-bootstrap-dotfiles` block → `chezmoi apply`).

Two settled, ledger-backed facts constrain *how* the capture can be automated:

1. **UTM's Apple-backend macOS guest has no keystroke-injection / guest-exec surface.**
   `utmctl`/AppleScript `sendText`/`exec`/`file` are QEMU-guest-agent-gated
   ([`05-utm-automation.md`](macos-ci/05-utm-automation.md) §2.6 Input Automation, §4 the `utmctl`
   wrapper). So we cannot script "type into iTerm2 inside the guest" — driving the guest GUI stays a
   human job.
2. **In-guest `screencapture` over SSH black-frames.** It is gated by macOS's Screen Recording (TCC)
   permission and returns a black frame from an SSH session
   ([`12-tooling-and-agent-loop.md`](macos-ci/12-tooling-and-agent-loop.md) §"`gui` — VNC framebuffer").

What *is* scriptable is the **host side**: macOS `screencapture` runs in the host's own GUI session,
which is already permissioned, so the *capture* becomes a recipe even though *driving the guest* does
not. Reaching the guest for the setup steps (e.g. installing iTerm2) uses the host-side IP discovery
already built for this lane ([`05-utm-automation.md`](macos-ci/05-utm-automation.md) §4.5): read the VM's
MAC from its `.utm` bundle, match it against `/var/db/dhcpd_leases`, `ssh` in.

### Why not the Tart-lane VNC framebuffer path

[`12-tooling-and-agent-loop.md`](macos-ci/12-tooling-and-agent-loop.md) §"`gui` — VNC framebuffer"
describes `tart run --vnc-experimental` → `_gui_core.parse_vnc_url()` → `asyncvnc` → PNGs, and it is
fully automatable. But it captures a **headless Tart desktop**, not an interactive iTerm2 session running
the dotfiles — so it is not the hero shot. It also remains an unimplemented stub
([`14-known-discrepancies.md`](macos-ci/14-known-discrepancies.md) §2 `gui vnc` missing, §3 `gui shot` =
`NotImplementedError`). This spec **defers** that path and leaves both gaps and their two
[`.team/claims.jsonl`](../.team/claims.jsonl) entries (`justfile-vnc-recipe-calls-nonexistent-command`,
`gui-shot-is-an-unimplemented-stub`) untouched.

## 2. What the hero shot must show

The shot targets three items from the recorded iTerm2 UX checklist
([`tests/manual/test_utm_ux.py`](../tests/manual/test_utm_ux.py)) at once — the ones that read from a
single still frame:

- **glyphs** — the prompt shows a git-branch glyph and no tofu/replacement-character boxes
  (`test_iterm2_prompt_renders_with_glyphs`);
- **sheldon highlighting** — a typed command shows syntax highlighting and ghost-text autosuggestion
  (`test_sheldon_plugins_active`);
- **24-bit color** — colors are correct and a truecolor test strip renders smooth
  (`test_colorscheme_and_profile`).

The remaining four checklist items (Ctrl-R history search, tab-completion menu, no first-run warnings,
Option-word-motion) are interaction signals, not a still frame; they remain the `manual` tier's job and
are **not** separate deliverables here.

## 3. The `utm shot` capture command

A new host-side command makes the capture one repeatable step. It mirrors the existing
`_utm_core` (pure) / [`utm.py`](../src/macos_ci/utm.py) (I/O shell) split, and reuses the screenshot
helpers already in the tree.

**Contract**

- `macos-ci utm shot LABEL [--vm <name>] [--full]` — and a `just utm-shot LABEL` recipe under the
  Justfile's UTM section.
- Foregrounds the UTM window (`open -a UTM`), then runs macOS `screencapture` of that window, writing to
  `artifacts/<run-id>/screenshots/NN-<label>.png`.
- Filename/sequence come from the existing pure helpers
  [`_gui_core.screenshot_filename(seq, label)`](../src/macos_ci/_gui_core.py) and
  `next_screenshot_sequence(...)`; the directory is
  [`_harness_core`](../src/macos_ci/_harness_core.py)'s `screenshots_dir` (`<root>/screenshots`). No new
  path convention is introduced.
- `--full` falls back to a full-display capture when a specific window id cannot be resolved.
- Prints the saved path. The human then promotes the chosen frame to `docs/images/iterm2-utm-guest.png`
  (artifacts stay ephemeral; `docs/images/` is curated).

**Pure core (unit-testable, no VM)**

```python
# src/macos_ci/_utm_core.py
def build_screencapture_argv(path: str, *, window_id: int | None = None, full: bool = False) -> list[str]:
    argv = ["/usr/sbin/screencapture", "-x", "-o"]           # -x: no sound; -o: no window shadow
    if window_id is not None and not full:
        argv += ["-l", str(window_id)]                        # capture a specific window by CGWindowID
    argv.append(path)
    return argv
```

The impure shell ([`utm.py`](../src/macos_ci/utm.py)) resolves the window id (an `osascript`/CGWindowList
helper) and executes the argv, exactly as [`tart.py`](../src/macos_ci/tart.py) drives
[`_tart_core`](../src/macos_ci/_tart_core.py). No new third-party dependency: `screencapture` is a macOS
built-in, and `asyncvnc`/`vncdotool` are **not** pulled in (that is the deferred Tart path).

**Ledger** — one positive `cli-help` control keeps the new (non-⚠️) recipe honest, added to
[`.team/claims.jsonl`](../.team/claims.jsonl):

```json
{"id": "macos-ci-utm-shot-command-exists", "kind": "cli-help", "file": "specs/enhance-readme.md",
 "argv": ["uv", "run", "macos-ci", "utm", "shot", "--help"], "expect": "Usage: macos-ci utm shot",
 "claim": "the `utm shot` command backing `just utm-shot` is wired (host-side screencapture of the UTM window); distinct from the still-stubbed Tart-lane `gui shot`/`gui vnc` (14 §2/§3)"}
```

Not `local_only`: `--help` resolves wherever the package installs, so `just verify-claims` runs it in CI
too. It does **not** invert or touch the two gap claims in §1.

## 4. Capture procedure (execution-time, human-in-the-loop)

Runs on the author's Apple-Silicon Mac with UTM installed; no headless CI job can produce this frame.

1. `just utm-up` → `just utm-gui`. Over SSH (`just utm-ssh`), `brew install --cask iterm2` if it is not
   already present in the guest — a documented step, not a golden-image or `zsh-dotfiles` change.
2. In the guest window, open iTerm2, paste the `just utm-bootstrap-dotfiles` block, run `chezmoi apply`,
   then open a fresh shell so the prompt renders (glyphs, sheldon highlighting, 24-bit color).
3. `just utm-shot hero` — captures the UTM window into `artifacts/<run-id>/screenshots/`.
4. Copy the chosen PNG to `docs/images/iterm2-utm-guest.png`. Then `just utm-destroy`.

## 5. The README edit

Replace the placeholder block under `#### 📸 Screenshot: iTerm2 inside the UTM guest` (keep the heading)
with an honest caption and the real image — matching the repo's existing local-image convention (centered
HTML `<img>`, as `specs/plans/macos-ci/hero.png` uses):

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

## 6. Honesty handling

- **No fabricated image.** The README `<img>` is swapped in **only after** `docs/images/iterm2-utm-guest.png`
  is a real capture and committed, because lychee's `file` scheme checks the `src`. If a session can't
  capture the shot, the labeled placeholder **stays** — the swap and the PNG commit simply do not happen,
  and `just check` remains green on the unchanged placeholder.
- **This spec cites the future PNG as a backticked path** (`docs/images/iterm2-utm-guest.png`), never as
  a markdown link or `<img>`, precisely because the file does not exist yet — so lychee has nothing to
  flag here. (This is the intended exception to "write every URL as a markdown link": we deliberately do
  not want a not-yet-existing file checked.)
- **No new `<!-- UNVERIFIED -->` markers.** Nothing in this spec asserts an unverified fact; the one
  load-bearing new assertion (the `utm shot` command exists) is a machine-checked ledger claim, not prose.

## 7. Verification

- `just link-check` — every markdown link plus every local `<img src>` resolves (this is what catches a
  dangling image path if the README is swapped before the PNG lands).
- `just verify-claims` — the new `macos-ci-utm-shot-command-exists` control passes; the gaps #2/#3 claims
  still pass unchanged.
- `just unverified-count` — unchanged vs. baseline (the honesty budget).
- `just check` — the full truth gate (`link-check` + `verify-claims` + `unverified-count`).
- `uv run pytest tests/unit -k screencapture` — the `build_screencapture_argv` argv-shape unit test.
- `uv run macos-ci utm shot --help` — the command is wired.
- Visual: after committing, confirm `docs/images/iterm2-utm-guest.png` renders in the README on GitHub.
