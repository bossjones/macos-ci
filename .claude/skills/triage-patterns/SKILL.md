---
name: triage-patterns
description: Use when you need to interpret a specific macOS log line from a tart VM harness run (install log, Homebrew, chezmoi diff/apply, unified log, launchd) — deciding whether it's a real failure or benign first-boot noise, or mapping a known signature to its root cause. Trigger on questions like "is `<log line>` a real problem or just noise?", "what does `<error>` mean / what usually causes it", "map this to a root cause", "which log lines actually matter vs benign warnings", or "is this xcode-select/keychain/rosetta thing expected or a real failure?". Covers the repo's seed failure signatures (tart ip never returns, CLT GUI prompt firing non-interactively, Rosetta/Homebrew path mismatch, locked login keychain (G8), chezmoi template render errors, asdf shims preceding mise) plus the generic strong-signature substring list. This is the reference/knowledge skill (also preloaded into the log-researcher subagent for identical triage); it does NOT sweep VMs itself — for a full "go investigate why the run is broken" across log sources, use the `triage-logs` skill instead.
capabilities: ["log-triage", "failure-signature-reference", "root-cause-mapping"]
---

# macOS harness triage patterns

This is the shared "what does this log line actually mean" reference for `macos-ci` tart VM runs.
It's the single source of truth behind `macos-ci vm-debug`'s signature matching and the
`triage-logs` skill's root-cause step. The goal is to move from a raw log line to a *named cause*
fast — the way `The specified item could not be found in the keychain` on a headless boot is
obviously "the login keychain is locked" once you've seen it once.

## Strong failure signatures (signal, not noise)

These are the substrings `macos-ci vm-debug` treats as smoking guns across the generic log
sources (`install-log`, `brew-log`, `unified-log`, `launchd`). They're deliberately **specific** —
not bare `error`/`warning` — so a clean boot with benign warnings still reports healthy:

`permission denied` · `failed to` · `failed with` · `cannot open` · `cannot access` ·
`no such file` · `connection refused` · `connection reset` · `timed out` ·
`operation not permitted` · `fatal` · `segfault` · `core dump`

If a line matches one of these, don't stop at "there's an error" — map it to a cause using the
seed table below, or reason from the specific text. The signature is the *starting* point of a
diagnosis, not the diagnosis itself.

## Seed failure signatures — canonical root-cause mappings

These are macOS/tart-specific and source-scoped (a given signature only means something on its
own log source — e.g. `/usr/local` alone is meaningless on `chezmoi-diff`). Grow this table from
real Phase-1 failures rather than inventing more.

**Example 1 — `tart ip` never returns**
Source: `tart-ip`. Symptom: `tart ip <vm>` hangs or returns empty/nothing to resolve.
Cause: the guest never got a DHCP lease. Check the networking mode (`tart run --net-bridged=en0`
needs ARP-based resolution, `tart ip <vm> --resolver=arp`; default softnet DHCP is the common
case). Fix: confirm the resolver matches the run mode; a bridged VM resolved with the default
resolver will hang indefinitely.

**Example 2 — the CLT GUI prompt fires non-interactively**
Source: `install-log`. Input: `xcode-select: note: install requested for command line developer
tools`.
Cause: the golden image is trying to install Xcode CLT via the interactive GUI installer inside a
headless/non-TTY provisioning run, which never completes because there's no GUI session to click
through. Fix: the golden-image provisioner must install CLT non-interactively via
`softwareupdate --install <label>` (the CLT label from `softwareupdate --list`), never
`xcode-select --install`.

**Example 3 — architecture mismatch (Rosetta / Homebrew prefix)**
Source: `brew-log`. Input: `Cannot install under Rosetta 2 on ARM processors` **or** a `brew
config` showing `/usr/local` where `/opt/homebrew` is expected.
Cause: something in the provisioning chain is running under Rosetta translation (x86_64) on an
arm64 host, or Homebrew got installed to the Intel prefix. Fix: ensure the shell provisioner and
every invoked binary run natively (no `arch -x86_64`), and that Homebrew is installed fresh to
`/opt/homebrew` — don't inherit a `/usr/local` install from a base image.

**Example 4 — locked login keychain on headless boot (G8)**
Source: `unified-log`. Input (headless boot): `The specified item could not be found in the
keychain.`
Cause: macOS 15+'s undocumented requirement that headless `tart run` needs an **unlocked**
`login.keychain` available, which a fresh non-interactive boot does not have. This is **G8** —
see `specs/macos-ci/01-tart-core.md`. Fix: the golden image must create *and* unlock a
non-interactive keychain during provisioning (the three-command sequence in `01-tart-core.md`),
not rely on a GUI login session that headless boots never get.

**Example 5 — chezmoi template render error**
Source: `chezmoi-diff`. Input: `chezmoi: template: dot_zshrc.tmpl:12:3: executing "dot_zshrc.tmpl"
at <.someVar>: map has no entry for key "someVar"`.
Cause: a chezmoi template references data that isn't present (missing `.chezmoidata`/seed-config
key, or a stale template referencing a removed field). This is a **pre-apply** failure — the run
must fail at the `chezmoi-diff` phase, before any install step executes, never fall through to
apply with a broken template. Fix: correct the template or the seed-config data feeding it; verify
with `chezmoi execute-template` locally before re-running.

**Example 6 — asdf shims precede mise on PATH**
Source: `unified-log` / a `PATH`-check command. Input: `which node` (or `zsh -lc 'which node'`)
resolves to `~/.asdf/shims/node` when `version_manager=mise` was requested.
Cause: the optional `zsh-dotfiles-prep` asdf installer ran and its shim directory landed earlier
in `PATH` than mise's, so the version manager under test never actually wins. This is exactly the
class of bug `08-dotfiles-under-test.md`'s "the `version_manager` selector" section warns about.
Fix: don't install `zsh-dotfiles-prep` on the `mise`-only matrix leg (it's a separate, optional
matrix leg per the packer-builder brief), or fix the dotfiles' `PATH` ordering so mise always wins
when selected.

## What counts as noise (do NOT flag)

A healthy provisioning run is noisy. Don't raise these as the root cause:

- Benign `install.log`/`brew config` chatter that doesn't match a strong signature and blocks
  nothing (Spotlight indexing messages, Homebrew analytics pings, routine `softwareupdate`
  progress lines).
- Transient failures immediately followed by a successful retry (`retry -t 4` wrapping the apply
  step logs its own retries — a single `failed to connect` that then succeeds is the retry
  working, not a bug). Read a few lines *past* the hit before concluding.
- `xcode-select: note:` lines that are just informational status, not the GUI-prompt failure mode
  (the smoking gun is specifically `install requested for command line developer tools` appearing
  *inside* a non-interactive run that then hangs — a CLT that's already installed logging its
  version is not this).
- `launchd` jobs briefly `<key>LastExitStatus</key>` non-zero on their first attempt but healthy on
  the next `launchctl print` poll.

The health rule `macos-ci vm-debug` uses: a source is healthy iff it's reachable **and** no
signature (seed or generic) hit. If you can't tie a line to a named cause, say so rather than
inventing one — a confident wrong cause is worse than an honest "inconclusive."
