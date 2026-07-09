# 11 — Sources

Every URL fetched (or attempted) across the research pass, grouped by bucket, each with a one-line
"what it gave us" and a grade: **[meaty]** — substantial, directly-cited content; **[thin]** — a stub
or index page, useful mainly as a pointer; **[404-pruned]** — dead, do not fetch or cite (G10).

## Tart core

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/quick-start/](https://tart.run/quick-start/) | [meaty] | Install, full core CLI verb table, prebuilt ghcr.io image matrix + default creds, `--dir` shared-mount syntax, disk-resize recovery procedure — [01](01-tart-core.md) |
| [tart.run/faq/](https://tart.run/faq/) | [meaty] | NAT vs bridged networking, `~/.tart` layout + auto-pruning, macOS 15+ headless keychain requirement (G8), nested-virtualization M3/M4+Linux-only limit (G8) — [01](01-tart-core.md) |

## Packer + Tart builder

| URL | Grade | What it gave us |
|---|---|---|
| [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart) | [thin] | Install snippet, macOS 15 host requirement, Sequoia local-network SSH workaround — explicitly defers config docs elsewhere — [02](02-packer-tart-builder.md) |
| [developer.hashicorp.com — tart builder component](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart) | [meaty] | Canonical full field reference (source-VM, registry, resources, disk, display/boot, runtime, SSH, HTTP server, VNC) — [02](02-packer-tart-builder.md) |
| [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation) | [meaty] | Real-world reference pipeline: `Packer.sh`/`Tarter.sh`, 15-20 min build time, IPSW sourcing, clone-and-run pattern, Ansible-during-build precedent, config toggles — [02](02-packer-tart-builder.md) |

## Tart CI integration and Orchard

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/) | [meaty] | `.cirrus.yml` macOS-task syntax, local/cloud parity, artifact extraction (`--artifacts-dir`) — [03](03-tart-ci-and-orchard.md) |
| [tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/) | [meaty] | Controller/worker architecture, `orchard dev`, core VM commands, SSH/VNC proxy, worker license tiers by env var — [03](03-tart-ci-and-orchard.md), also cross-cited in [04](04-tart-licensing-risk.md) for the worker-count column |

## Tart / Orchard licensing (G4)

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/licensing/](https://tart.run/licensing/) | [meaty] | Current tier table (Free/Gold/Platinum/Diamond), the "all cores always counted" clarification — [04](04-tart-licensing-risk.md) |
| [tart.run/blog/2023/02/11/changing-tart-license/](https://tart.run/blog/2023/02/11/changing-tart-license/) | [meaty] | Fair Source 100 transition announcement, personal-use exemption, "server installation" definition (no connected display) — [04](04-tart-licensing-risk.md) |
| [tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/](https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/) | [meaty] | Proof enforcement is not theoretical — competing-product violation, paid settlement, named counsel, CEO characterization of the case as exceptional — [04](04-tart-licensing-risk.md) |

## UTM automation and IaC gap

| URL | Grade | What it gave us |
|---|---|---|
| [docs.getutm.app/scripting/reference/](https://docs.getutm.app/scripting/reference/) | [meaty] | Full AppleScript dictionary: UTM/Guest/Configuration/USB/Registry/Input suites, the QEMU-guest-agent gate on Guest Suite, `apple configuration` field reference — [05](05-utm-automation.md), [06](06-utm-macos-guest.md)§5 |
| [docs.getutm.app/scripting/cheat-sheet/](https://docs.getutm.app/scripting/cheat-sheet/) | [meaty] | Worked AppleScript snippets for every suite, annotated for backend applicability — [05](05-utm-automation.md)§3 |
| [docs.getutm.app/advanced/remote-control/](https://docs.getutm.app/advanced/remote-control/) | [meaty] | `utm://` URL-scheme command table, Shortcuts/Automator recipes, improper-shutdown warnings — [05](05-utm-automation.md)§5 |
| [docs.getutm.app/advanced/headless/](https://docs.getutm.app/advanced/headless/) | [meaty] | Headless setup (delete display/serial-terminal device), dock-icon hiding — [05](05-utm-automation.md)§4 |
| [docs.getutm.app/preferences/macos/](https://docs.getutm.app/preferences/macos/) | [thin] | App-wide prefs incl. dock-icon toggle and UTM server remote-access settings — [05](05-utm-automation.md)§4, [07](07-utm-settings-appendix.md) |
| [github.com/utmapp/UTM/discussions/3618](https://github.com/utmapp/UTM/discussions/3618) | [meaty] | The IaC feature request and maintainer's "a long way off" reply — direct source for G1 — [05](05-utm-automation.md)§1 |
| `github.com/utmapp/UTM/issues/3718` | [thin] | The tracked (still-open) IaC-support issue referenced by the discussion above — [05](05-utm-automation.md)§1 |

## UTM macOS guest support

| URL | Grade | What it gave us |
|---|---|---|
| [docs.getutm.app/guest-support/macos/](https://docs.getutm.app/guest-support/macos/) | [meaty] | macOS 12+/Apple-Silicon-host requirement, IPSW sourcing, the master missing-features list, VirtioFS + network-sharing mount instructions, clipboard sharing steps — [06](06-utm-macos-guest.md)§1-3,8 |
| [docs.getutm.app/advanced/disposable/](https://docs.getutm.app/advanced/disposable/) | [thin] | Single-sentence confirmation: disposable mode is QEMU-backend only — direct source for G5 — [06](06-utm-macos-guest.md)§2 |
| [docs.getutm.app/advanced/multiple-displays/](https://docs.getutm.app/advanced/multiple-displays/) | [thin] | Single-sentence confirmation: no multi-display on Apple backend — direct source for G6 — [06](06-utm-macos-guest.md)§2 |
| [docs.getutm.app/advanced/recovery/](https://docs.getutm.app/advanced/recovery/) | [thin] | 1TR recovery-mode boot, macOS 13+/Apple-backend-only, SIP-disable use case — [06](06-utm-macos-guest.md)§4 |
| [docs.getutm.app/advanced/serial/](https://docs.getutm.app/advanced/serial/) | [thin] | PTTY-vs-network-socket serial backends, `screen /dev/ttysNNN` connection pattern — [06](06-utm-macos-guest.md)§6 |
| [docs.getutm.app/guest-support/dynamic-resolution/](https://docs.getutm.app/guest-support/dynamic-resolution/) | [thin] | macOS 14+ Apple-backend auto-resolution behavior vs QEMU's manual `xrandr` workaround — [06](06-utm-macos-guest.md)§7 |
| [docs.getutm.app/guides/classic-macos/](https://docs.getutm.app/guides/classic-macos/) | [thin] | Confirmed out-of-scope: classic 68k/PPC Mac OS emulation, unrelated to this repo's macOS 12+ Apple-backend target — [06](06-utm-macos-guest.md)§10 |
| `docs.getutm.app/advanced/rosetta/` | [thin] | Confirmed Rosetta (x86_64-on-ARM) applies to **Linux** guests only, not macOS guests — direct source for G7 — excluded from macOS-guest scope per [06](06-utm-macos-guest.md)§2 |

## UTM settings pages (thin appendix)

| URL | Grade | What it gave us |
|---|---|---|
| `docs.getutm.app/settings-apple/boot/` | [thin] | OS selection, IPSW field — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-apple/drive/` | [thin] | Drive fields incl. macOS 26+ ASIF format — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-apple/system/` | [thin] | CPU/memory fields — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-apple/information/` | [thin] | Cosmetic name/notes/icon — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-apple/sharing/` | [thin] | Shared-directory list — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-qemu/system/` | [thin] | Contrast-only: QEMU arch/CPU/memory fields — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-qemu/qemu/` | [thin] | Contrast-only: logging/UEFI/RNG/balloon/TPM/TSO toggles; notes the Apple-backend TSO equivalent is undocumented — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-qemu/sharing/` | [thin] | Contrast-only: SPICE WebDAV/VirtFS sharing — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-qemu/input/` | [thin] | Contrast-only: USB bus version/limits, N/A to Apple backend — [07](07-utm-settings-appendix.md) |
| `docs.getutm.app/settings-qemu/information/` | [thin] | Byte-identical to Apple-backend information page — [07](07-utm-settings-appendix.md) |

## Pruned — 404 during this research pass (G10, do not fetch or cite)

| URL | Grade | Note |
|---|---|---|
| `docs.getutm.app/settings-apple/devices/` | [404-pruned] | Would have documented Apple-backend device toggles (balloon/entropy/sound/keyboard/pointer/trackpad) |
| `docs.getutm.app/settings-qemu/devices/devices/` | [404-pruned] | — |
| `docs.getutm.app/settings-qemu/drive/drive/` | [404-pruned] | — |
| `docs.getutm.app/guest-support/sharing/sharing/` | [404-pruned] | — |

## Local working trees (read directly, not fetched — G11)

| Path | Grade | What it gave us |
|---|---|---|
| `/Users/bossjones/dev/bossjones/zsh-dotfiles` | [meaty] | `.chezmoiroot`, `.chezmoiversion`, `home/.chezmoi.yaml.tmpl` (the `stdinIsATTY` non-interactive contract), `scripts/smoke-test-docker.sh` (canonical non-TTY invocation + assertion vocabulary), `test_dotfiles.py`, `CLAUDE.md`, `.github/workflows/tests.yml` — [08](08-dotfiles-test-harness.md), [09](09-dotfiles-under-test.md) |
| `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep` | [meaty] | `bin/zsh-dotfiles-prereq-installer`, `Brewfile`, `Makefile`, `TESTING.md`/`DEBUG.md`, `Dockerfile-{centos-9,debian-12,ubuntu-2204}` (the existing Linux coverage this repo has no macOS equivalent of) — [09](09-dotfiles-under-test.md) |

## Not fetched — cited only as a contrast/exclusion in the ground truths

`tonyyo11`'s blog (Terraform-for-Jamf-Pro, **G2**) was identified during prior research (predating this
pass) as a source to explicitly *not* cite as VM-as-code evidence; it is not re-fetched here and is
referenced only in [10-tart-vs-utm-adr.md](10-tart-vs-utm-adr.md) to preempt a plausible misreading.
