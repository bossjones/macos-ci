# Justfile Reference

Complete reference for every `just` recipe in this project.

## Quick Reference

| Group | Recipe | Purpose |
|-------|--------|---------|
| **Truth Gate** | `link-check` | Check all markdown links using lychee |
| | `link-check-verbose` | Check links with verbose output |
| | `link-check-fresh` | Check links, bypassing 7-day cache |
| | `verify-claims` | Re-execute evidence behind every spec claim |
| | `verify-claims-json` | Re-execute claims, emit machine-readable JSON |
| | `unverified-count` | Count `<!-- UNVERIFIED -->` markers in specs |
| | `check` | **The full truth gate**: link-check + verify-claims + unverified-count |
| **Build** | `build-golden` | Packer build of golden Tart image |
| | `build-ipsw` | Build from pinned IPSW (placeholder) |
| | `build` | Alias for `build-golden` |
| | `verify-no-secrets` | Leak canary: assert token absent from VM artifact |
| **Lifecycle** | `doctor` | Preflight checks |
| | `up` | Clone, start VM, bootstrap SSH |
| | `down` (alias: `stop`) | Stop VM, keep clone |
| | `destroy` | Delete VM clone |
| | `recreate` | Destroy and up |
| | `run` | Full integration: doctor → up → diff → apply → verify → destroy |
| | `apply` | Fast iteration: chezmoi apply on live VM |
| | `prune` | Delete orphan clones |
| **Images** | `images` | Print `macos-versions.toml` and `tart list` |
| | `pull` | `tart pull` the OCI ref for IMAGE (placeholder) |
| **Inspection** | `ssh` | Interactive shell into VM |
| | `exec` | One-shot remote command in VM |
| | `logs` | Sweep guest logs into artifacts |
| | `debug` | Triage: run vm-debug sweep |
| | `status` | Print `tart list` and parsed state.json |
| | `gui` | `tart run` with windowed display |
| | `vnc` | VNC framebuffer connect (unimplemented) |
| | `shot` | Framebuffer screenshot (unimplemented) |
| **Testing** | `test` | Hermetic unit tests (no VM) |
| | `verify` | testinfra assertions over SSH (`-m vm`) |
| | `verify-pty` | pexpect over SSH with PTY (`-m pty`) |
| | `verify-gui` | VNC screenshots (`-m gui`) |
| | `verify-manual` | Human-interactive tests (`-m manual`) |
| | `matrix` | Cross-product: image × version-manager |
| **Quality** | `lint` | `ruff check .` |
| | `fmt` | `ruff format .` |
| | `typecheck` | `basedpyright` |
| | `ci` | `cirrus run` for local/CI parity |

---

## Justfile Variables

These variables are used throughout recipes and can be overridden via environment variables:

| Variable | Default | Override Env Var | Purpose |
|----------|---------|------------------|---------|
| `vm` | `dotfiles-test` | `MACOS_CI_VM` | VM name for lifecycle recipes |
| `image` | `sequoia` | `MACOS_CI_IMAGE` | macOS image version to test |
| `dotfiles` | `../zsh-dotfiles` (rel. to Justfile) | `ZSH_DOTFILES` | Path to zsh-dotfiles repo to test |
| `vm_user` | `admin` | (none) | Guest SSH user (fixed, do not override) |
| `vmgr` | `mise` | `MACOS_CI_VERSION_MANAGER` | Version manager to configure (mise or asdf) |
| `ssh_opts` | (see below) | (none) | SSH options for key-based auth |

**SSH Options** (fixed):
```
-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=8 -o BatchMode=yes
```

---

## Truth Gate (Spec Verification)

These recipes implement the claims ledger verification workflow — every assertion in `specs/**/*.md` is paired with evidence, and these recipes re-execute the evidence.

### link-check

**Invocation**: `just link-check`

**Description**: Check all links in markdown files using lychee.

**Implementation**: Runs `lychee --config lychee.toml '**/*.md'`

**Environment**: `GITHUB_TOKEN` is populated from `gh auth token` if available (lychee uses GitHub API instead of unauthenticated scraping, avoiding rate-limit false positives).

---

### link-check-verbose

**Invocation**: `just link-check-verbose`

**Description**: Check all links with verbose output (debug mode).

**Implementation**: Runs `lychee --config lychee.toml --verbose debug '**/*.md'`

**Use When**: Investigating why `link-check` failed.

---

### link-check-fresh

**Invocation**: `just link-check-fresh`

**Description**: Check all links, bypassing the 7-day lychee cache.

**Implementation**: Runs `lychee --config lychee.toml --max-cache-age 0s '**/*.md'`

**Use When**: After fixing a broken link, to verify the fix before running `check`.

---

### verify-claims

**Invocation**: `just verify-claims`

**Description**: Re-execute the evidence behind every claim in `.team/claims.jsonl`.

**Implementation**: Runs `uv run tools/verify_claims.py`

**Exit Codes**:
- `0` — All claims verified
- `2` — One or more claims failed
- `3` — Evidence unreachable (network, missing binary)
- `4` — Usage error

**Evidence Types**:
- `file-contains` — Text appears in a file
- `file-line` — Text appears at a specific line
- `cli-help` — Command help text (limited; use `doc-contains` for backend questions)
- `doc-contains` — Text appears on a doc page (fetches via `curl`, searches index)
- `doc-index` — A doc page exists in the search index
- `absent` — Text does NOT appear in a file

---

### verify-claims-json

**Invocation**: `just verify-claims-json`

**Description**: Re-execute claims and emit machine-readable JSON (for agent consumption).

**Implementation**: Runs `uv run tools/verify_claims.py --json`

**Output**: JSON-serialized results (same exit codes as `verify-claims`).

---

### unverified-count

**Invocation**: `just unverified-count`

**Description**: Count `<!-- UNVERIFIED -->` markers in spec files.

**Implementation**: Greps for `UNVERIFIED` in `specs/**/*.md` and counts occurrences.

**Purpose**: An "honesty budget" — specs should minimize unverified assertions. The count should fall as claims get verified, not because markers get deleted.

---

### check

**Invocation**: `just check`

**Description**: The full truth gate: `link-check` + `verify-claims` + `unverified-count`.

**Implementation**: Runs all three in sequence; fails if any step fails.

**Purpose**: Gate that everything an agent must pass before a spec is trustworthy.

---

## Build (Image Construction)

These recipes manage Packer builds and image validation.

### build-golden

**Invocation**: `just build-golden`

**Description**: Packer build of the golden Tart image (`packer/tart-golden-image.pkr.hcl`).

**Implementation**:
1. Verify `packer/tart-golden-image.pkr.hcl` exists (exit 4 if not)
2. Set `HOMEBREW_GITHUB_API_TOKEN` from environment or `gh auth token` (optimization only; build succeeds without it)
3. Run `packer build packer/tart-golden-image.pkr.hcl`

**Prerequisites**:
- Packer installed
- Tart installed
- `packer/tart-golden-image.pkr.hcl` present (generated, not checked in)

**Output**: A local Tart VM named `dotfiles-golden` (with optional per-image suffix for future multi-image support).

**Duration**: ~2+ hours (dominated by 23.7GB base OCI image pull on first run; subsequent runs clone from local cache in minutes).

**Notes**:
- The template file is deliberately unauthorized (packer build/init not in allowed scope), so the recipe fails loudly if missing rather than letting packer emit a confusing error.
- See `specs/macos-ci/13-build-secrets.md` and `OQ-04` for secret handling.

---

### build-ipsw

**Invocation**: `just build-ipsw VERSION`

**Parameters**:
- `VERSION` — macOS version to build from (e.g., `15.0`)

**Description**: Packer build from a pinned IPSW (macOS installer).

**Status**: ⚠️ Placeholder — implementation not yet landed.

**Implementation** (planned): `uv run macos-ci build-ipsw {{VERSION}}`

---

### build

**Invocation**: `just build`

**Description**: Alias for `build-golden`.

**Implementation**: `alias build := build-golden`

**Purpose**: Shorthand for spec-12-shaped recipe naming.

---

### verify-no-secrets

**Invocation**: `just verify-no-secrets vm=VMNAME`

**Parameters**:
- `vm` — VM name to scan (no default; must be specified)

**Description**: Leak canary: assert the Homebrew token appears nowhere in a built VM's artifact.

**Implementation**:
1. Resolve `HOMEBREW_GITHUB_API_TOKEN` from environment or `gh auth token`
2. If no token present, exit 0 (nothing to search for)
3. If `~/.tart/vms/{{vm}}/` does not exist, exit 4 (usage error)
4. Recursively search for token string in VM directory (binary-safe search)
5. If found, exit 2 (leak detected); if not found, exit 0 (clean)

**Purpose**: Verify that SSH provisioner environment variables (which carry the token) never leaked into the disk image.

**Note**: Deletion of a secret from the guest does not erase it — `rm` unlinks an inode but does not zero blocks. Secrets survive in the disk image and can be recovered with `strings`. The correct pattern is to pass secrets through environment variables only, never write them to files.

---

## Lifecycle (VM Management)

These recipes manage the harness workflow: bring up a VM, configure it, test it, tear it down.

### doctor

**Invocation**: `just doctor [ARGS...]`

**Parameters**:
- `ARGS` — Optional arguments forwarded to the CLI (e.g., `--json`)

**Description**: Preflight every requirement. Exit 2 if anything is missing.

**Implementation**: `uv run macos-ci doctor {{ARGS}}`

**CLI Reference**: See [`cli-reference.md#doctor`](./cli-reference.md#doctor)

**Common Invocations**:
```bash
just doctor           # Human-readable output
just doctor --json    # JSON output (for agents)
```

---

### up

**Invocation**: `just up`

**Parameters**: Uses Justfile variables `{{vm}}`, `{{image}}`, `{{dotfiles}}`

**Description**: Clone the golden image, start a headless Tart VM, bootstrap SSH, configure shell environment.

Writes `artifacts/<run-id>/state.json` with VM metadata.

**Implementation**: `uv run macos-ci harness up --vm {{vm}} --image {{image}} --dotfiles {{dotfiles}}`

**CLI Reference**: See [`cli-reference.md#up`](./cli-reference.md#up)

**Environment Overrides**:
```bash
MACOS_CI_VM=my-test just up
MACOS_CI_IMAGE=ventura just up
ZSH_DOTFILES=/path/to/dotfiles just up
```

---

### down

**Invocation**: `just down` (or `just stop` — alias)

**Parameters**: Uses Justfile variable `{{vm}}`

**Description**: Stop the VM, leave the clone on disk for re-use or inspection.

**Implementation**: `uv run macos-ci harness down --vm {{vm}}`

**CLI Reference**: See [`cli-reference.md#down`](./cli-reference.md#down)

**Note**: Does not delete the VM — use `destroy` for that.

---

### stop

**Invocation**: `just stop`

**Description**: Alias for `down`.

**Implementation**: `alias stop := down`

---

### destroy

**Invocation**: `just destroy`

**Parameters**: Uses Justfile variable `{{vm}}`

**Description**: Delete the VM clone entirely.

**Implementation**: `uv run macos-ci harness destroy --vm {{vm}}`

**CLI Reference**: See [`cli-reference.md#destroy`](./cli-reference.md#destroy)

**Note**: Calls `tart stop` first if necessary, then `tart delete`.

---

### recreate

**Invocation**: `just recreate`

**Parameters**: Uses Justfile variables `{{vm}}`, `{{image}}`, `{{dotfiles}}`

**Description**: Destroy and up in one command (full VM refresh).

**Implementation**: `destroy up`

**Use When**: You want to start fresh without manually running `destroy` then `up`.

---

### run

**Invocation**: `just run`

**Parameters**: Uses Justfile variables `{{vm}}`, `{{image}}`, `{{vmgr}}`, `{{dotfiles}}`

**Description**: The main loop: preflight → up → chezmoi diff → apply → verify → destroy.

Gates on `doctor`; always writes `verdict.json`, even on crash.

**Implementation**: 
```just
run: doctor
    @uv run macos-ci harness run --vm {{vm}} --image {{image}} --version-manager {{vmgr}} --dotfiles {{dotfiles}}
```

**CLI Reference**: See [`cli-reference.md#run`](./cli-reference.md#run)

**Artifact Output**:
- `artifacts/<run-id>/state.json` — VM details
- `artifacts/<run-id>/apply.log` — chezmoi output
- `artifacts/<run-id>/verdict.json` — success/failure verdict

**Environment Overrides**:
```bash
MACOS_CI_VERSION_MANAGER=asdf just run
MACOS_CI_IMAGE=ventura just run
```

---

### apply

**Invocation**: `just apply`

**Parameters**: Uses Justfile variables `{{vm}}`, `{{vmgr}}`

**Description**: Only the chezmoi apply, against an already-live VM (fast iteration path).

Assumes a prior `up` has populated `artifacts/latest/state.json`.

**Implementation**: `uv run macos-ci harness apply --vm {{vm}} --version-manager {{vmgr}}`

**CLI Reference**: See [`cli-reference.md#apply`](./cli-reference.md#apply)

**Use When**: You've already run `up` and want to iterate quickly without destroying and re-cloning.

---

### prune

**Invocation**: `just prune`

**Description**: Delete orphan VM clones not tracked in `artifacts/*/state.json`.

**Implementation**: `uv run macos-ci harness prune`

**CLI Reference**: See [`cli-reference.md#prune`](./cli-reference.md#prune)

**Use When**: You've accidentally left behind VMs (e.g., from a crashed test run) and want to clean up.

---

## Images (OCI and Packer Image Management)

These recipes manage Tart VM images and base layers.

### images

**Invocation**: `just images`

**Description**: Print `macos-versions.toml` and list available Tart VMs.

**Implementation**: 
```just
@cat macos-versions.toml
@tart list
```

**Purpose**: Cross-reference declared image versions with what's actually available locally.

---

### pull

**Invocation**: `just pull IMAGE`

**Parameters**:
- `IMAGE` — Image name to pull (e.g., `sequoia`)

**Description**: `tart pull` the OCI ref for IMAGE (resolved from `macos-versions.toml`).

**Status**: ⚠️ Placeholder — implementation not yet landed.

**Implementation** (planned): `uv run macos-ci pull {{IMAGE}}`

**Note**: Pre-pulling the base OCI image to local cache is an optimization that avoids re-pulling the ~23.7GB layer on every golden-image build. See `macos-ci.md` §"Build performance" for details.

---

## Inspection (Debugging and Observation)

These recipes provide interactive and observational access to a running or recently-run VM.

### ssh

**Invocation**: `just ssh`

**Parameters**: Uses Justfile variables `{{vm}}`, `{{vm_user}}`, `{{ssh_opts}}`

**Description**: Interactive shell into the VM.

**Implementation**: 
```just
@ip=$(tart ip {{vm}}) && ssh {{ssh_opts}} {{vm_user}}@"$ip"
```

**Prerequisites**: VM must be running (started by `up`).

**Keys**: 
- `tart ip` — Queries the running VM for its IP
- `ssh_opts` — Pre-configured for key-based auth, no strict checking, batch mode

---

### exec

**Invocation**: `just exec CMD`

**Parameters**:
- `CMD` — Remote command to execute

**Description**: One-shot remote command in the VM.

**Implementation**: 
```just
@ip=$(tart ip {{vm}}) && ssh {{ssh_opts}} {{vm_user}}@"$ip" -- {{CMD}}
```

**Example**: `just exec "uname -a"` prints the guest's OS info.

**Prerequisites**: VM must be running.

---

### logs

**Invocation**: `just logs`

**Parameters**: Uses Justfile variable `{{vm}}`

**Description**: Sweep guest logs into `artifacts/<run-id>/logs/`.

**Implementation**: `uv run macos-ci logs --vm {{vm}}`

**⚠️ Discrepancy**: Justfile invokes `macos-ci logs` (top-level), but CLI defines `macos-ci harness logs` (sub-app). This recipe will fail.

**Correct Implementation** (should be): `uv run macos-ci harness logs --vm {{vm}}`

**CLI Reference**: See [`cli-reference.md#logs`](./cli-reference.md#logs)

---

### debug

**Invocation**: `just debug`

**Description**: Triage: run vm-debug sweep to match logs against failure signatures.

Writes `verdict.json` with findings.

**Implementation**: `uv run macos-ci vm-debug sweep --json`

**CLI Reference**: See [`cli-reference.md#sweep`](./cli-reference.md#sweep)

**Purpose**: Fast post-mortem to identify known failure patterns without manual log inspection.

---

### status

**Invocation**: `just status`

**Description**: Print `tart list` (all VMs) and pretty-print the latest `artifacts/latest/state.json`.

**Implementation**: 
```just
@tart list
@if [ -f artifacts/latest/state.json ]; then jq . artifacts/latest/state.json; else echo "no state.json yet"; fi
```

**Use When**: You want a quick overview of VM state without SSHing in.

---

### gui

**Invocation**: `just gui`

**Parameters**: Uses Justfile variable `{{vm}}`

**Description**: Launch `tart run` with a windowed display (graphical mode).

**Implementation**: `tart run {{vm}}`

**Prerequisites**: VM must be created (by `up`).

**Note**: This opens an interactive Tart window on the host; close the window to disconnect. Useful for manual debugging or screenshots.

---

### vnc

**Invocation**: `just vnc`

**Parameters**: Uses Justfile variable `{{vm}}`

**Description**: Start `tart run --vnc-experimental` and print the parsed VNC target.

**Implementation**: `uv run macos-ci gui vnc --vm {{vm}}`

**Status**: ⚠️ Non-existent command — CLI does not provide `macos-ci gui vnc`.

**Mounted under**: `gui` sub-app (not implemented)

**Note**: `gui.py` only defines `shot`, not `vnc`. This recipe will fail if invoked.

---

### shot

**Invocation**: `just shot LABEL`

**Parameters**:
- `LABEL` — Screenshot label/filename

**Description**: Capture one framebuffer PNG screenshot into `artifacts/<run-id>/screenshots/`.

**Implementation**: `uv run macos-ci gui shot {{LABEL}} --vm {{vm}}`

**Status**: ⚠️ Not yet implemented — CLI command raises `NotImplementedError`.

**Mounted under**: `gui` sub-app

**CLI Reference**: See [`cli-reference.md#shot`](./cli-reference.md#shot)

---

## Testing (Test Execution)

These recipes run the test suite with different scopes and markers.

### test

**Invocation**: `just test`

**Description**: Hermetic unit tests (no VM required).

**Implementation**: `uv run pytest`

**Marker**: (default, no `-m` flag — runs tests without a marker)

**Scope**: Tests in `tests/` that don't require a running VM.

**Use When**: Developing features locally, before committing.

---

### verify

**Invocation**: `just verify`

**Description**: testinfra assertions over SSH against a live VM.

**Implementation**: `uv run pytest -m vm`

**Marker**: `vm`

**Scope**: Tests in `tests/integration/` that assert guest state over SSH.

**Prerequisites**: VM must be running (started by `up`).

**Example**: Assertions that Homebrew is installed, mise is on PATH, etc.

---

### verify-pty

**Invocation**: `just verify-pty`

**Description**: pexpect over `ssh -tt` with PTY.

**Implementation**: `uv run pytest -m pty`

**Marker**: `pty`

**Scope**: Tests in `tests/pty/` that require interactive shell behavior (expect/send patterns).

**Prerequisites**: VM must be running.

**Use When**: Testing shell interactions, prompt behavior, or terminal-specific features.

---

### verify-gui

**Invocation**: `just verify-gui`

**Description**: VNC screenshots and GUI assertions.

**Implementation**: `uv run pytest -m gui`

**Marker**: `gui`

**Scope**: Tests in `tests/gui/` that capture and analyze framebuffer screenshots.

**Prerequisites**: VM running with VNC framebuffer access.

**Use When**: Testing GUI rendering or visual behavior (not yet widely used).

---

### verify-manual

**Invocation**: `just verify-manual`

**Description**: Human-interactive tests (the only recipe that may ever prompt a human).

**Implementation**: `uv run pytest -m manual`

**Marker**: `manual`

**Scope**: Tests in `tests/manual/` requiring human intervention or observation.

**Use When**: Verifying behavior that can't be automated (e.g., manual installation steps, user prompts).

---

### matrix

**Invocation**: `just matrix`

**Description**: Cross-product integration test: every image × every version-manager combination.

**Implementation**: `uv run macos-ci harness matrix`

**CLI Reference**: See [`cli-reference.md#matrix`](./cli-reference.md#matrix)

**Legs**: Default `mise,asdf` × default image (typically `sequoia`).

**Output**: One `verdict.json` per leg under `artifacts/`.

**Example**: With 2 images and 2 version managers, 4 VMs are created and tested independently.

---

## Quality (Code Quality and CI)

These recipes enforce code quality standards and run CI checks.

### lint

**Invocation**: `just lint`

**Description**: Linter check with ruff.

**Implementation**: `uvx ruff check .`

**Scope**: Applies `.ruff.toml` configuration.

**Warnings**: Non-fatal (returns 0 even if warnings found); use for early feedback during development.

---

### fmt

**Invocation**: `just fmt`

**Description**: Code formatter with ruff.

**Implementation**: `uvx ruff format .`

**Scope**: Applies `.ruff.toml` configuration.

**Mutative**: Modifies files in-place. Review changes before committing.

---

### typecheck

**Invocation**: `just typecheck`

**Description**: Type-check with basedpyright (pyright fork).

**Implementation**: `uv run basedpyright`

**Scope**: Applies `pyrightconfig.json` configuration.

**Prerequisites**: basedpyright installed in the project environment.

---

### ci

**Invocation**: `just ci`

**Description**: Run Cirrus CI config locally for parity with remote CI.

**Implementation**: `cirrus run`

**Prerequisites**: Cirrus CLI installed on host.

**Scope**: Executes `.cirrus.yml` tasks locally.

**Use When**: Before pushing, to catch CI failures early.

---

## Planned, Not Implemented

These recipes reference CLI commands that do not yet exist or are stubs:

| Recipe | Status | Reason |
|--------|--------|--------|
| `pull IMAGE` | Placeholder | CLI command not yet implemented |
| `build-ipsw VERSION` | Placeholder | CLI command not yet implemented |
| `gui vnc --vm VM` | Unimplemented | CLI command not yet defined (only `gui shot` exists) |
| `gui shot LABEL` | Stub | CLI raises `NotImplementedError` |
| `just logs` | Broken | Calls wrong invocation (`macos-ci logs` instead of `macos-ci harness logs`) |

These follow the repo's convention of never presenting inference as fact — placeholder recipes that reference unimplemented CLI commands document the *intended* interface, but will fail if invoked.

Tracked with reproduction evidence and claims-ledger entries (plus `images-cache`, absent from this Justfile entirely) in [specs/macos-ci/14-known-discrepancies.md](../../specs/macos-ci/14-known-discrepancies.md) — `just verify-claims` catches these directly.

---

## Sourcing

This reference is extracted from `/Users/bossjones/dev/bossjones/macos-ci/Justfile` (lines 1–226).

**Last verified**: 2026-07-10 by reading actual recipe definitions and comments.

**Note**: The `just` command supports recursive variable expansion, conditionals, and multiple parameter styles. This reference documents the most common patterns; refer to the Justfile itself or `just --help` for advanced features.
