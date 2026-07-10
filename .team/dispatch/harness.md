# 🧪 harness — YOUR BRIEF

**You are `harness`.** Surface `1DD2FCB0-C403-4974-980F-BC6D0BC7EAA5` (`pane:47`).
**Read [`_RULES.md`](_RULES.md) in full first.** Then this.

## You own
- `specs/macos-ci/08-dotfiles-test-harness.md`
- `specs/macos-ci/09-dotfiles-under-test.md`
- `specs/macos-ci/12-tooling-and-agent-loop.md`

## READ THE LOCAL CLONES. They are the authority. Do NOT WebFetch GitHub for them.
```
/Users/bossjones/dev/bossjones/zsh-dotfiles
/Users/bossjones/dev/bossjones/zsh-dotfiles-prep
```

## YOU OWN DEFECTS D2 AND D4

**D2 — spec 12 documents recipes that do not exist.** Confirmed by the lead:
```
$ just --summary
build-golden check default link-check link-check-fresh link-check-verbose unverified-count
verify-claims verify-claims-json verify-no-secrets
```
Spec 12 documents `build [IMAGE]`, `build-ipsw VERSION`, `images`. **None exist.** The real recipe is
`build-golden`.
> ⚠️ The brief cites these at `12:200-202`. **Do not inherit that.** The brief's *other* line-number
> claim (D5's) was **wrong**, and the prior lead pass hallucinated `12:607` in a **535-line** file.
> **Re-derive the line numbers yourself with `grep -n` / `sed -n 'Np'`.**

**D4 — spec 12's "not yet built" framing is now wrong.** `verify-claims`, `verify-claims-json`,
`unverified-count`, `check`, `verify-no-secrets`, `build-golden` and `tools/verify_claims.py` are all
**real**. Redraw the *"to build"* / *"already implemented"* split against `just --summary` and
`ls tools/ tests/`.

**D1 (with 🔐 secrets):** `Justfile:44` invokes `packer/tart-golden-image.pkr.hcl`, which **does not
exist**. `just build-golden` is broken today. **HUMAN DECISION: document only.** Do **not** author the
template; do **not** touch the `Justfile` (the lead owns it, and the only edit this run is line 63).
See **OQ-04**.

## G12 reshapes the golden image — verify EVERY bullet, and RE-DERIVE the line numbers (they are approximate)

- `zsh-dotfiles` installs **mise** itself on macOS:
  `home/.chezmoiscripts/run_onchange_before_02-macos-install-mise.sh.tmpl`, gated on
  `(eq .version_manager "mise")`.
- `zsh-dotfiles` **cannot** install **asdf** on macOS — there is no `02-macos-install-asdf` script, only
  `-centos-` / `-ubuntu-`. asdf on macOS comes **only** from `zsh-dotfiles-prep`
  (`bin/zsh-dotfiles-prereq-installer`, **~`:578`, ~`:752` — approximate, re-derive**).
- `zsh-dotfiles` **never** installs Homebrew (`install.sh:206` hard-errors) or Xcode CLT (no
  `xcode-select` anywhere).
- `home/.chezmoiignore.tmpl:5` enforces **mise/asdf mutual exclusion at the file level**.
- ⇒ **`mise` is the harness default** (the only VM `zsh-dotfiles` can bootstrap unaided); the golden
  image owns **CLT + Homebrew + chezmoi + `retry`**; the asdf leg needs `--with-prereq-installer`.

Use `file-contains` / `absent` / `file-line` claims. Several already pass
(`mise-installed-by-dotfiles-on-macos`, `no-macos-asdf-installer`, `chezmoiignore-enforces-mutual-exclusion`,
`prereq-installer-bakes-asdf`) — **extend, don't duplicate.**

**Confirm the exact `smoke-test-docker.sh` apply invocation** and the **`retry -t 4` wrapper** —
therefore the golden image must install `retry`: **verify `retry` appears in the brew prereq list.**

## G11 — non-interactive chezmoi is SOLVED UPSTREAM. Confirm; do not re-derive.
`.chezmoiroot` = `home` · `.chezmoiversion` = `2.20.0` · `home/.chezmoi.yaml.tmpl:2` =
`{{- $interactive := stdinIsATTY -}}`. Every prompt sits inside `{{- if $interactive -}}`, so in a
non-TTY run they never fire and defaults are used. Non-TTY defaults for
ruby/pyenv/nodejs/k8s/cuda/fnm/opencv are **all `false`** — *"the dotfiles installed"* means the **LEAN
set**. `computer_name`/`hostname` read env first (`CM_computer_name` / `CM_hostname`).
**`version_manager` is DELIBERATELY OUTSIDE the `$interactive` block (`:102-107`)** precisely so a
non-TTY run can select it; upstream default is `asdf` (`:20`). Override with
`--promptString version_manager=mise`. `chezmoi verify` does **not** work pre-apply — upstream uses
`chezmoi diff`. **`--promptBool` CANNOT reach the seven bools non-TTY.**

**G9** — **neither** dotfiles repo uses Ansible. Ansible is a wrapper we may *choose*, not something
inherited. Prove it with an `absent` claim.

## G13 — 12's VNC stdout format MUST STAY `<!-- UNVERIFIED -->`
The marker is at **`12-tooling-and-agent-loop.md:340`** (the lead verified this; the prior lead pass
cited `:607`, which **does not exist** — the file is 535 lines). It is pinned by the lead's proposed
`oq02-vnc-marker-pinned-at-12-340`. **Do not upgrade it to fact without booting a VM, which this run
forbids.** See **OQ-02**.

## Then: CROSS-AUDIT 🏭 tart-ci's files
`03-tart-ci-and-orchard.md`, `04-tart-licensing-risk.md`. **The G4 licence numbers are the
highest-risk figures in the repo.** Re-check them independently against `tart.run/licensing`.
**Do not edit them** — file CONFLICTs in the backlog under `### 🧪 harness`.

Propose claims to `.team/proposed/harness.jsonl`, and **dry-run them**:
```bash
uv run tools/verify_claims.py .team/proposed/harness.jsonl
```

End with exactly:
```
TASK-DONE: harness | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
