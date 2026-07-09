# 10 — ADR: Tart Is Primary, UTM Is the Escape Hatch

## Status

Accepted (house stance for this repo).

## Context

This repo needs a way to run a macOS VM, install `zsh-dotfiles`/`zsh-dotfiles-prep` into it
non-interactively, assert the install worked, and tear the VM down — repeatably, locally, and fast
enough to iterate on a dotfiles change (see
[09](09-dotfiles-under-test.md#the-linux-coverage-gap-this-repo-exists-to-close) for why this gap
exists at all). Two virtualization tools on macOS were evaluated: **Tart** (Cirrus Labs,
Virtualization.framework-only) and **UTM** (Apple Virtualization.framework + QEMU, GUI-first).

Neither tool has a Terraform provider (**G1**); Tart's own IaC-adjacent story is Orchard (its own
controller/worker CLI + REST API — [03](03-tart-ci-and-orchard.md)), while UTM's tracked IaC request
(`utmapp/UTM#3618`, escalated to issue #3718) is explicitly, per the maintainer, "a long way off." The
`tonyyo11` blog's use of "Terraform" refers to managing **Jamf Pro resources**, not VMs (**G2**) — it
is not counter-evidence for UTM IaC and must not be cited as such.

Beyond the shared absence of IaC, the two tools diverge sharply on what *is* automatable:

- **Packer**: `packer-plugin-tart` is a real, HashiCorp-documented builder with a full field reference
  ([02](02-packer-tart-builder.md)). **No Packer builder exists for UTM** (**G3**) — UTM VMs are built
  by hand or by AppleScript, with no repeatable build pipeline.
- **Guest automation**: Tart's guest interaction is SSH over `--dir` shared mounts — always available.
  UTM's AppleScript Guest Suite (file I/O, command exec) and Input Automation Suite (keystrokes/mouse)
  both require the **QEMU guest agent**, which does not exist for the Apple-backend macOS guest this
  repo needs ([05](05-utm-automation.md)§2.2/§2.6). UTM's AppleScript surface for a macOS guest is
  therefore **lifecycle-only** (start/stop/suspend/duplicate/configure), not guest-exec.
- **Disposable/ephemeral VMs**: Tart's `clone` + `delete` gives an instant, byte-identical, throwaway
  VM per test run. UTM's disposable ("run without saving") mode is **QEMU-backend only** — it does
  not work for macOS guests (**G5**), which require the Apple backend. There is no UTM-native
  disposable macOS VM; the closest approximation is scripting create→snapshot→restore→delete by hand,
  strictly more moving parts for the same outcome ([08](08-dotfiles-test-harness.md)§d).
- **Multi-display**: UTM's Apple backend does not support multiple graphical displays (**G6**) — not
  relevant to a headless CI harness, but confirms the Apple backend is a thinner surface than QEMU
  across the board.

Note explicitly: `advanced/rosetta` (x86_64-on-ARM binary translation) applies to **Linux guests**,
not macOS guests (**G7**) — it is not a factor in either tool's macOS-guest story and is excluded from
this decision.

## Decision

**Tart is primary** for CI and automated dotfiles testing. **UTM is the escape hatch** for
interactive/GUI work, recovery-mode fiddling, and non-ARM or non-macOS guest scenarios where Tart
doesn't apply.

Concretely, for this repo:
- The dotfiles test harness ([08](08-dotfiles-test-harness.md)) is built entirely on Tart primitives:
  Packer golden image → `tart clone` → SSH (no TTY) → chezmoi apply → assertions → `tart delete`.
- UTM is not part of the automated harness. It remains available for a human to boot a macOS VM
  interactively — e.g. to eyeball a rendered dotfiles config in a real GUI session, or to use
  recovery mode (1TR) for SIP/disk changes ([06](06-utm-macos-guest.md)§4) — scenarios where a GUI
  session is the point, not an obstacle.

## Consequences

**Costs accepted:**

1. **Licensing exposure (G4).** Tart and Orchard ship under Fair Source, not a permissive
   open-source license, and Cirrus Labs actively enforced it against a commercial violator in
   October 2025 ([04](04-tart-licensing-risk.md)§3). Personal/workstation use is unconditionally free;
   headless "server installation" use is free only up to **100 combined CPU cores** (Tart) / **4
   workers** (Orchard) before paid tiers (Gold $12K/yr, Platinum $36K/yr, Diamond custom) apply. This
   repo's recommended fleet size (2-3 hosts, 8-16 cores each) stays comfortably under both ceilings by
   design, with an explicit trigger condition to re-evaluate before adding a 4th host or approaching
   100 cores ([04](04-tart-licensing-risk.md)§4). **This requires human sign-off** — it is a real,
   monitored commercial term, not a footnote.
2. **Loss of disposable-mode convenience.** Because UTM's disposable mode doesn't reach macOS guests
   anyway (G5), this is really a non-cost relative to UTM — but it does mean the harness must
   implement its own ephemeral-clone discipline (golden image + `tart clone`/`tart delete`) rather than
   getting it for free from either tool's built-in disposable feature.
3. **No cross-tool image portability.** A Tart golden image and a hand-built UTM VM are not
   interchangeable artifacts; choosing Tart as primary means UTM-based interactive work starts from a
   separately maintained VM, not the same golden image the harness clones from.

**Benefits gained:**

1. A real, versioned, repeatable build pipeline (Packer) for the golden image.
2. An OCI-registry-backed image distribution story (ghcr.io push/pull) if this ever needs to share
   images across machines.
3. A clear, low-moving-parts scale-out path (Orchard) if the harness ever needs to run across more
   than one physical host — see [03](03-tart-ci-and-orchard.md).
4. A guest automation channel (SSH over `--dir`) that actually works for a macOS Apple-backend guest,
   unlike UTM's guest-exec primitives which are gated on infrastructure (QEMU guest agent) this guest
   type doesn't have.

## Revisit triggers

- Tart/Orchard fleet grows past 4 physical hosts or approaches 100 combined CPU cores → re-evaluate
  licensing tier or reduce fleet size (**G4**, [04](04-tart-licensing-risk.md)§4).
- UTM ships IaC support (tracked in `utmapp/UTM#3718`) → re-evaluate whether UTM's automation gap
  (G1/G3/G5) has closed enough to reconsider its role.
- A workload genuinely requires a non-Apple-Silicon host or a non-macOS/non-Linux-Tart guest type that
  Tart cannot serve → UTM's QEMU backend becomes relevant beyond "escape hatch."
