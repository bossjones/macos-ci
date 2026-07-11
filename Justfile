set shell := ["bash", "-uc"]

# List available recipes
default:
    @just --list

# lychee scrapes github.com HTML unauthenticated by default, which rate-limits
# into spurious 404s. Passing a token makes lychee use the GitHub API instead.

# Check all links in markdown files using lychee
link-check:
    @echo "🚀 Checking all links in markdown files using lychee"
    @GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null)}" lychee --config lychee.toml '**/*.md'

# Check all links in markdown files with verbose output
link-check-verbose:
    @echo "🚀 Checking all links in markdown files with verbose output"
    @GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null)}" lychee --config lychee.toml --verbose debug '**/*.md'

# Re-check links ignoring the 7d cache (use after fixing a link).
# lychee has no --no-cache; ageing every entry out to 0s is the supported bypass.
link-check-fresh:
    @echo "🚀 Checking all links, bypassing the lychee cache"
    @GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null)}" lychee --config lychee.toml --max-cache-age 0s '**/*.md'

# Re-execute the evidence behind every claim in .team/claims.jsonl.
# Exit 0 all verified · 2 a claim failed · 3 evidence unreachable · 4 usage.
verify-claims:
    @echo "🔬 Re-checking every spec claim against its evidence"
    @uv run tools/verify_claims.py

# Same, machine-readable — this is what an agent reads instead of scraping prose.
verify-claims-json:
    @uv run tools/verify_claims.py --json

# The token reaches the guest only as a provisioner env var, never a file (specs/macos-ci/13).
# It is an optimisation, not a dependency: without it the build still works, against GitHub's
# 60 req/hr unauthenticated cap instead of 5,000.

# Build the golden Tart image, injecting HOMEBREW_GITHUB_API_TOKEN if one is available.
# The template is deliberately UNAUTHORED: `packer build`/`packer init` are forbidden by the
# verification run's scope, so not one line of it could be validated. Fail loudly rather than
# let `packer build` emit its own error for a file we know is absent. Exit 4 = USAGE, matching
# tools/verify_claims.py. See specs/macos-ci/13-build-secrets.md and OQ-04.
build-golden:
    @test -f packer/tart-golden-image.pkr.hcl || { \
       echo "missing: packer/tart-golden-image.pkr.hcl" >&2; \
       echo "see specs/macos-ci/13-build-secrets.md and OQ-04" >&2; \
       exit 4; }
    @echo "📦 Building the golden image"
    @HOMEBREW_GITHUB_API_TOKEN="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}" \
      packer build packer/tart-golden-image.pkr.hcl

# `rm` inside a guest unlinks an inode; it does not zero the blocks, so a secret written to
# the guest survives in the disk image. This proves we never wrote one. Scans the whole VM
# directory rather than a named disk file: tart documents ~/.tart/vms/ but not the file
# inside it, and disk_format may be raw or asif.

# Leak canary: assert the Homebrew token appears nowhere in a built VM's artifact.
verify-no-secrets vm:
    @tok="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}"; \
     if [ -z "$tok" ]; then echo "⚠️  no token in the environment — nothing to search for"; exit 0; fi; \
     if [ ! -d ~/.tart/vms/{{vm}} ]; then echo "no such VM: {{vm}}" >&2; exit 4; fi; \
     if LC_ALL=C grep -r -a -l -F "$tok" ~/.tart/vms/{{vm}}/ 2>/dev/null; then \
       echo "🚨 LEAK: the token is present in the artifact above"; exit 2; \
     else echo "✅ clean: token absent from ~/.tart/vms/{{vm}}/"; fi

# Count unverified markers. A spec's honesty budget: these must be justified, not ambient.
unverified-count:
    @echo "🕵️  <!-- UNVERIFIED --> markers by file:"
    @grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -v '`<!-- UNVERIFIED' || echo "  none"

# The full truth gate. Everything an agent must pass before a spec is trustworthy.
check: link-check verify-claims unverified-count

# ===================== Below this line: 12-tooling-and-agent-loop.md's =====================
# ===================== recipe-table extension (Step 4). Nothing above    =====================
# ===================== this line moved, to keep .team/claims.jsonl's     =====================
# ===================== file-line citations pinned to their original lines. =====================

vm       := env_var_or_default("MACOS_CI_VM", "dotfiles-test")
image    := env_var_or_default("MACOS_CI_IMAGE", "sequoia")
dotfiles := env_var_or_default("ZSH_DOTFILES", justfile_directory() / ".." / "zsh-dotfiles")
vm_user  := "admin"
vmgr     := env_var_or_default("MACOS_CI_VERSION_MANAGER", "mise")
ssh_opts := "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=8 -o BatchMode=yes"

# `build-golden` is the real recipe (the ledger's claims reference it by name); `build` is the
# spec-12-shaped alias for anyone driving the recipe table by its documented name instead.
alias build := build-golden

# ============================== Lifecycle ==============================

# Preflight every requirement. --json for agents. Exit 2 if anything is missing.
doctor *ARGS:
    @uv run macos-ci doctor {{ARGS}}

# `tart clone` -> `tart run --no-graphics &` -> poll `tart ip` -> wait for SSH.
# `harness` is a sub-app (`cli.py: app.add_typer(harness.app, name="harness")`).
up:
    @uv run macos-ci harness up --vm {{vm}} --image {{image}} --dotfiles {{dotfiles}}

# Stop the VM, leave the clone on disk.
down:
    @uv run macos-ci harness down --vm {{vm}}

alias stop := down

# Delete the VM clone.
destroy:
    @uv run macos-ci harness destroy --vm {{vm}}

# `destroy` then `up`.
recreate: destroy up

# The main loop: doctor -> up -> chezmoi diff -> apply -> verify -> destroy.
# Gates on `doctor`; always writes verdict.json, even on crash.
run: doctor
    @uv run macos-ci harness run --vm {{vm}} --image {{image}} --version-manager {{vmgr}} --dotfiles {{dotfiles}}

# Only the chezmoi apply, against an already-live VM. Fast iteration.
apply:
    @uv run macos-ci harness apply --vm {{vm}} --version-manager {{vmgr}}

# Delete orphan clones not tracked under artifacts/.
prune:
    @uv run macos-ci harness prune

# ================================ Images ================================

# Packer build from a pinned IPSW. Verifies sha256 before building.
build-ipsw VERSION:
    @uv run macos-ci build-ipsw {{VERSION}}

# Print macos-versions.toml alongside `tart list`.
images:
    @cat macos-versions.toml
    @tart list

# `tart pull` the OCI ref for IMAGE (resolved from macos-versions.toml).
pull IMAGE:
    @uv run macos-ci pull {{IMAGE}}

# ============================== Inspection ==============================

# Interactive shell into the VM.
ssh:
    @ip=$(tart ip {{vm}}) && ssh {{ssh_opts}} {{vm_user}}@"$ip"

# One-shot remote command in the VM.
exec CMD:
    @ip=$(tart ip {{vm}}) && ssh {{ssh_opts}} {{vm_user}}@"$ip" -- {{CMD}}

# Sweep guest logs into artifacts/<run-id>/logs/.
logs:
    @uv run macos-ci logs --vm {{vm}}

# Triage; writes verdict.json. `vm-debug` is a sub-app (`cli.py`, 🐍's file) with one command,
# `sweep` — spec 12's recipe body reads `macos-ci vm-debug --json` verbatim, but that's a group,
# not a leaf command, so the actual invocation needs the subcommand name.
debug:
    @uv run macos-ci vm-debug sweep --json

# `tart list` plus a pretty-printed artifacts/latest/state.json.
status:
    @tart list
    @if [ -f artifacts/latest/state.json ]; then jq . artifacts/latest/state.json; else echo "no state.json yet"; fi

# `tart run` with a window, for poking at it by hand.
gui:
    @tart run {{vm}}

# `tart run --vnc-experimental`, print the parsed VNC target.
# Mounted under the `gui` sub-app (`cli.py: app.add_typer(gui.app, name="gui")`), 🐍's file.
vnc:
    @uv run macos-ci gui vnc --vm {{vm}}

# Capture one framebuffer PNG into artifacts/<run-id>/screenshots/.
# Mounted under the `gui` sub-app (`cli.py: app.add_typer(gui.app, name="gui")`), 🐍's file.
shot LABEL:
    @uv run macos-ci gui shot {{LABEL}} --vm {{vm}}

# ================================ Testing ================================

# Hermetic units. No VM. This is what an agent runs by default.
test:
    @uv run pytest

# `-m vm` — testinfra assertions over SSH.
verify:
    @uv run pytest -m vm

# `-m pty` — pexpect over `ssh -tt`.
verify-pty:
    @uv run pytest -m pty

# `-m gui` — VNC screenshots.
verify-gui:
    @uv run pytest -m gui

# `-m manual` — the only recipe that may ever prompt a human.
verify-manual:
    @uv run pytest -m manual

# Cross-product of image × version_manager.
matrix:
    @uv run macos-ci harness matrix

# ================================ Quality ================================

# `ruff check .`
lint:
    @uvx ruff check .

# `ruff format .`
fmt:
    @uvx ruff format .

# `basedpyright`
typecheck:
    @uv run basedpyright

# `cirrus run` for local/CI parity.
ci:
    @cirrus run

# pyrefly type check (standalone; only fails on errors new since the baseline)
# `.claude/status_lines` is passed explicitly on the CLI (not via [tool.pyrefly] project-includes)
# because pyrefly's directory walker silently skips dot-directory paths declared in config.
check-pyrefly:
    uv run pyrefly check --baseline pyrefly-baseline.json --summarize-errors src tests tools .claude/status_lines/status_line_v10.py

# refresh the committed baseline after fixing/introducing errors
pyrefly-baseline:
    uv run pyrefly check --baseline pyrefly-baseline.json --update-baseline src tests tools .claude/status_lines/status_line_v10.py

# type-coverage report (typed / Any / untyped) as JSON
pyrefly-coverage:
    uv run pyrefly coverage report src tests tools .claude/status_lines/status_line_v10.py

# ===== UTM (manual GUI lane -- spec 10: human escape hatch, not CI) =====
# specs/utm-improvements.md. Naming convention, no config lane: `dotfiles-golden-utm` /
# `dotfiles-utm`, env-overridable. This lane never gates CI -- appended below the pinning
# banner (line 76), so no existing .team/claims.jsonl file-line citation shifts.

utm_vm     := env_var_or_default("MACOS_CI_UTM_VM", "dotfiles-utm")
utm_golden := env_var_or_default("MACOS_CI_UTM_GOLDEN", "dotfiles-golden-utm")
utmctl     := "/Applications/UTM.app/Contents/MacOS/utmctl"

# UTM.app version (Info.plist only), golden bundle presence, leases readability. Exit 2 on miss;
# `just doctor` never fails when UTM is absent (step 6's optional row).
utm-doctor:
    @uv run macos-ci utm doctor --golden {{utm_golden}}

# One-time: stage the tart golden disk as raw + print the manual GUI import checklist.
utm-import-golden:
    @uv run macos-ci utm import-golden

# `utmctl clone` golden -> session VM; no-op if it already exists.
utm-clone:
    @uv run macos-ci utm clone --vm {{utm_vm}} --golden {{utm_golden}}

# Clone-if-missing -> windowed start -> MAC->leases IP -> two-phase SSH -> state.json (lane: utm).
utm-up:
    @uv run macos-ci utm up --vm {{utm_vm}} --golden {{utm_golden}}

# `open -a UTM` -- bring the GUI window forward.
utm-gui:
    @open -a UTM

# Print the guest-side VirtioFS mount + chezmoi apply block to paste into iTerm2. The human
# applies interactively; SSH is the feedback channel, not the applier.
utm-bootstrap-dotfiles:
    @uv run macos-ci utm bootstrap-dotfiles

# The `tart ip` equivalent for the UTM lane (host-side MAC -> dhcpd_leases/arp; spec 05 §4.5).
utm-ip:
    @uv run macos-ci utm ip --vm {{utm_vm}}

# Interactive shell into the UTM VM.
utm-ssh:
    @ip=$(uv run macos-ci utm ip --vm {{utm_vm}}) && ssh {{ssh_opts}} -i harness/ssh/id_ed25519_harness {{vm_user}}@"$ip"

# One-shot remote command over the same SSH.
utm-exec CMD:
    @ip=$(uv run macos-ci utm ip --vm {{utm_vm}}) && ssh {{ssh_opts}} -i harness/ssh/id_ed25519_harness {{vm_user}}@"$ip" -- {{CMD}}

# Redirect the serial input/output to this terminal -- the only guest channel utmctl offers
# without a QEMU guest agent (the degraded path if IP discovery ever fails).
utm-serial:
    @{{utmctl}} attach {{utm_vm}}

# `utmctl list`.
utm-status:
    @{{utmctl}} list

# Graceful stop (request mode).
utm-stop:
    @uv run macos-ci utm stop --vm {{utm_vm}}

# Delete the session clone; the golden VM is untouched.
utm-destroy:
    @uv run macos-ci utm destroy --vm {{utm_vm}}

# The seven-item iTerm2 UX checklist, JSON-reported. Prompts on a TTY, skips cleanly off-TTY.
utm-verify-manual:
    @uv run pytest -m manual tests/manual/test_utm_ux.py --json-report --json-report-file=artifacts/latest/manual-utm.json
