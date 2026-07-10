# 14 — Known Discrepancies

Six gaps between what the Justfile/`CLAUDE.md` describe and what `src/macos_ci/` actually does, found
while writing [`docs/`](../../docs/) and verified directly (read-only — every reproduction below is a
`--help` probe, which Typer resolves before the command body ever runs, or a plain file read; nothing here
boots a VM or mutates the tree). Each is backed by a `.team/claims.jsonl` entry so `just verify-claims` /
`just check` catches it if it's fixed or if it regresses further.

**Scope**: this page tracks these gaps. It does not fix them — that's separate follow-up work.

## 1. `just logs` calls a top-level command that doesn't exist

The Justfile's `logs` recipe runs `uv run macos-ci logs --vm {{vm}}`. `src/macos_ci/cli.py` mounts no
top-level `logs` command — `logs` only exists under the `harness` sub-app.

```
$ uv run macos-ci logs --help
Error: No such command 'logs'.

$ uv run macos-ci harness logs --help    # the correct invocation
Usage: macos-ci harness logs [OPTIONS]
  --vm  TEXT  [default: dotfiles-test]
```

Ledger: `justfile-logs-recipe-calls-nonexistent-top-level-command` (the defect),
`harness-logs-is-the-correct-invocation` (the working path).

## 2. `just vnc` calls a command that doesn't exist at all

The Justfile's `vnc` recipe runs `uv run macos-ci gui vnc --vm {{vm}}`. `src/macos_ci/gui.py` defines no
`vnc` command — only `shot` (see §3).

```
$ uv run macos-ci gui vnc --help
Error: No such command 'vnc'.
```

Ledger: `justfile-vnc-recipe-calls-nonexistent-command`.

## 3. `just shot` calls a real command that is an unconditional stub

`gui.py`'s `shot` command exists and is wired correctly, but its entire body is:

```python
@app.command()
def shot(label: str) -> None:
    raise NotImplementedError("gui.shot: not yet implemented")
```

(`src/macos_ci/gui.py:8-10`.) Every invocation raises before doing anything.

Ledger: `gui-shot-is-an-unimplemented-stub`.

## 4. `just build-ipsw` calls a top-level command that doesn't exist

The Justfile's `build-ipsw` recipe runs `uv run macos-ci build-ipsw {{VERSION}}`. No such command is
defined anywhere in `cli.py` — only `doctor` plus the `harness`/`gui`/`vm-debug` sub-apps are mounted.

```
$ uv run macos-ci build-ipsw --help
Error: No such command 'build-ipsw'.
```

Ledger: `justfile-build-ipsw-recipe-calls-nonexistent-top-level-command`.

## 5. `just pull` calls a top-level command that doesn't exist

Same shape as §4 — the Justfile's `pull` recipe runs `uv run macos-ci pull {{IMAGE}}`, and no `pull`
command exists in `cli.py`.

```
$ uv run macos-ci pull --help
Error: No such command 'pull'.
```

Ledger: `justfile-pull-recipe-calls-nonexistent-top-level-command`.

## 6. `just images-cache` doesn't exist at all

This repo's own [`CLAUDE.md`](../../CLAUDE.md) (§"Build performance") describes pre-pulling the base OCI
image so future golden-image builds clone from a local cache instead of re-pulling ~23.7GB, naming
`just images-cache` as the recipe that would do it. No recipe by that name — or with that effect — exists
in the checked-in `Justfile`; only `images` (prints `macos-versions.toml` + `tart list`) and `pull IMAGE`
(itself broken per §5) exist under the *Images* section.

Ledger: `no-images-cache-recipe-in-justfile` (the negative claim), paired with its required positive
control `justfile-images-recipe-exists` (proves the Justfile's *Images* section isn't simply empty/gutted).

## Why this page exists

None of the six gaps above were tracked as *current* `.team/claims.jsonl` entries before this page — some
were mentioned in passing inside historical, now-archived run transcripts
(`.team/macos-ci-build.board.md`, `.team/macos-ci-build.open-questions.md`) from the build run that shipped
`GATE-clean`/`DONE`, but a transcript is not a ledger entry, and `just check` passing green said nothing
about whether these six CLI paths actually work. This page and its ledger entries close that gap: the truth
gate can now catch it directly if any of these get fixed, or regress further.
