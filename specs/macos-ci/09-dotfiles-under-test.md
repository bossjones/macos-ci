# 09 — What Is Actually Under Test

Owner: 🧪 harness. Sources: local working trees at
`/Users/bossjones/dev/bossjones/zsh-dotfiles` and
`/Users/bossjones/dev/bossjones/zsh-dotfiles-prep` (read directly, not via WebFetch — see G11).
Line numbers cited below are from the trees as read on 2026-07-09.

This spec answers "if a macOS VM runs the dotfiles bootstrap, what should come out the other end,
and what does 'correctly installed' mean?" [11-tart-vs-utm harness spec 08](./08-dotfiles-test-harness.md)
is the harness *design*; this file is the harness's *subject matter*.

## Two repos, two jobs

- **`zsh-dotfiles-prep`** — OS-level prerequisite installer (Homebrew, Xcode CLT, asdf, chezmoi
  binary, Rust, Go, sheldon). Not chezmoi-managed itself; it is what chezmoi needs already present.
- **`zsh-dotfiles`** — the chezmoi source repo (`.chezmoiroot` = `home`, so chezmoi treats
  `home/` as the config root: `zsh-dotfiles/.chezmoiroot:1`). This is what actually lays down
  `~/.zshrc`, `~/.sheldon`, etc.

**Neither repo is *provisioned by* Ansible.** `zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer` is a
plain POSIX/bash script (strap.sh-derived — see its own header comment,
`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer:4`); `zsh-dotfiles` is driven end-to-end by
`chezmoi init --apply`. No playbook, role, or inventory exists in either tree.

`ansible` does appear in the stack, **twice**, both in `zsh-dotfiles-prep/Brewfile`: `:57` (`brew
"ansible"`, one of 500+ formulae) and `:602` (`vscode "redhat.ansible"`). Both are *installable tools*,
not the mechanism that installs anything else. This is G9 — but note that G9 therefore **cannot** be
stated as *"the string `ansible` is absent"*, only as *"no Ansible playbook drives either repo"*.
The ledger proves the second, not the first.

## Bootstrap, verbatim (G9)

```sh
curl -fsSL https://raw.githubusercontent.com/bossjones/zsh-dotfiles-prep/main/bin/zsh-dotfiles-prereq-installer | bash -s -- --debug
```
(`zsh-dotfiles-prep/README.md:12`. `docs/quickstart.md:10` is a **different** bootstrap — it curls
`zsh-dotfiles-prep/install.sh`, not the prereq installer, and passes no `--debug`.)

The prereq installer's own closing "next steps" line
(`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer:1135`) is:

```sh
chezmoi init -R --debug -v --apply https://github.com/bossjones/zsh-dotfiles.git
```

It is a bare `chezmoi init` — the installer has already put the binary on `$PATH` at `:1132`
(`sh -cx "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME"/.bin -t v2.31.1`), which is an *install* step, not
an init. For a source-checkout run — which is what a VM harness actually does — the equivalent is
`chezmoi init -R --debug -v --apply --force --source=.` per
`zsh-dotfiles/scripts/smoke-test-docker.sh:361-365`, see below.

The macOS prereq installer (`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer`) is heavyweight:
Xcode CLT (`xcode-select --install`), Homebrew, ~25 brew formulae including compiled deps for Ruby
(openssl@3, readline, libyaml, gmp, autoconf), asdf v0.11.2 cloned from git, Rust via rustup, global
Python via both brew and pyenv (3.12.8, built with `--enable-shared`), fnm + Node 20.19.5, and
finally chezmoi itself pinned to **v2.31.1** (`get.chezmoi.io` installer,
`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer:1132`) — comfortably above the
`.chezmoiversion` floor of `2.20.0` (`zsh-dotfiles/.chezmoiversion:1`). This step alone is why
09/08 recommend a golden image (see 08(a)): it is slow (Homebrew + Ruby toolchain compile time) and
network-heavy, but idempotent and identical for every test run, so it belongs in the image, not in
the per-test path.

## The chezmoi template contract (G11)

`zsh-dotfiles/home/.chezmoi.yaml.tmpl` is the whole non-interactive story. Read top to bottom:

1. **Line 2**: `{{- $interactive := stdinIsATTY -}}`. Every prompt in the file is gated on this.
2. **Lines 6–20**: seven boolean feature flags (`ruby`, `pyenv`, `nodejs`, `k8s`, `cuda`, `fnm`,
   `opencv`) default `false`, plus `version_manager` defaulting `"asdf"`.
3. **Lines 33–100**: the entire `promptString`/`promptBool` block for
   `name`/`email`/`computer_name`/`hostname`/`ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv`
   sits inside `{{- if $interactive -}} ... {{- end -}}`.
4. **Lines 102–107**: `version_manager` is the one exception — its `hasKey`/`promptString` pair is
   **outside** the `$interactive` guard, on purpose. The inline comment at line 102 spells out why:
   the prompt key must literally be `"version_manager"` so a non-TTY
   `--promptString version_manager=…` flag matches it, and it must stay outside the guard so a
   non-TTY run can still steer it.

**Mechanism, not investigation**: an SSH/exec session with no TTY attached makes `stdinIsATTY`
return false. That single boolean gates every prompt above except `version_manager`. No flag, no
config trick, no chezmoi feature discovery is involved — it is exactly what `$interactive` being
false already means. This is settled; see 08(b) for how the harness exploits it.

### Non-TTY default state (what "installed" means for a lean baseline run)

| Field | Non-TTY value | Source |
|---|---|---|
| `name` | `"Malcolm Jones"` | `.chezmoi.yaml.tmpl:24` |
| `email` | `"bossjones@theblacktonystark.com"` | `.chezmoi.yaml.tmpl:25` |
| `computer_name` | `env CM_computer_name`, else `"boss workstation"` | `.chezmoi.yaml.tmpl:26` |
| `hostname` | `env CM_hostname`, else `"bossworkstation"` | `.chezmoi.yaml.tmpl:27` |
| `ruby` | `false` | `.chezmoi.yaml.tmpl:6` |
| `pyenv` | `false` | `.chezmoi.yaml.tmpl:8` |
| `nodejs` | `false` | `.chezmoi.yaml.tmpl:10` |
| `k8s` | `false` | `.chezmoi.yaml.tmpl:12` |
| `cuda` | `false` | `.chezmoi.yaml.tmpl:18` |
| `fnm` | `false` | `.chezmoi.yaml.tmpl:16` |
| `opencv` | `false` | `.chezmoi.yaml.tmpl:14` |
| `version_manager` | `"asdf"` (overridable non-TTY via `--promptString`) | `.chezmoi.yaml.tmpl:20` |

**A baseline non-TTY harness run installs the *lean* set only**: zsh config, Sheldon plugin
management, tmux, nvim, fzf, git config, and the `asdf`-vs-`mise` version-manager scaffolding — it
does **not** provision Ruby, a pyenv-managed Python, Node.js, Kubernetes tooling, CUDA, fnm, or
OpenCV, because those seven `promptBool`s never fire without a TTY. Any assertion or spec that
assumes "the dotfiles installed" includes those toolchains is wrong for a non-TTY harness run and
must say "lean baseline" instead.

`computer_name`/`hostname` are the two fields that *are* reachable non-TTY, via `CM_computer_name`
and `CM_hostname` env vars (`.chezmoi.yaml.tmpl:26-27`) — the harness sets these per VM so parallel
runs are distinguishable in logs and in the rendered config (see 08(b)).

### The `version_manager` selector (asdf | mise)

`version_manager` (`.chezmoi.yaml.tmpl:20`, comment at `:102`) is deliberately reachable non-TTY:
`--promptString version_manager=mise` (or `=asdf`) selects the lane. It is the **only** prompt key
placed outside the `if $interactive` block — every other prompt, including all seven feature bools,
sits inside it and is therefore unreachable in a non-TTY run (G11). Together with the `CM_computer_name`
and `CM_hostname` env vars, it is the entire externally-settable surface of a non-interactive apply.

Mutual exclusion is enforced in two places. At the **file** level, `home/.chezmoiignore.tmpl:5` —
`{{ if eq .version_manager "mise" }}` ignores the asdf scripts, `{{ else }}` ignores the mise ones — so
selecting one lane prevents the other's scripts from ever rendering. At the **shell-init** level,
`zsh-dotfiles/scripts/smoke-test-docker.sh` never sources `asdf.sh` or sets `ASDF_DIR` when
`VERSION_MANAGER=mise`, and vice versa — the invariant is stated in the comment at
`smoke-test-docker.sh:222-224` (citing `specs/migrate-asdf-to-mise.md:15-27` in that repo) and *enforced*
by the `if [[ "$VERSION_MANAGER" == "asdf" ]]` branch at `:245`. A harness that runs both lanes must
preserve this: never let both managers' shell initialization run in the same test.

### What `zsh-dotfiles` cannot bootstrap on macOS

`zsh-dotfiles` is a dotfiles/config layer that provisions user-space tools on top of an
already-bootstrapped system. Read directly from the source, the boundary is sharp:

**It installs itself, on macOS:** `mise` (`run_onchange_before_02-macos-install-mise.sh.tmpl`, gated on
`(eq .version_manager "mise")`, via `brew install mise`), `sheldon` (built from source via rustup+cargo
on arm64 — slow, and a hard Xcode CLT dependency), `bun`, `deno`, `uv`, and `wtp`.

**It never installs:**

- **Homebrew.** `install.sh:206-209` hard-errors when brew is missing (`:206` opens the guard,
  `:209` is the `exit 1`). Every `brew install` in the repo assumes it is already present.
- **Xcode Command Line Tools.** `xcode-select` appears in no *tracked* file of `zsh-dotfiles`
  (`git grep -c xcode-select` → no output). An untracked `.venv/` vendors npm's `node-gyp` docs, which
  do mention it — which is why the ledger claim probes the tracked tree, not the working tree.
- **asdf, on macOS.** There is no `run_*-macos-install-**asdf.sh**` *installer* — the `02-*-install-asdf`
  scripts exist only for `centos` and `ubuntu`. A macOS asdf-***plugins*** script *does* exist
  (`run_onchange_after_50-macos-install-asdf-plugins.sh.tmpl`), and it explicitly exits 0 at `:32` when
  the binary is absent: `"asdf not available - skipping asdf plugin install"`. So the macOS asdf lane is
  a plugin installer with no installer beneath it.
- **chezmoi.** Chicken-and-egg; it is bootstrapped by `install.sh`, CI, or the prereq installer.

**Consequences for this harness.** The golden image must own Homebrew, Xcode CLT, chezmoi, and the brew
prereq list. And because asdf on macOS can only come from `zsh-dotfiles-prep`, **`mise` is the only
version manager `zsh-dotfiles` can bootstrap unaided** — which is why it is the harness default. The
`asdf` leg remains available behind a `--with-prereq-installer` flag that runs
`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer --debug` before apply, matching what upstream CI
(`zsh-dotfiles/.github/workflows/tests.yml:136-138`) and `smoke-test-docker.sh:202` already do. Note
that upstream's own smoke test therefore does **not** demonstrate standalone bootstrap either.

### Template data block (pinned tool versions)

`.chezmoi.yaml.tmpl:130-151`'s `data:` block pins exact versions the templates render against —
`myFzfVersion: 0.73.1`, `mySheldonVersion: 0.6.6`, `myAsdfVersion: v0.11.2`,
`myAsdfRubyVersion: 3.4.9`, `myAsdfGolangVersion: 1.25.1`, `myAsdfNeovimVersion: latest`,
`myfnmNodeVersion: 20.19.5`, plus a long tail of asdf-managed devops CLIs (kubectl, helm, k9s,
kubectx, opa, yq, mkcert, shellcheck, shfmt, github-cli, wtp). These only actually get installed
when the corresponding feature flag is `true` (ruby/fnm/k8s) or via the `asdf`/`mise` lane itself
(fzf, sheldon, neovim, tmux are unconditional). An assertion suite pinned to exact `--version`
strings for these tools is testing *this template's data block*, not "did chezmoi run correctly" —
keep version-pinned assertions loose (tool present + roughly-correct major version) unless the test
explicitly targets a version bump.

### OS/arch branching

The template system additionally branches on `.chezmoi.os` (`darwin`/`linux`) and `.chezmoi.arch`
per `zsh-dotfiles/CLAUDE.md:45`. On the macOS VM target this pins the harness to the `darwin` branch
of every `.tmpl` file — Linux-only branches (Ubuntu/CentOS/Debian package installs) are dead code on
the guest and out of scope for this harness's assertions.

## Pre-apply template validation: `chezmoi diff`, not `chezmoi verify`

`chezmoi verify` diffs the **destination** against the **target state** — it requires an apply to
already have happened, so it fails (non-error, just unusable) on a fresh VM before anything is
installed. Upstream's own smoke test therefore validates templates with `chezmoi diff --source=.`
instead, treating template-parse errors as the failure signal and expected file-content differences
as fine (`zsh-dotfiles/scripts/smoke-test-docker.sh:308-320`, comment: "chezmoi verify checks
destination=target, which fails before apply. Instead, use chezmoi diff to validate templates parse
correctly"). The harness must reuse this ordering: `chezmoi diff` pre-apply as a lint gate, never
`chezmoi verify` pre-apply.

## The Linux-coverage gap this repo exists to close

`zsh-dotfiles-prep` already has three Dockerfiles —
`Dockerfile-centos-9`, `Dockerfile-debian-12`, `Dockerfile-ubuntu-2204` — each building a
non-interactive test user (`tester`, passwordless sudo via `/etc/sudoers.d/tester`,
`Defaults:tester !authenticate`) and installing the prereqs. They are driven from
`zsh-dotfiles-prep/Makefile`'s `docker-buildx` / `docker-run-test{,-debug,-bash}` /
`docker-full-pipeline` targets — that Makefile has **no `smoke*` target**; the word does not occur in it.
`zsh-dotfiles/scripts/smoke-test-docker.sh` drives the equivalent for the downstream `zsh-dotfiles` repo,
on `ubuntu:24.04`, per `zsh-dotfiles/Dockerfile:12`.
**There is no macOS equivalent** — Docker cannot run a macOS guest, full stop. GitHub Actions does
run this repo's CI on `macos-14`/`macos-latest` hosted runners
(`zsh-dotfiles/.github/workflows/tests.yml`, matrix includes `os` and `version_manager`), but that
is remote, queued, GH-hosted infrastructure with no local, fast, disposable-VM iteration loop —
exactly what the Linux side gets for free from `docker run`. **That gap — a local, scriptable,
disposable macOS VM to run this same install-and-assert loop against, in seconds instead of a CI
queue — is this whole `macos-ci` repo's reason to exist.** Spec 08 designs the harness that fills it.

## Assertion vocabulary already in use upstream (reuse, don't reinvent)

- `zsh-dotfiles-prep/contrib/tests.sh` installs `pytest-testinfra` — the intended assertion
  framework for infra-level checks (package installed, file exists, service state) is
  **testinfra**, not a bespoke DSL.
- `zsh-dotfiles/scripts/smoke-test-docker.sh:388-411`'s zsh init check is the canonical
  "did this actually work" probe: `timeout 10s zsh -c 'source ~/.zshrc; [[ -n "$ZSH_VERSION" ]] &&
  echo ok; [[ -n "$PROMPT" || -n "$PS1" ]] && echo ok'` — i.e. zsh loads without erroring *and* a
  prompt variable is set. This is a stronger, more portable signal than grepping for a specific
  alias.
- `zsh-dotfiles/test_dotfiles.py` is **not** a model for this layer, and its tmux test is the clearest
  reason why. `TestDotfiles.test_pure_prompt` (`:246-270`) reads like a prompt-loaded check, but `:254`
  spawns `env zsh -f` — `-f` suppresses **every** rcfile — and `:265` then types `PS1='> '` by hand
  before `:270` asserts `">" in pane_contents`. It verifies that tmux echoes a string the test itself
  just sent; it exercises no line of `zsh-dotfiles`. It is also `@pytest.mark.skip`ped (`:245`), as are
  the alias-content tests, with `reason="These tests are meant to only run locally on laptop..."`.
  **Do not port any of it.** The upstream probe worth porting is `smoke-test-docker.sh:388-404`'s
  `source ~/.zshrc` check above, which loads the real rcfile.
- `zsh-dotfiles/scripts/smoke-test-docker.sh:326-350` (`run_build`) is the fullest existing
  "smoke" definition: `brew doctor` non-fatal-warn, `mise doctor` if present, `chezmoi init --apply`
  must exit 0, `post-install-chezmoi` with retry, then the zsh init check above. 08(c) builds the
  harness's assertion layer directly on top of this list rather than inventing a parallel one.

## Cross-references

- Harness design that consumes this spec: [08-dotfiles-test-harness.md](./08-dotfiles-test-harness.md)
- Tart primitives (`--dir` mounts, `tart ip`, ghcr.io images) the harness composes:
  [01-tart-core.md](./01-tart-core.md)
- Packer/Ansible-during-build precedent (not used here, but informs the golden-image approach):
  [02-packer-tart-builder.md](./02-packer-tart-builder.md)
