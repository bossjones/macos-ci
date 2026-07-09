# 11 — Sources

Every URL fetched (or attempted) across the research pass, grouped by bucket, each with a one-line
"what it gave us" and a grade:

| Grade | Meaning |
|---|---|
| `[meaty]` | Substantial, directly-cited content |
| `[thin]` | A stub, index, or TOC page — useful mainly as a pointer |
| `[404]` | Genuinely dead. Exactly one URL qualifies |
| `[cited-as-exclusion]` | Read only to establish what it does **not** support; never cited as evidence |

**Every URL below is a live markdown link on purpose.** `just link-check` runs
[lychee](https://github.com/lycheeverse/lychee) over this file; a bare-backtick URL would be invisible to
it, which is how the mistake in the retraction section below survived a full cross-check pass.

## Tart core

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/quick-start/](https://tart.run/quick-start/) | `[meaty]` | Install, full core CLI verb table, prebuilt ghcr.io image matrix + default creds, `--dir` shared-mount syntax, disk-resize recovery procedure — [01](01-tart-core.md) |
| [tart.run/faq/](https://tart.run/faq/) | `[meaty]` | NAT vs bridged networking, `~/.tart` layout + auto-pruning, macOS 15+ headless keychain requirement (G8), nested-virtualization M3/M4+Linux-only limit (G8) — [01](01-tart-core.md) |

## Packer + Tart builder

| URL | Grade | What it gave us |
|---|---|---|
| [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart) | `[thin]` | Install snippet, macOS 15 host requirement, Sequoia local-network SSH workaround — explicitly defers config docs elsewhere — [02](02-packer-tart-builder.md) |
| [developer.hashicorp.com — tart builder](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart) | `[meaty]` | Canonical full field reference (source-VM, registry, resources, disk, display/boot, runtime, SSH, HTTP server, VNC) — [02](02-packer-tart-builder.md) |
| [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation) | `[meaty]` | Real-world reference pipeline: `Packer.sh`/`Tarter.sh`, 15-20 min build time, IPSW sourcing, clone-and-run pattern, Ansible-during-build precedent, config toggles — [02](02-packer-tart-builder.md) |

## Tart CI integration and Orchard

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/) | `[meaty]` | `.cirrus.yml` macOS-task syntax, local/cloud parity, artifact extraction (`--artifacts-dir`) — [03](03-tart-ci-and-orchard.md) |
| [tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/) | `[meaty]` | Controller/worker architecture, `orchard dev`, core VM commands, SSH/VNC proxy, worker license tiers by env var — [03](03-tart-ci-and-orchard.md), [04](04-tart-licensing-risk.md) |

## Tart / Orchard licensing (G4)

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/licensing/](https://tart.run/licensing/) | `[meaty]` | Current tier table (Free/Gold/Platinum/Diamond), the "all cores always counted" clarification — [04](04-tart-licensing-risk.md) |
| [tart.run/blog/](https://tart.run/blog/) | `[thin]` | Blog index; the two posts below are what mattered |
| [Changing Tart's license (2023-02-11)](https://tart.run/blog/2023/02/11/changing-tart-license/) | `[meaty]` | Fair Source 100 transition, personal-use exemption, "server installation" definition (no connected display) — [04](04-tart-licensing-risk.md) |
| [Cirrus Labs enforces its Fair Source license (2025-10-27)](https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/) | `[meaty]` | Proof enforcement is not theoretical — competing-product violation, paid settlement, named counsel — [04](04-tart-licensing-risk.md) |

## UTM automation and the IaC gap

| URL | Grade | What it gave us |
|---|---|---|
| [docs.getutm.app/](https://docs.getutm.app/) | `[thin]` | Docs home; nav is the authoritative page index (and revealed pages the brief omitted) |
| [mac.getutm.app/](https://mac.getutm.app/) | `[thin]` | Product landing page — download, feature bullets. No automation content |
| [docs.getutm.app/installation/macos/](https://docs.getutm.app/installation/macos/) | `[thin]` | How a human installs UTM.app. No CLI/unattended install path |
| [scripting/reference/](https://docs.getutm.app/scripting/reference/) | `[meaty]` | Full AppleScript dictionary: UTM/Guest/Configuration/USB/Registry/Input suites, **the QEMU-guest-agent gate on the Guest Suite**, `apple configuration` field reference — [05](05-utm-automation.md), [06](06-utm-macos-guest.md) |
| [scripting/cheat-sheet/](https://docs.getutm.app/scripting/cheat-sheet/) | `[meaty]` | Worked AppleScript snippets for every suite, annotated for backend applicability — [05](05-utm-automation.md) |
| [advanced/remote-control/](https://docs.getutm.app/advanced/remote-control/) | `[meaty]` | `utm://` URL-scheme command table, Shortcuts/Automator recipes, improper-shutdown warnings — [05](05-utm-automation.md) |
| [advanced/headless/](https://docs.getutm.app/advanced/headless/) | `[meaty]` | Headless setup (delete display / serial-terminal device), dock-icon hiding — [05](05-utm-automation.md) |
| [preferences/macos/](https://docs.getutm.app/preferences/macos/) | `[thin]` | App-wide prefs incl. dock-icon toggle and UTM server remote-access settings — [05](05-utm-automation.md), [07](07-utm-settings-appendix.md) |
| [basics/actions/](https://docs.getutm.app/basics/actions/) | `[thin]` | GUI VM actions (start/pause/stop/clone/share). The AppleScript equivalents in `scripting/reference` supersede this for automation |
| [basics/controls/](https://docs.getutm.app/basics/controls/) | `[thin]` | GUI toolbar/input controls. No automation surface |
| [advanced/version/](https://docs.getutm.app/advanced/version/) | `[thin]` | How to read the UTM build version. No bearing on the harness |
| [utmapp/UTM discussion #3618](https://github.com/utmapp/UTM/discussions/3618) | `[meaty]` | The "Machines-as-code" IaC feature request and the maintainer's "a long way off" reply — direct source for **G1** — [05](05-utm-automation.md) |
| [utmapp/UTM issue #3718](https://github.com/utmapp/UTM/issues/3718) | `[thin]` | The tracked, still-open IaC-support issue referenced by the discussion above — [05](05-utm-automation.md) |

## UTM macOS guest support

| URL | Grade | What it gave us |
|---|---|---|
| [guest-support/macos/](https://docs.getutm.app/guest-support/macos/) | `[meaty]` | macOS 12+/Apple-Silicon-host requirement, IPSW sourcing, the master missing-features list, VirtioFS + network-sharing mount instructions, clipboard sharing steps — [06](06-utm-macos-guest.md) |
| [settings-apple/virtualization/](https://docs.getutm.app/settings-apple/virtualization/) | `[meaty]` | **The page the brief omitted.** Balloon, entropy, sound/keyboard/pointer (macOS 12+), trackpad (13+), Rosetta (13+), clipboard sharing — each with its guest-version gate — [06](06-utm-macos-guest.md) §9 |
| [advanced/disposable/](https://docs.getutm.app/advanced/disposable/) | `[thin]` | Single-sentence confirmation: disposable mode is QEMU-backend only — direct source for **G5** — [06](06-utm-macos-guest.md) |
| [advanced/multiple-displays/](https://docs.getutm.app/advanced/multiple-displays/) | `[thin]` | Single-sentence confirmation: no multi-display on Apple backend — direct source for **G6** — [06](06-utm-macos-guest.md) |
| [advanced/recovery/](https://docs.getutm.app/advanced/recovery/) | `[thin]` | 1TR recovery-mode boot, macOS 13+/Apple-backend-only, SIP-disable use case — [06](06-utm-macos-guest.md) |
| [advanced/serial/](https://docs.getutm.app/advanced/serial/) | `[thin]` | PTTY-vs-network-socket serial backends, `screen /dev/ttysNNN` connection pattern — [06](06-utm-macos-guest.md) |
| [advanced/rosetta/](https://docs.getutm.app/advanced/rosetta/) | `[thin]` | Confirms Rosetta (x86_64-on-ARM) applies to **Linux** guests only — direct source for **G7** |
| [guest-support/dynamic-resolution/](https://docs.getutm.app/guest-support/dynamic-resolution/) | `[thin]` | macOS 14+ Apple-backend auto-resolution vs QEMU's manual `xrandr` workaround — [06](06-utm-macos-guest.md) |
| [guides/guides/](https://docs.getutm.app/guides/guides/) | `[thin]` | Index of per-guest walkthroughs. All non-macOS except `classic-macos` |
| [guides/classic-macos/](https://docs.getutm.app/guides/classic-macos/) | `[thin]` | Confirmed out-of-scope: classic 68k/PPC Mac OS emulation, unrelated to macOS 12+ Apple-backend — [06](06-utm-macos-guest.md) |

## UTM settings pages (thin appendix)

| URL | Grade | What it gave us |
|---|---|---|
| [settings-apple/boot/](https://docs.getutm.app/settings-apple/boot/) | `[thin]` | OS selection, IPSW field — [07](07-utm-settings-appendix.md) |
| [settings-apple/drive/](https://docs.getutm.app/settings-apple/drive/) | `[thin]` | Drive fields incl. macOS 26+ ASIF format — [07](07-utm-settings-appendix.md) |
| [settings-apple/system/](https://docs.getutm.app/settings-apple/system/) | `[thin]` | CPU/memory fields — [07](07-utm-settings-appendix.md) |
| [settings-apple/information/](https://docs.getutm.app/settings-apple/information/) | `[thin]` | Cosmetic name/notes/icon — [07](07-utm-settings-appendix.md) |
| [settings-apple/sharing/](https://docs.getutm.app/settings-apple/sharing/) | `[thin]` | Shared-directory list — [07](07-utm-settings-appendix.md) |
| [settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/) | `[thin]` | Index only: add/remove a device. TOC = Display, Network, Serial — [07](07-utm-settings-appendix.md) |
| [settings-qemu/system/](https://docs.getutm.app/settings-qemu/system/) | `[thin]` | Contrast-only: QEMU arch/CPU/memory fields — [07](07-utm-settings-appendix.md) |
| [settings-qemu/qemu/](https://docs.getutm.app/settings-qemu/qemu/) | `[thin]` | Contrast-only: logging/UEFI/RNG/balloon/TPM/TSO toggles — [07](07-utm-settings-appendix.md) |
| [settings-qemu/sharing/](https://docs.getutm.app/settings-qemu/sharing/) | `[thin]` | Contrast-only: SPICE WebDAV/VirtFS sharing — [07](07-utm-settings-appendix.md) |
| [settings-qemu/input/](https://docs.getutm.app/settings-qemu/input/) | `[thin]` | Contrast-only: USB bus version/limits, N/A to Apple backend — [07](07-utm-settings-appendix.md) |
| [settings-qemu/information/](https://docs.getutm.app/settings-qemu/information/) | `[thin]` | Byte-identical to the Apple-backend information page — [07](07-utm-settings-appendix.md) |
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | `[thin]` | Index only: add/remove a device. TOC = Display, Network, Serial, Sound |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | `[meaty]` | Contrast-only: QEMU drive creation, importing, deletion, boot order, removable, interface, image type, raw images |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | `[thin]` | Index over Clipboard / Directory / USB sharing; the children carry the content (SPICE WebDAV, VirtFS backends) |

## Retraction — the G10 prune list was wrong

The research brief carried a ground truth **G10** instructing every agent that four URLs were 404 and
must not be fetched or cited. **Three of the four are live.** Verified with
`curl -sS -o /dev/null -w '%{http_code}' -L`:

| URL | G10 claimed | Actual |
|---|---|---|
| [settings-apple/devices/](https://docs.getutm.app/settings-apple/devices/) | 404 | **404** — the only true entry. Real path is `.../devices/devices/` |
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | 404 | **200** |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | 404 | **200** |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | 404 | **200** |

Two things made this durable:

1. **The instruction was self-sealing.** "Do not fetch, do not cite" guaranteed no agent could ever
   surface evidence against it. The lead's cross-check ledger marked G10 `verified` — but verifying a
   *don't-look* rule only confirms nobody looked.
2. **The brief's URL list omitted
   [settings-apple/virtualization/](https://docs.getutm.app/settings-apple/virtualization/)**, the page
   that actually documents the Apple-backend balloon/entropy/sound/keyboard/pointer/trackpad/Rosetta/
   clipboard toggles. `06` was ordered to produce that content, could not find it, and correctly recorded
   the gap — blaming the wrong cause.

The mis-pruned pages turned out to be mostly thin index/TOC pages, so little substance was lost. The real
loss was `settings-apple/virtualization/`, now written up in [06](06-utm-macos-guest.md) §9. **G10 is
retracted**; the ledger row in `.team/macos-ci.board.md` is marked accordingly. `just link-check` now
guards against a repeat.

## Local working trees (read directly, not fetched — G11)

| Path | Grade | What it gave us |
|---|---|---|
| `/Users/bossjones/dev/bossjones/zsh-dotfiles` | `[meaty]` | `.chezmoiroot`, `.chezmoiversion`, `home/.chezmoi.yaml.tmpl` (the `stdinIsATTY` non-interactive contract), `scripts/smoke-test-docker.sh` (canonical non-TTY invocation + assertion vocabulary), `test_dotfiles.py`, `CLAUDE.md`, `.github/workflows/tests.yml` — [08](08-dotfiles-test-harness.md), [09](09-dotfiles-under-test.md) |
| `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep` | `[meaty]` | `bin/zsh-dotfiles-prereq-installer`, `Brewfile`, `Makefile`, `TESTING.md`/`DEBUG.md`, `Dockerfile-{centos-9,debian-12,ubuntu-2204}` (the existing Linux coverage this repo has no macOS equivalent of) — [09](09-dotfiles-under-test.md) |

The two bootstrap one-liners quoted verbatim in [09](09-dotfiles-under-test.md) (G9):

| URL | Grade | What it gave us |
|---|---|---|
| [chezmoi.io/get](https://chezmoi.io/get) | `[meaty]` | The chezmoi installer the `zsh-dotfiles` bootstrap pipes into `sh` |
| [github.com/bossjones/zsh-dotfiles](https://github.com/bossjones/zsh-dotfiles) | `[meaty]` | The chezmoi source repo the bootstrap one-liner targets |
| [zsh-dotfiles-prereq-installer](https://raw.githubusercontent.com/bossjones/zsh-dotfiles-prep/main/bin/zsh-dotfiles-prereq-installer) | `[meaty]` | The prereq installer the `zsh-dotfiles-prep` bootstrap pipes into `bash` |

## Read as counter-evidence, never cited as support (G2)

| URL | Grade | What it gave us |
|---|---|---|
| [tonyyo11 — Prepping for Learning Terraform (Oct 2025)](https://tonyyo11.github.io/posts/October-Learning-Terraform/) | `[cited-as-exclusion]` | Uses Terraform to manage **Jamf Pro resources**, not VMs. Establishes **G2**: it is not evidence of VM-as-code for either tool. Referenced only in [10](10-tart-vs-utm-adr.md) to preempt the misreading |
| [motionbug — Baking Up Your Perfect Jamf Pro Test VM](https://motionbug.com/the-cookbook-baking-up-your-perfect-jamf-pro-test-vm/) | `[cited-as-exclusion]` | A Jamf-Pro-flavored VM cookbook. Same trap as above: adjacent tooling, not a VM-as-code story for tart or UTM |

## Known gaps — pages in neither the brief nor the source list

The docs nav exposes pages no agent was pointed at. None are load-bearing for the harness, but they exist
and are unread: `settings-apple/{display,network,port-forwarding,serial}`,
`settings-qemu/{display,network,port-forwarding,serial,sound}`, `settings-qemu/drive/resize-and-compress`,
`guest-support/{linux,windows,clipboard,directory,usb}`, `remote/utm-server`, and the `guides/*` per-guest
walkthroughs. Tracked in `.team/macos-ci.backlog.md`.
