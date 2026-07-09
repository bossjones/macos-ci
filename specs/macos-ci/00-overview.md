# 00 — Overview

## The problem

`zsh-dotfiles` (chezmoi-managed) and `zsh-dotfiles-prep` (Homebrew/Xcode-CLT bootstrap) both have
Linux CI coverage today — three Dockerfiles (`centos-9`, `debian-12`, `ubuntu-2204`) in
`zsh-dotfiles-prep`, plus a `smoke-test-docker.sh` harness in `zsh-dotfiles` that runs on
`ubuntu:24.04` in GitHub Actions. **Neither repo has a macOS equivalent.** Docker cannot run a macOS
guest, and GitHub's hosted `macos-14`/`macos-latest` runners are remote, queued CI — not a local,
fast, disposable-VM iteration loop a developer can run in seconds while editing a template. That gap
— a local, scriptable, disposable macOS VM to run the same install-and-assert loop Linux already gets
from `docker run` — is this repo's entire reason to exist. See
[09-dotfiles-under-test.md](09-dotfiles-under-test.md#the-linux-coverage-gap-this-repo-exists-to-close).

## The stack (house stance)

**Tart is primary, UTM is the escape hatch.** Tart has a Packer builder, an OCI image registry, a
CLI, and an orchestrator (Orchard); UTM has none of that for macOS guests — its automation surface is
AppleScript/JXA plus the `utm://` URL scheme, both of which are lifecycle-only for a macOS
(Apple-backend) guest, not guest-exec. Full reasoning and the accepted-risk tradeoffs are in
[10-tart-vs-utm-adr.md](10-tart-vs-utm-adr.md).

- **Golden image**: Packer + `packer-plugin-tart` builds a Tart VM once, with Xcode CLT + Homebrew +
  chezmoi ≥ 2.20.0 preinstalled.
- **Per-test clone**: `tart clone <golden> <ephemeral>` gives a byte-identical VM in seconds; the
  dotfiles working tree is mounted in (not baked in) via `tart --dir`.
- **The install run**: an SSH session with no TTY attached, which is exactly what makes chezmoi's
  `stdinIsATTY` gate resolve every prompt to its documented default — already solved upstream, not
  discovered here (G11).
- **Teardown**: `tart delete`. UTM has no equivalent for a macOS guest (disposable mode is
  QEMU-backend only, G5).
- **Scale-out** (not needed yet): Orchard, if/when this ever needs to run across more than one
  physical host.

## File map and reading order

| # | File | Owner | What it covers |
|---|---|---|---|
| 00 | `00-overview.md` (this file) | synth | Orientation |
| 01 | `01-tart-core.md` | tart-core | Install, CLI verbs, prebuilt images, `--dir` mounts, networking, headless keychain requirement (G8) |
| 02 | `02-packer-tart-builder.md` | tart-core | Full Packer builder field reference; markkenny reference implementation |
| 03 | `03-tart-ci-and-orchard.md` | tart-ci | Cirrus CLI (`cirrus run`) for local/CI parity; Orchard multi-host orchestration |
| 04 | `04-tart-licensing-risk.md` | tart-ci | Fair Source tier table, Oct-2025 enforcement, accepted-risk recommendation (G4) |
| 05 | `05-utm-automation.md` | utm | Why UTM has no IaC (G1); AppleScript suites; the QEMU-guest-agent gate (G3); `utm://` scheme |
| 06 | `06-utm-macos-guest.md` | utm | macOS-guest requirements, missing-features list (G5/G6/G7), VirtioFS as the real automation channel |
| 07 | `07-utm-settings-appendix.md` | utm | Thin settings-page index; 4 pruned dead URLs (G10) |
| 08 | `08-dotfiles-test-harness.md` | harness | The harness design: golden image, non-interactive chezmoi run, assertions, teardown, Ansible rejection |
| 09 | `09-dotfiles-under-test.md` | harness | What's actually installed; the chezmoi template contract (G11); reused assertion vocabulary |
| 10 | `10-tart-vs-utm-adr.md` | synth | The ADR recording the house stance |
| 11 | `11-sources.md` | synth | Every source URL, grouped, graded meaty/thin/404/cited-as-exclusion. Checked by `just link-check` |

Suggested reading order for a newcomer: **00 → 10 → 01 → 02 → 08 → 09 → 03 → 04 → 05 → 06 → 07 → 11.**
Start with the decision (why Tart), then the primitives it composes (01/02), then the harness that
uses them (08/09), then the supporting detail (03/04/05/06/07), then the audit trail (11).

## Scope note

This is a **docs-only** research/spec pass. No VM was booted, no `brew install` was run, and no host
was mutated to produce these specs — see each file's inline citations and `<!-- UNVERIFIED -->`
markers for what is confirmed from a source versus composed from documented primitives.
