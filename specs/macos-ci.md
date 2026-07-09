# Plan: macOS CI — Tart-Based Dotfiles Test Harness

## Task Description

Build a local, scriptable, disposable-VM test harness that installs `zsh-dotfiles` (chezmoi) and
`zsh-dotfiles-prep` (Homebrew/Xcode-CLT bootstrap) into a macOS virtual machine, asserts the install
succeeded, and tears the VM down — giving macOS the same fast local CI loop that `zsh-dotfiles-prep`'s
three Linux Dockerfiles already give Linux. This closes the one gap those two repos still have: no
local, disposable macOS test environment (only remote, queued GitHub Actions `macos-14` runners).

## Objective

A developer can run one command against a working tree of `zsh-dotfiles` and get, within a few
minutes, a pass/fail verdict on whether the dotfiles bootstrap installs correctly on a clean macOS VM
— without touching a physical Mac, without waiting on a CI queue, and without leaving state behind.

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

## Solution Approach

**Tart is primary; UTM is the interactive escape hatch** (house stance, full reasoning in
[10-tart-vs-utm-adr.md](macos-ci/10-tart-vs-utm-adr.md)). The harness is built entirely from Tart
primitives documented in [01-tart-core.md](macos-ci/01-tart-core.md) and
[02-packer-tart-builder.md](macos-ci/02-packer-tart-builder.md):

1. **Golden image, built once.** A Packer build using `packer-plugin-tart`
   ([02](macos-ci/02-packer-tart-builder.md)) runs `zsh-dotfiles-prep`'s prereq installer to completion
   inside a cloned `ghcr.io/cirruslabs/macos-*` base image — Xcode CLT, Homebrew, asdf, chezmoi
   ≥ 2.20.0 preinstalled — and is tagged/versioned so it isn't a snowflake on one machine.
2. **Ephemeral clone per test run.** `tart clone <golden> <run-id>` ([01](macos-ci/01-tart-core.md))
   gives a byte-identical VM in seconds. The dotfiles working tree is mounted via `tart --dir`, not
   `git clone`d inside the guest, so local uncommitted changes under test are visible.
3. **Non-interactive chezmoi apply.** SSH into the clone **without a TTY** — this is the entire
   mechanism, already solved upstream (G11, see
   [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#the-chezmoi-template-contract-g11)):
   `stdinIsATTY` resolves false, every gated prompt takes its documented default, and the harness
   reuses upstream's exact non-TTY invocation
   (`zsh-dotfiles/scripts/smoke-test-docker.sh:361-365`) verbatim, pointed at the mounted source tree.
4. **Assertions reused, not reinvented.** The pass/fail vocabulary
   ([08-dotfiles-test-harness.md §c](macos-ci/08-dotfiles-test-harness.md)) is drawn directly from
   `smoke-test-docker.sh`'s own checks (chezmoi apply exit code, post-install hook, zsh/prompt load
   probe) plus macOS-specific additions (login shell via `dscl`, `nvim --headless +qa`), run over SSH
   via `pytest-testinfra` to avoid inventing a second assertion DSL.
5. **Teardown**: `tart delete <run-id>` — instant and total because nothing mutated the golden image.
6. **No Ansible.** Rejected explicitly in
   [08-dotfiles-test-harness.md §e](macos-ci/08-dotfiles-test-harness.md); neither dotfiles repo uses
   it (G9), and introducing it here would test a different invocation shape than CI actually runs.

Full technical depth for every step above lives in the linked `specs/macos-ci/NN-*.md` files — this
plan is the executable summary, not a restatement.

## Relevant Files

- `specs/macos-ci/00-overview.md` — orientation, file map, reading order.
- `specs/macos-ci/01-tart-core.md` — Tart install, CLI verbs, prebuilt images, `--dir` mounts,
  networking, headless keychain requirement (G8).
- `specs/macos-ci/02-packer-tart-builder.md` — full Packer builder field reference; golden-image
  build sketch.
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
- `/Users/bossjones/dev/bossjones/zsh-dotfiles/home/.chezmoi.yaml.tmpl` — the non-interactive prompt
  contract (read-only dependency; not owned by this repo).
- `/Users/bossjones/dev/bossjones/zsh-dotfiles/scripts/smoke-test-docker.sh` — the invocation and
  assertion shapes this harness ports to macOS (read-only dependency).
- `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer` — the installer
  the golden-image build runs (read-only dependency).

### New Files

- `packer/tart-golden-image.pkr.hcl` — the Packer template building the golden Tart VM
  ([02](macos-ci/02-packer-tart-builder.md)'s field reference).
- `packer/http/` — any autoinstall/boot payload the `boot_command`/`http_directory` fields need.
- `harness/run-test.sh` — orchestrates `tart clone` → boot → SSH non-TTY chezmoi apply → assertions →
  `tart delete` for one test run.
- `harness/assertions/` — `pytest-testinfra` test modules implementing the checks from
  [08-dotfiles-test-harness.md §c](macos-ci/08-dotfiles-test-harness.md).
- `harness/seed-config/chezmoi.yaml` (template) — the pre-seeded config file for Option A toggle-matrix
  runs ([08-dotfiles-test-harness.md §b](macos-ci/08-dotfiles-test-harness.md)).
- `.cirrus.yml` — wraps `harness/run-test.sh` as a Cirrus CLI task so `cirrus run` reproduces the same
  flow locally that a future self-hosted CI runner would use ([03](macos-ci/03-tart-ci-and-orchard.md)).

## Implementation Phases

### Phase 1: Foundation

Stand up the golden image and confirm a single manual `tart clone` → SSH → chezmoi-apply → `tart
delete` cycle works end-to-end by hand, before any automation wraps it.

### Phase 2: Core Implementation

Script the full cycle (`harness/run-test.sh`), port the assertion vocabulary from
`smoke-test-docker.sh` into `pytest-testinfra` modules, and implement the pre-seeded-config lever for
the feature-toggle matrix.

### Phase 3: Integration & Polish

Wrap the harness in a `.cirrus.yml` task for `cirrus run` parity, add per-VM identity
(`CM_computer_name`/`CM_hostname`) and the `retry -t 4` resilience wrapper, and document the licensing
guardrail (G4) as a checked precondition before any headless host is provisioned.

## Step by Step Tasks

### 1. Confirm host prerequisites

Verify the build host is Apple Silicon, macOS 13+ (Tart's floor) — macOS 15+ if using
`packer-plugin-tart` (its stated requirement, [02](macos-ci/02-packer-tart-builder.md)). Install
`tart` and `packer` (`brew install cirruslabs/cli/tart`). Apply the Sequoia local-network-permission
workaround and unlock/create the login keychain for headless boots (G8,
[01](macos-ci/01-tart-core.md#headless-mode-and-the-macos-15-keychain-requirement-g8)) if the host is
macOS 15+.

### 2. Read and sign off the licensing section

Read [04-tart-licensing-risk.md](macos-ci/04-tart-licensing-risk.md) in full and get explicit human
sign-off on the accepted-risk posture (G4) before provisioning any headless ("no connected display")
Tart host. Record the sign-off and the fleet-size ceiling (≤3 hosts / ≤100 combined cores) somewhere
durable (e.g. this repo's README or an issue).

### 3. Write the Packer golden-image template

Author `packer/tart-golden-image.pkr.hcl` per the field reference in
[02-packer-tart-builder.md](macos-ci/02-packer-tart-builder.md): `vm_base_name` pointing at a
`ghcr.io/cirruslabs/macos-*-base` image, `cpu_count`/`memory_gb`/`disk_size_gb` sized for a Homebrew +
Xcode-CLT build, `headless = true`, `ssh_username`/`ssh_password` matching the default `admin`/`admin`
creds (G8). Add a `shell` provisioner that runs
`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer --debug` to completion.

### 4. Build and smoke-test the golden image

Run `packer build`, then manually `tart clone` it once, boot it, and confirm `chezmoi --version` and
`brew doctor` succeed inside the clone before automating anything further.

### 5. Implement `harness/run-test.sh`

Compose the run from Tart primitives per
[08-dotfiles-test-harness.md §b](macos-ci/08-dotfiles-test-harness.md): `tart clone` → headless
`tart run` → poll `tart ip` → mount the dotfiles tree via `--dir` → SSH with **no `-t`** running
`chezmoi diff` (pre-apply lint) then the exact non-TTY apply command from
`smoke-test-docker.sh:361-365`, wrapped in `retry -t 4`, with `CM_computer_name`/`CM_hostname` set
per run.

### 6. Implement the pre-seeded-config lever (Option A)

For toggle-matrix runs, write a `~/.config/chezmoi/chezmoi.yaml` into the guest before `chezmoi init`
with the relevant `ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv` keys pre-set, per
[08-dotfiles-test-harness.md §b](macos-ci/08-dotfiles-test-harness.md). Do not attempt to reach these
via `--promptBool` in a non-TTY run — that lever does not exist (G11).

### 7. Port the assertion layer

Implement `harness/assertions/` as `pytest-testinfra` modules covering the checklist in
[08-dotfiles-test-harness.md §c](macos-ci/08-dotfiles-test-harness.md): apply exit code, post-install
hook, zsh/prompt load probe, macOS login-shell check (`dscl`), Sheldon lock check, `nvim --headless
+qa`, `tmux -V`, PATH ordering, non-fatal `brew doctor`, and feature-toggle-field verification via
`chezmoi data`.

### 8. Implement teardown

Always run `tart delete <run-id>` at the end of `run-test.sh`, with an opt-in `--keep-on-failure` flag
for local debugging, per [08-dotfiles-test-harness.md §d](macos-ci/08-dotfiles-test-harness.md).

### 9. Wrap in a Cirrus CLI task

Author `.cirrus.yml` per [03-tart-ci-and-orchard.md](macos-ci/03-tart-ci-and-orchard.md) so `cirrus
run` executes the same harness locally that a future self-hosted CI runner would use, and configure
`--artifacts-dir` extraction for logs/`chezmoi diff` output.

### 10. Dry-run the full matrix

Run the harness once per `version_manager` value (`asdf`, `mise`) and once with a pre-seeded
toggle-matrix config, confirming the mutual-exclusion invariant
([09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#the-version_manager-selector-asdf--mise))
holds and no cross-run state leaks (each run must use its own clone).

## Testing Strategy

- **Golden-image smoke test**: one manual `tart clone` + `chezmoi --version` + `brew doctor` check
  after every Packer rebuild, before trusting the image for automated runs.
- **Per-run assertions**: the `pytest-testinfra` suite from Step 7 runs after every `chezmoi apply`,
  over the same SSH transport the harness already uses — no new transport or assertion DSL introduced.
- **Template lint before apply**: `chezmoi diff --source=<mount>` must exit with empty stderr before
  `chezmoi init --apply` is attempted; a non-empty diff-stderr fails the run before any install step
  runs, per
  [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#pre-apply-template-validation-chezmoi-diff-not-chezmoi-verify).
- **Matrix coverage**: at minimum, one run per `version_manager` (asdf/mise) and one run with a
  pre-seeded toggle config, to exercise both the default lean-baseline path and the Option-A lever.
- **Regression check against upstream**: any assertion added here that upstream's
  `smoke-test-docker.sh` already defines must produce the same pass/fail verdict as the Linux run for
  the same dotfiles commit — a macOS-only failure with a Linux pass is a signal to investigate the
  harness, not just the dotfiles change.

## Acceptance Criteria

- A Packer build produces a tagged, bootable golden Tart image with Xcode CLT, Homebrew, asdf, and
  chezmoi ≥ 2.20.0 preinstalled and verified (`chezmoi --version` exits 0).
- `harness/run-test.sh` runs unattended end-to-end (clone → apply → assert → delete) against a local
  working tree of `zsh-dotfiles`, with no interactive prompts at any point, and exits non-zero on any
  assertion failure.
- The non-interactive chezmoi run leaves the seven optional toolchain flags (`ruby`/`pyenv`/`nodejs`/
  `k8s`/`cuda`/`fnm`/`opencv`) `false` in the default (non-seeded) case, matching the documented
  lean-baseline default (G11).
- The pre-seeded-config lever (Option A) successfully flips at least one toggle (e.g. `ruby=true`) in a
  dedicated run and the assertion layer detects the resulting installed toolchain.
- `tart delete` runs after every test invocation, including failed ones (unless `--keep-on-failure` is
  passed), and `tart list` shows no leftover clones after a full matrix run.
- `cirrus run` (via `.cirrus.yml`) reproduces the same pass/fail result as running `harness/run-test.sh`
  directly.
- No headless Tart host is provisioned without an explicit, recorded licensing sign-off (G4).

## Validation Commands

```bash
# Confirm Tart + Packer are installed and the plugin is initialized
tart --version
packer --version
packer init packer/tart-golden-image.pkr.hcl

# Build and smoke-test the golden image
packer build packer/tart-golden-image.pkr.hcl
tart clone dotfiles-golden smoke-check
tart run smoke-check --no-graphics &
ssh admin@$(tart ip smoke-check) 'chezmoi --version && brew doctor'
tart delete smoke-check

# Run the harness against a local zsh-dotfiles checkout
harness/run-test.sh --source /Users/bossjones/dev/bossjones/zsh-dotfiles

# Run the same flow through Cirrus CLI for local/CI parity
cirrus run --artifacts-dir artifacts

# Confirm no leftover clones after a run
tart list
```

## Notes

- This plan and every linked `specs/macos-ci/NN-*.md` file was produced as a **docs-only** research
  pass: no VM was booted, no `brew install` was run, and no host was mutated to produce them. Anything
  marked `<!-- UNVERIFIED -->` in a linked file is a composed example, not a source-quoted fact —
  treat it as needing confirmation during Phase 1, not as settled.
- The non-interactive chezmoi mechanism (G11) is **already solved upstream** — do not re-investigate
  it during implementation; port the exact invocation from `smoke-test-docker.sh` as documented in
  [09-dotfiles-under-test.md](macos-ci/09-dotfiles-under-test.md#the-chezmoi-template-contract-g11).
- Orchard (multi-host orchestration, [03](macos-ci/03-tart-ci-and-orchard.md)) and UTM (interactive
  escape hatch, [05](macos-ci/05-utm-automation.md)–[07](macos-ci/07-utm-settings-appendix.md)) are
  intentionally out of scope for this plan's phases — they are documented for context and future
  scale-out, not because Phase 1-3 requires them.
- Ansible was evaluated and explicitly rejected for this harness
  ([08-dotfiles-test-harness.md §e](macos-ci/08-dotfiles-test-harness.md)); do not reintroduce it
  without re-litigating that decision against the same burden-of-proof standard.
- The licensing accepted-risk section (G4) requires a human decision, not an engineering one — flag it
  for sign-off rather than proceeding silently if this plan is handed to an autonomous build step.
