# Plan: macOS CI — Tart-Based Dotfiles Test Harness

## Task Description

Build a local, scriptable, disposable-VM test harness that installs `zsh-dotfiles` (chezmoi) into a
macOS virtual machine, asserts the install succeeded, and tears the VM down — giving macOS the same
fast local CI loop that `zsh-dotfiles-prep`'s three Linux Dockerfiles already give Linux. This closes
the one gap those two repos still have: no local, disposable macOS test environment (only remote,
queued GitHub Actions `macos-14` runners).

The harness is driven by a `Justfile` (`just up`, `just run`, `just doctor`, …) backed by an
installable `macos-ci` Python package, and every command emits machine-readable state so that both a
human and an *agent* can tell what worked and what did not.

## Objective

A developer can run `just run` against a working tree of `zsh-dotfiles` and get, within a few minutes,
a pass/fail verdict on whether the dotfiles bootstrap installs correctly on a clean macOS VM — without
touching a physical Mac, without waiting on a CI queue, and without leaving state behind.

An agent can read `artifacts/latest/verdict.json` and know, without parsing English, which phase failed
and what to do next.

## Problem Statement

- `zsh-dotfiles-prep`'s `Dockerfile-{centos-9,debian-12,ubuntu-2204}` and `zsh-dotfiles`'s
  `scripts/smoke-test-docker.sh` (running on `ubuntu:24.04`) give the Linux side of this stack a fast,
  local, disposable test loop via `docker run`. See
  [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#the-linux-coverage-gap-this-repo-exists-to-close).
- Docker cannot run a macOS guest. The only macOS CI today is GitHub's hosted `macos-14`/`macos-latest`
  runners (`zsh-dotfiles/.github/workflows/tests.yml`) — remote, queued, and not something a developer
  can iterate against locally while editing a chezmoi template.
- Two virtualization tools exist on macOS for building a local substitute: **Tart** and **UTM**.
  Neither has a Terraform/IaC story (G1), and UTM has no Packer builder (G3) and no disposable-mode
  path for a macOS guest (G5) — see the ADR at
  [10-tart-vs-utm-adr.md](macos-ci/10-tart-vs-utm-adr.md) for the full comparison.
- Building the harness naively (from-scratch VM per test, or a bespoke assertion DSL, or introducing
  Ansible where neither dotfiles repo uses it, G9) would be slow, divergent from what CI already
  validates, or unjustified complexity. Each of those traps and why they're avoided is documented in
  [08-dotfiles-test-harness.md](macos-ci/08-dotfiles-test-harness.md).
- A harness whose only interface is a bare shell script is operator-hostile and, worse, *agent*-hostile:
  there is nothing to run, nothing to unit-test, and no structured signal telling an autonomous loop
  whether the last action worked. The tooling surface is not a nicety; it is what makes the feedback
  cycle possible ([12-tooling-and-agent-loop.md](macos-ci/12-tooling-and-agent-loop.md)).

## Solution Approach

**Tart is primary; UTM is the interactive escape hatch** (house stance, full reasoning in
[10-tart-vs-utm-adr.md](macos-ci/10-tart-vs-utm-adr.md)). The harness is built entirely from Tart
primitives documented in [01-tart-core.md](macos-ci/01-tart-core.md) and
[02-packer-tart-builder.md](macos-ci/02-packer-tart-builder.md):

1. **Golden image, built once.** A Packer build using `packer-plugin-tart`
   ([02](macos-ci/02-packer-tart-builder.md)) clones a `ghcr.io/cirruslabs/macos-*-base` image and
   installs **exactly what `zsh-dotfiles` assumes but never installs itself**: Xcode CLT, Homebrew,
   chezmoi ≥ 2.20.0 (`zsh-dotfiles/.chezmoiversion:1`), and the brew prereq list from
   `smoke-test-docker.sh:142-157` — `wget curl retry go trash openssl@3 readline libyaml gmp autoconf
   tmux`. **`retry` is load-bearing**: the ported apply command is `retry -t 4 -- chezmoi init …`.
   The image is tagged/versioned so it isn't a snowflake on one machine.

   **`zsh-dotfiles-prep` is not part of the golden image.** See "The prep-installer boundary" below.

2. **Two image lanes, declared in `macos-versions.toml`.** The default lane clones a cirruslabs OCI
   base image (seconds, major versions only). A second lane builds from a pinned IPSW URL
   (`tart create --from-ipsw`) for exact point releases such as `15.6.1` or `26.1` — the approach
   `markkenny/macos-virtualisation` uses. Version selection is declarative, not a hardcoded template.

3. **Ephemeral clone per test run.** `tart clone <golden> <run-id>` ([01](macos-ci/01-tart-core.md))
   gives a byte-identical VM in seconds. The dotfiles working tree is mounted via `tart --dir`, not
   `git clone`d inside the guest, so local uncommitted changes under test are visible.

4. **Non-interactive chezmoi apply, defaulting to `mise`.** SSH into the clone **without a TTY** — this
   is the entire mechanism, already solved upstream (G11, see
   [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#the-chezmoi-template-contract-g11)):
   `stdinIsATTY` resolves false, every gated prompt takes its documented default, and the harness
   reuses upstream's exact non-TTY invocation (`zsh-dotfiles/scripts/smoke-test-docker.sh:361-365`)
   verbatim, pointed at the mounted source tree, with `--promptString version_manager=mise`.

5. **Assertions reused, not reinvented.** The pass/fail vocabulary
   ([08-dotfiles-test-harness.md §c](macos-ci/08-dotfiles-test-harness.md)) is drawn directly from
   `smoke-test-docker.sh`'s own checks (chezmoi apply exit code, post-install hook, zsh/prompt load
   probe) plus macOS-specific additions (login shell via `dscl`, `nvim --headless +qa`), run over SSH
   via `pytest-testinfra` to avoid inventing a second assertion DSL.

6. **Teardown**: `tart delete <run-id>` — instant and total because nothing mutated the golden image.

7. **A tooling surface built for a feedback cycle.** A `Justfile` (source of truth) plus a thin
   `Makefile` shim front an installable `src/macos_ci/` typer package. Each module is split into an
   I/O shell and a stdlib-only pure `_core` sibling, so the harness logic is unit-tested hermetically
   with `pytest-subprocess` and **never boots a VM in `just test`**. Every command writes structured
   state to `artifacts/<run-id>/`, with `verdict.json` as the single source of truth and exit codes
   (`0` ok / `2` issues / `3` unreachable / `4` usage) that let a caller distinguish "assertion failed"
   from "the VM never booted". Full detail in
   [12-tooling-and-agent-loop.md](macos-ci/12-tooling-and-agent-loop.md).

8. **Four verification tiers, all opt-in.** `vm` (testinfra over SSH), `pty` (pexpect over `ssh -tt`,
   for tab completion and keybindings), `gui` (VNC framebuffer screenshots, for what only an eye can
   judge), and `manual` (human y/n). All four are deselected by default so an agent run can never
   block on a human.

9. **No Ansible.** Rejected explicitly in
   [08-dotfiles-test-harness.md §e](macos-ci/08-dotfiles-test-harness.md); neither dotfiles repo uses
   it (G9), and introducing it here would test a different invocation shape than CI actually runs.

Full technical depth for every step above lives in the linked `specs/macos-ci/NN-*.md` files — this
plan is the executable summary, not a restatement.

### The prep-installer boundary

This is the load-bearing scoping decision, and it was verified against the source rather than assumed:

- `zsh-dotfiles` **installs mise itself** on macOS —
  `home/.chezmoiscripts/run_onchange_before_02-macos-install-mise.sh.tmpl` is gated on
  `(eq .version_manager "mise")` and runs `brew install mise`.
- `zsh-dotfiles` **cannot install asdf** on macOS. There is no `02-macos-install-asdf` script — only
  `-centos-` and `-ubuntu-` variants — and the macOS asdf-plugins script exits cleanly when the binary
  is absent. asdf on macOS comes *only* from `zsh-dotfiles-prep`, which installs it unconditionally
  (`bin/zsh-dotfiles-prereq-installer:578`, `:752`).
- `zsh-dotfiles` **never installs Homebrew or Xcode CLT**. `install.sh:206` hard-errors when brew is
  missing, and `xcode-select` appears nowhere in the repo.

Therefore: the golden image supplies Homebrew + Xcode CLT + chezmoi + brew prereqs, `zsh-dotfiles`
supplies everything above that, and **`mise` is the default `version_manager` because it is the only
one `zsh-dotfiles` can bootstrap unaided.** The `asdf` lane remains available as an explicitly-optional
matrix leg behind a `--with-prereq-installer` flag, which runs
`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer --debug` before apply — matching what
`zsh-dotfiles/.github/workflows/tests.yml:136-138` and `smoke-test-docker.sh:202` already do.

Two facts make this safe rather than wishful:

- `home/.chezmoiignore.tmpl:5` enforces mise/asdf mutual exclusion at the **file** level
  (`{{ if eq .version_manager "mise" }}` ignores the asdf scripts, `{{ else }}` ignores the mise ones),
  so selecting `mise` prevents the asdf scripts from ever rendering.
- `home/.chezmoi.yaml.tmpl:102-107` places the `version_manager` `promptString` **outside** the
  `if $interactive` block, while all seven feature bools sit inside it. So `--promptString
  version_manager=mise` works in a non-TTY run and **no upstream change is required**.

## Relevant Files

- `specs/macos-ci/00-overview.md` — orientation, file map, reading order.
- `specs/macos-ci/01-tart-core.md` — Tart install, CLI verbs, prebuilt images, `--dir` mounts,
  networking, headless keychain requirement (G8).
- `specs/macos-ci/02-packer-tart-builder.md` — full Packer builder field reference; golden-image
  build sketch.
- `specs/macos-ci/13-build-secrets.md` — how `HOMEBREW_GITHUB_API_TOKEN` reaches the build without
  reaching the artifact; why `HOMEBREW_GITHUB_PACKAGES_TOKEN`, an SSH key, `~/.gitconfig`, and
  `~/.ssh/config` are all unnecessary; and why deleting a secret from the guest does not erase it.
- `specs/macos-ci/03-tart-ci-and-orchard.md` — `cirrus run` local/CI parity; Orchard multi-host
  scale-out (not needed at current scope).
- `specs/macos-ci/04-tart-licensing-risk.md` — Fair Source tier table and accepted-risk sign-off
  (G4) — **read before provisioning any headless host**.
- `specs/macos-ci/05-utm-automation.md`, `06-utm-macos-guest.md`, `07-utm-settings-appendix.md` —
  UTM's automation surface, for the escape-hatch lane only; not required to build the Tart harness.
- `specs/macos-ci/08-dotfiles-test-harness.md` — the harness design this plan implements.
- `specs/macos-ci/09-dotfiles-under-test.md` — what's actually installed, the chezmoi non-interactive
  contract, and the assertion vocabulary to reuse.
- `specs/macos-ci/10-tart-vs-utm-adr.md` — the decision record this plan assumes.
- `specs/macos-ci/11-sources.md` — full source audit trail.
- `specs/macos-ci/12-tooling-and-agent-loop.md` — the Justfile/CLI surface, the pure/impure split, the
  four test tiers, the artifacts contract, and the `.claude/` agent loop.
- `/Users/bossjones/dev/bossjones/zsh-dotfiles/home/.chezmoi.yaml.tmpl` — the non-interactive prompt
  contract (read-only dependency; not owned by this repo).
- `/Users/bossjones/dev/bossjones/zsh-dotfiles/home/.chezmoiignore.tmpl` — the mise/asdf file-level
  mutual exclusion (read-only dependency).
- `/Users/bossjones/dev/bossjones/zsh-dotfiles/scripts/smoke-test-docker.sh` — the invocation and
  assertion shapes this harness ports to macOS (read-only dependency).
- `/Users/bossjones/dev/bossjones/zsh-dotfiles/hack/doctor/check_dev_environment.py` — an existing
  in-guest environment validator to reuse as an assertion rather than reimplement.
- `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer` — required only
  by the optional `asdf` matrix leg (read-only dependency).

### Existing Files To Extend

- `Justfile` — already exists with `default`, `link-check`, `link-check-verbose`, `link-check-fresh`
  (lychee, `GITHUB_TOKEN` from `gh auth token`). It stays the single source of truth; the harness
  recipes are **added** to it, not written into a new file. Keep `set shell := ["bash", "-uc"]`.
- `lychee.toml` — already configured with `include_fragments = true`, so internal `#anchor` links are
  validated. Do not weaken this; it has already caught broken anchors.
- `CLAUDE.md` — already documents the doc-site search-index oracle and the link-hygiene rule. Extend it
  with the harness commands once they exist.

### New Files

- `Makefile` — a thin passthrough shim (`make up` → `just up`); no recipe is written twice.
- `pyproject.toml` — the `macos-ci` package, its dev dependency group, pytest markers and `addopts`.
- `macos-versions.toml` — the declarative image matrix (OCI lane + pinned-IPSW lane).
- `src/macos_ci/` — typer CLI. Each module paired with a stdlib-only pure `_core` sibling:
  `cli.py`, `config.py`/`_config_core.py`, `tart.py`/`_tart_core.py`, `doctor.py`/`_doctor_core.py`,
  `harness.py`/`_harness_core.py`, `vm_debug.py`/`_triage_core.py`, `gui.py`/`_gui_core.py`,
  `artifacts.py`.
- `tests/unit/` — hermetic; `pytest-subprocess` fakes the `tart` binary. No VM, no network.
- `tests/integration/`, `tests/pty/`, `tests/gui/`, `tests/manual/` — the four opt-in tiers.
- `packer/tart-golden-image.pkr.hcl` — the OCI-lane Packer template
  ([02](macos-ci/02-packer-tart-builder.md)'s field reference), including the sensitive
  `homebrew_github_api_token` variable and the env-only secret injection from
  [13](macos-ci/13-build-secrets.md).
- `tests/fixtures/packer-sensitive/fixture.pkr.hcl` — a two-variable template, one `sensitive`, one
  plain. Built only to be probed by `packer inspect` from the claims ledger, proving masking is on
  *and* (via the plain control) that the probe would have shown the secret had it been off.
- `packer/ipsw/<version>.pkr.hcl` — the IPSW lane, `from_ipsw` + Setup Assistant `boot_command`.
- `harness/seed-config/chezmoi.yaml.tmpl` — the pre-seeded config file for Option A toggle-matrix runs
  ([08-dotfiles-test-harness.md §b](macos-ci/08-dotfiles-test-harness.md)).
- `.cirrus.yml` — wraps `just run` as a Cirrus CLI task so `cirrus run` reproduces the same flow
  locally that a future self-hosted CI runner would use ([03](macos-ci/03-tart-ci-and-orchard.md)).
- `artifacts/` — gitignored; the structured-state contract described in
  [12](macos-ci/12-tooling-and-agent-loop.md).

## Implementation Phases

### Phase 1: Foundation

Stand up the tooling skeleton and the golden image. Write `just doctor` first — it is the cheapest way
to discover that the host is wrong before anything expensive runs. Confirm a single manual `tart clone`
→ SSH → chezmoi-apply → `tart delete` cycle works end-to-end by hand, before any automation wraps it.

### Phase 2: Core Implementation

Script the full cycle behind `just run`, port the assertion vocabulary from `smoke-test-docker.sh` into
`pytest-testinfra` modules, implement the pre-seeded-config lever for the feature-toggle matrix, and
land the `artifacts/<run-id>/` contract including `verdict.json`.

### Phase 3: Integration & Polish

Add the `pty`/`gui`/`manual` tiers, rewrite the `.claude/` agent tooling for macOS, wrap the harness in
a `.cirrus.yml` task for `cirrus run` parity, add per-VM identity (`CM_computer_name`/`CM_hostname`) and
the `retry -t 4` resilience wrapper, and document the licensing guardrail (G4) as a checked precondition
before any headless host is provisioned.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Confirm host prerequisites

Verify the build host is Apple Silicon, macOS 13+ (Tart's floor) — macOS 15+ if using
`packer-plugin-tart` (its stated requirement, [02](macos-ci/02-packer-tart-builder.md)). Install
`tart` and `packer` (`brew install cirruslabs/cli/tart hashicorp/tap/packer`). Apply the Sequoia
local-network-permission workaround and unlock/create the login keychain for headless boots (G8,
[01](macos-ci/01-tart-core.md#headless-mode-and-the-macos-15-keychain-requirement-g8)) if the host is
macOS 15+.

This host now has `tart` 2.32.1, `just`, `uv`, `cirrus`, and `packer` 1.15.4. `packer` was the last
one missing, and installing it was the first acceptance test for Step 3 — now met. `just doctor` must
still report a missing `packer` on a host without it, so keep that path tested.

### 2. Read and sign off the licensing section

Read [04-tart-licensing-risk.md](macos-ci/04-tart-licensing-risk.md) in full and get explicit human
sign-off on the accepted-risk posture (G4) before provisioning any headless ("no connected display")
Tart host. Record the sign-off and the fleet-size ceiling (≤3 hosts / ≤100 combined cores) somewhere
durable (e.g. this repo's README or an issue). `just doctor` must *report* this ceiling; it must never
silently approve it.

### 3. Scaffold the package and write `doctor` (TDD, red first)

Create `pyproject.toml` (hatchling, `[project.scripts] macos-ci = "macos_ci.cli:app"`), then write the
failing unit test before the implementation, for each pure core:
`_gui_core.parse_vnc_url`, `_config_core.load`, `_tart_core.clone_argv`, `_doctor_core.check`.
Unit tests use `pytest-subprocess` to register a fake `tart` binary and assert on argv — no VM.

Then implement `doctor.py`: `shutil.which` + version probes, Apple Silicon check, macOS floor, login
keychain unlocked (G8), `$ZSH_DOTFILES` exists, free disk space. `just doctor --json` writes
`artifacts/<run-id>/doctor.json` and exits 2 on any miss.

### 4. Write the `Justfile` and the `Makefile` shim

Implement the recipe table from [12](macos-ci/12-tooling-and-agent-loop.md): `doctor`, `build`,
`build-ipsw`, `images`, `pull`, `up`, `down`, `destroy`, `recreate`, `run`, `apply`, `ssh`, `exec`,
`logs`, `debug`, `status`, `gui`, `vnc`, `shot`, `test`, `verify{,-pty,-gui,-manual}`, `matrix`,
`lint`, `fmt`, `typecheck`, `ci`, `prune`, `link-check`. Every non-trivial body delegates to
`uv run macos-ci <subcommand>`. `just run` gates on `just doctor` and always writes `verdict.json`,
even on crash. Add `Bash(just:*)` to `.claude/settings.json`'s `permissions.allow` — it is not
currently listed.

### 5. Author `macos-versions.toml` and the two image lanes

`packer/tart-golden-image.pkr.hcl` per the field reference in
[02-packer-tart-builder.md](macos-ci/02-packer-tart-builder.md): `vm_base_name` pointing at a
`ghcr.io/cirruslabs/macos-*-base` image, `cpu_count`/`memory_gb`/`disk_size_gb` sized for a Homebrew +
Xcode-CLT build, `headless = true`, `ssh_username`/`ssh_password` matching the default `admin`/`admin`
creds (G8). One idempotent `shell` provisioner installing Xcode CLT, Homebrew, chezmoi, and the brew
prereq list — **including `retry`**, and **not** `zsh-dotfiles-prep`.

`packer/ipsw/<version>.pkr.hcl` sets `from_ipsw = var.ipsw_url` and drives Setup Assistant with a
`boot_command`. Crib from `markkenny/macos-virtualisation/Packs/vanilla-26.1.pkr.hcl` — but note its
typo'd `<wai7s>` wait token as a cautionary tale, and validate every token.

### 6. Build and smoke-test the golden image

Run `just build`, then manually `tart clone` it once, boot it, and confirm `chezmoi --version` and
`brew doctor` succeed inside the clone before automating anything further.

### 6a. Inject the Homebrew token without letting it reach the artifact

Per [13](macos-ci/13-build-secrets.md). Declare `homebrew_github_api_token` as `sensitive = true` with
`default = env("HOMEBREW_GITHUB_API_TOKEN")`, and pass it — plus the `GIT_CONFIG_*` rewrite that sends
`zsh-dotfiles-prep/Brewfile`'s one `git@github.com:` tap over anonymous HTTPS — through the shell
provisioner's `environment_vars`, wrapped in `compact()` so an unset token omits the variable entirely.
Leave `use_env_var_file` at its default of `false`; setting it true writes the secret to a file **on the
guest**, which is the one thing this design exists to avoid.

Then prove it: `just verify-no-secrets <vm>`. Do not trust a canary you have not seen fail — plant the
token in a scratch file under the VM directory first and confirm the recipe exits `2`, exactly as the
ledger's masking claims are paired with a control. Do **not** add a cleanup provisioner that `rm`s a
secret from the guest; `rm` unlinks an inode without zeroing the blocks, so it would look like hygiene
while leaving the plaintext recoverable from the disk image.

### 7. Implement the harness (`up` / `run` / `destroy`)

`_harness_core.py` (pure) owns run-id generation, the artifact path layout, and `chezmoi_argv()` —
which reproduces `smoke-test-docker.sh:361-365` verbatim, parameterized on `version_manager` (default
`mise`) and `--source` pointed at the `tart --dir` mount.

`harness.py` (impure) composes the run from Tart primitives per
[08-dotfiles-test-harness.md §b](macos-ci/08-dotfiles-test-harness.md): `tart clone` → headless
`tart run` → poll `tart ip` → mount the dotfiles tree via `--dir` → SSH with **no `-t`** running
`chezmoi diff` (pre-apply lint; non-empty stderr fails the run) then the exact non-TTY apply command,
wrapped in `retry -t 4`, with `CM_computer_name`/`CM_hostname` set per run. Never mutate the golden
image; every run is its own clone.

### 8. Implement the pre-seeded-config lever (Option A)

For toggle-matrix runs, write a `~/.config/chezmoi/chezmoi.yaml` into the guest before `chezmoi init`
with the relevant `ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv` keys pre-set, per
[08-dotfiles-test-harness.md §b](macos-ci/08-dotfiles-test-harness.md). Do not attempt to reach these
via `--promptBool` in a non-TTY run — that lever does not exist (G11). `version_manager` is the sole
exception and is passed on the CLI.

### 9. Port the assertion layer (the `vm` tier)

Implement `tests/integration/` as `pytest-testinfra` modules covering the checklist in
[08-dotfiles-test-harness.md §c](macos-ci/08-dotfiles-test-harness.md): apply exit code, post-install
hook, zsh/prompt load probe, macOS login-shell check (`dscl`), Sheldon lock check, `nvim --headless
+qa`, `tmux -V`, PATH ordering, non-fatal `brew doctor`, and feature-toggle-field verification via
`chezmoi data`.

`conftest.py` follows `multipass-lab/clusters/*/tests/testinfra/conftest.py`: a session-scoped host
fixture that polls `host.run("true").rc == 0` until a deadline before yielding.

**mise assertions**: `chezmoi data` reports `version_manager: mise`; `mise --version` exits 0;
`zsh -lc 'which node'` does not resolve through `~/.asdf/shims/`. A dormant `~/.asdf` is tolerated —
it can only exist if the optional prereq installer ran. Also run `zsh-dotfiles`'s own
`hack/doctor/check_dev_environment.py` in-guest as a single assertion rather than reimplementing it.

### 10. Implement teardown

Always run `tart delete <run-id>` at the end of `just run`, with an opt-in `--keep-on-failure` flag
for local debugging, per [08-dotfiles-test-harness.md §d](macos-ci/08-dotfiles-test-harness.md).
`just prune` deletes orphan clones not tracked in `artifacts/`.

### 11. Add the `pty`, `gui`, and `manual` tiers

`pty`: `pexpect.spawn("ssh -tt …")`, send `\t`, assert on the byte stream — this is how tab completion,
keybindings, and prompt escape sequences get tested. This does **not** violate G11; the no-TTY rule
governs `chezmoi apply`, not verification.

`gui`: `_gui_core.parse_vnc_url` on `tart run --vnc-experimental` stdout → drive the framebuffer with
`asyncvnc` → write PNGs to `artifacts/<run-id>/screenshots/`. Capture happens at the hypervisor level,
so it sidesteps the macOS TCC/Screen-Recording gate that blocks `screencapture` over SSH.

`manual`: a `confirm()` fixture that calls `pytest.skip()` when `not sys.stdin.isatty()`, so even
`-m manual` degrades to skips rather than blocking an agent. Verify a bare `uv run pytest` deselects
all three tiers.

### 12. Implement `vm-debug` and rewrite the `.claude/` tooling for macOS

`_triage_core.py` (pure) holds the failure-signature table and `match(log_lines) -> [Finding]`,
unit-tested against fixture log text with no VM. `vm_debug.py` (impure) sweeps the guest's log sources
over `ssh` — shelling out to `ssh` rather than opening a socket from Python, which dodges the macOS
Local Network errno-65 block — and writes `logs/*.log` plus `verdict.json`, exiting 0/2/3/4.

The repo's existing `.claude/agents/log-researcher.md`, `.claude/commands/system-debug.md`, and both
`triage-*` skills are Multipass/journalctl/cloud-init tools inherited from another project; they
reference a `tools/system_debug.py` that does not exist here. Rewrite them per
[12-tooling-and-agent-loop.md](macos-ci/12-tooling-and-agent-loop.md), and add `/vm-status`.

### 13. Wrap in a Cirrus CLI task

Author `.cirrus.yml` per [03-tart-ci-and-orchard.md](macos-ci/03-tart-ci-and-orchard.md) so `cirrus
run` executes the same harness locally that a future self-hosted CI runner would use, and configure
`--artifacts-dir` extraction for logs/`chezmoi diff` output.

### 14. Dry-run the full matrix and validate the feedback loop

Run `just matrix` across `{sequoia} × {mise, asdf}`, confirming no cross-run state leaks (each run must
use its own clone). The `asdf` leg requires `--with-prereq-installer`; without it, it is *expected* to
fail, and that failure is a correct result to record rather than a bug to paper over.

Then break something on purpose — point `ZSH_DOTFILES` at a tree with a deliberately malformed template
— run `just run`, and confirm `verdict.json` names the phase (`chezmoi-diff`) and the cause without a
human reading a log.

## Testing Strategy

- **Hermetic unit tier (`just test`)**: the pure `_core` modules are stdlib-only and import nothing from
  their I/O siblings, so they test without a VM, a network, or `tart`. `pytest-subprocess` fakes the
  `tart` binary and the tests assert on constructed argv. This is where TDD actually happens, and it is
  what an agent runs by default. It cannot hang.
- **Golden-image smoke test**: one manual `tart clone` + `chezmoi --version` + `brew doctor` check
  after every Packer rebuild, before trusting the image for automated runs.
- **Per-run assertions (`-m vm`)**: the `pytest-testinfra` suite from Step 9 runs after every
  `chezmoi apply`, over the same SSH transport the harness already uses — no new transport or assertion
  DSL introduced.
- **Interactive-shell tier (`-m pty`)**: `pexpect` over `ssh -tt` covers what a non-TTY assertion
  cannot — tab completion, keybindings, prompt escape sequences.
- **Visual tier (`-m gui`)**: VNC framebuffer screenshots for what only an eye can judge — nerd-font
  glyph rendering, colorschemes, iTerm2. Screenshots land in `artifacts/<run-id>/screenshots/` where an
  agent can read them directly.
- **Template lint before apply**: `chezmoi diff --source=<mount>` must exit with empty stderr before
  `chezmoi init --apply` is attempted; a non-empty diff-stderr fails the run before any install step
  runs, per
  [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#pre-apply-template-validation-chezmoi-diff-not-chezmoi-verify).
- **Matrix coverage**: at minimum, one run per `version_manager` (mise default, asdf behind
  `--with-prereq-installer`) and one run with a pre-seeded toggle config, to exercise both the default
  lean-baseline path and the Option-A lever.
- **Regression check against upstream**: any assertion added here that upstream's
  `smoke-test-docker.sh` already defines must produce the same pass/fail verdict as the Linux run for
  the same dotfiles commit — a macOS-only failure with a Linux pass is a signal to investigate the
  harness, not just the dotfiles change.

## Acceptance Criteria

- `uv run pytest` (no flags) passes, runs only the hermetic unit tier, and boots no VM. The `vm`, `pty`,
  `gui`, and `manual` tiers are all deselected by default.
- Each `_core` module imports successfully in isolation, proving it depends on no I/O sibling.
- `just doctor --json` correctly reports `packer` as missing on a host without it, and exits 0 once it
  is installed.
- A Packer build produces a tagged, bootable golden Tart image with Xcode CLT, Homebrew, `retry`, and
  chezmoi ≥ 2.20.0 preinstalled and verified (`chezmoi --version` exits 0). It does **not** contain
  `zsh-dotfiles-prep`'s output.
- The build succeeds **both** with `HOMEBREW_GITHUB_API_TOKEN` set and with it unset, proving the token
  is an optimisation against GitHub's 60 req/hr cap and not a dependency ([13](macos-ci/13-build-secrets.md)).
- `just verify-no-secrets <vm>` exits 0 on the built image, and exits 2 when the token is deliberately
  planted under the VM directory. A canary that has never failed has not been tested.
- The token appears nowhere in `artifacts/latest/*.log`, including under `PACKER_LOG=1`.
- `just run` runs unattended end-to-end (doctor → clone → apply → assert → delete) against a local
  working tree of `zsh-dotfiles`, with no interactive prompts at any point, and exits non-zero on any
  assertion failure.
- The default run uses `version_manager=mise`; `chezmoi data` confirms it, `mise --version` exits 0,
  and no asdf shim precedes mise on the login-shell `PATH`.
- The non-interactive chezmoi run leaves the seven optional toolchain flags (`ruby`/`pyenv`/`nodejs`/
  `k8s`/`cuda`/`fnm`/`opencv`) `false` in the default (non-seeded) case, matching the documented
  lean-baseline default (G11).
- The pre-seeded-config lever (Option A) successfully flips at least one toggle (e.g. `ruby=true`) in a
  dedicated run and the assertion layer detects the resulting installed toolchain.
- `artifacts/latest/verdict.json` exists after every `just run`, including crashed and failed ones, and
  names the failing phase. Exit codes distinguish `2` (issues found) from `3` (VM unreachable).
- `tart delete` runs after every test invocation, including failed ones (unless `--keep-on-failure` is
  passed), and `tart list` shows no leftover clones after a full matrix run.
- `make doctor` and `make test` produce identical results to their `just` counterparts, and the
  `Makefile` contains no recipe logic of its own.
- `cirrus run` (via `.cirrus.yml`) reproduces the same pass/fail result as running `just run` directly.
- No headless Tart host is provisioned without an explicit, recorded licensing sign-off (G4).

## Validation Commands

Execute these commands to validate the task is complete:

```bash
# Hermetic — no VM, no network. Must pass before anything else is trusted.
uv run pytest                                    # unit tier only
uv run ruff check . && uv run ruff format --check .
uv run basedpyright src/
uv run python -c "import macos_ci._tart_core, macos_ci._doctor_core, macos_ci._gui_core"

# Every host prereq is now installed, so the doctor must be clean.
just doctor --json | jq '.[] | select(.ok == false)'   # => expect no rows
just doctor                                            # => exit 0

# Confirm Tart + Packer are installed and the plugin is initialized.
tart --version
packer --version
packer init packer/tart-golden-image.pkr.hcl

# Build and smoke-test the golden image.
just build
tart clone dotfiles-golden smoke-check
tart run smoke-check --no-graphics &
ssh admin@$(tart ip smoke-check) 'chezmoi --version && brew doctor'
tart delete smoke-check

# Run the harness against a local zsh-dotfiles checkout.
ZSH_DOTFILES=/Users/bossjones/dev/bossjones/zsh-dotfiles just run
jq '.ok, .phase, .cause' artifacts/latest/verdict.json

# The opt-in tiers.
just verify-pty                                  # tab completion over a real PTY
just verify-gui && ls artifacts/latest/screenshots/
just verify-manual                               # the only recipe that may prompt

# make is a shim, not a fork.
make doctor && make test

# Run the same flow through Cirrus CLI for local/CI parity.
cirrus run --artifacts-dir artifacts

# Confirm no leftover clones after a run.
tart list
```

## Notes

- Every linked `specs/macos-ci/NN-*.md` file was produced as a **docs-only** research pass: no VM was
  booted, no `brew install` was run, and no host was mutated to produce them. Anything marked
  `<!-- UNVERIFIED -->` in a linked file is a composed example, not a source-quoted fact — treat it as
  needing confirmation during Phase 1, not as settled. This plan's *dotfiles* findings (the prep
  boundary, the mise/asdf split, the prompt contract) are the exception: they were read directly from
  the source files cited inline.
- The non-interactive chezmoi mechanism (G11) is **already solved upstream** — do not re-investigate
  it during implementation; port the exact invocation from `smoke-test-docker.sh` as documented in
  [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#the-chezmoi-template-contract-g11).
- **No upstream change to `zsh-dotfiles` or `zsh-dotfiles-prep` is required.** `mise` is selected
  per-run on the CLI. The upstream specs `migrate-asdf-to-mise.md` and
  `fix-smoke-mise-version-manager.md` indicate that migration is already in flight there; this harness
  will validate it when it lands rather than blocking on it.
- `tart run --vnc-experimental` is flagged experimental by Tart itself. Treat the `gui` tier as
  `<!-- UNVERIFIED -->` until Phase 1 exercises it against a real VM; `vncdotool` is the fallback if
  `asyncvnc` misbehaves.
- New dependencies: `uv add --dev pytest-testinfra asyncvnc pexpect pytest-json-report`. Everything
  else — `pytest-sugar`, `pytest-mock`, `pytest-timeout`, `pytest-retry`, `pytest-subprocess`,
  `pytest-skip-slow`, `ruff`, `basedpyright` — matches `zsh-dotfiles/pyproject.toml`'s existing stack.
- Orchard (multi-host orchestration, [03](macos-ci/03-tart-ci-and-orchard.md)) and UTM (interactive
  escape hatch, [05](macos-ci/05-utm-automation.md)–[07](macos-ci/07-utm-settings-appendix.md)) are
  intentionally out of scope for this plan's phases — they are documented for context and future
  scale-out, not because Phase 1-3 requires them.
- Ansible was evaluated and explicitly rejected for this harness
  ([08-dotfiles-test-harness.md §e](macos-ci/08-dotfiles-test-harness.md)); do not reintroduce it
  without re-litigating that decision against the same burden-of-proof standard.
- The licensing accepted-risk section (G4) requires a human decision, not an engineering one — flag it
  for sign-off rather than proceeding silently if this plan is handed to an autonomous build step.
