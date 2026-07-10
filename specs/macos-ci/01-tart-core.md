# 01 — Tart Core

Sources: [tart.run/quick-start/](https://tart.run/quick-start/), [tart.run/faq/](https://tart.run/faq/).
See [11-sources.md](11-sources.md) for the full audit trail.

## Install

```bash
brew install cirruslabs/cli/tart
```
— [tart.run/quick-start/](https://tart.run/quick-start/)

Manual install: download the release archive and invoke `./tart.app/Contents/MacOS/tart` (not a bare
binary) so it gets its privilege elevation from the app bundle's embedded provisioning profile.
— [tart.run/quick-start/](https://tart.run/quick-start/)

**Host requirement:** macOS 13.0 (Ventura) or later, Apple Silicon only.
— [tart.run/quick-start/](https://tart.run/quick-start/)

## Core CLI commands

| Command | Purpose |
|---|---|
| `tart clone <src> <name>` | Duplicate a local or remote (registry) image into a new local VM |
| `tart create <name>` | Build a new VM from scratch |
| `tart run <name>` | Boot a VM |
| `tart set <name>` | Modify VM configuration (CPU/RAM/disk/display/networking flags) |
| `tart list` | List local VMs |
| `tart delete <name>` | Remove a local VM |
| `tart ip <name>` | Resolve a running VM's IP address |
| `tart exec <name> <cmd>` | Execute a command inside a running VM (**requires the guest agent**) |
| `tart login <registry>` | Authenticate to an OCI registry |
| `tart push <name> <registry ref>` | Upload a local VM image to an OCI registry |
| `tart pull <registry ref>` | Download a remote image into the local cache |

— [tart.run/quick-start/](https://tart.run/quick-start/); verb list re-derived from `tart --help` (tart 2.32.1)

`tart --help` lists nine further verbs this table omits as out of scope: `create`, `get`, `logout`,
`import`, `export`, `prune`, `rename`, `stop`, `suspend`.

Default new-VM allocation (when not overridden): 2 CPUs, 4 GB RAM, 1024×768 display.
— [tart.run/quick-start/](https://tart.run/quick-start/)

## Prebuilt ghcr.io images

Available macOS base images: **Tahoe (26), Sequoia (15), Sonoma (14), Ventura (13), Monterey (12)** —
i.e. macOS 12 through 26, matching the ground-truth range. Each ships in three variants: `vanilla`,
`base`, `xcode`. Linux options include Ubuntu, Debian, and Fedora.
— [tart.run/quick-start/](https://tart.run/quick-start/)

**Default credentials for every prebuilt image: `admin` / `admin`** — valid for GUI, console, and SSH
access.
— [tart.run/quick-start/](https://tart.run/quick-start/)

That is not just a docs assertion; it is visible in the Packer templates that build these images.
[`templates/vanilla-tahoe.pkr.hcl:20-21`](https://github.com/cirruslabs/macos-image-templates/blob/main/templates/vanilla-tahoe.pkr.hcl)
sets `ssh_password = "admin"` and `ssh_username = "admin"`, and the same file's `boot_command` walks the
macOS setup assistant to enable **Remote Login** (stock `sshd`, password auth accepted). Two further
properties of every `vanilla-*` image follow from that same template's provisioner and matter downstream:

- **Passwordless sudo** for `admin` (`admin ALL=(ALL) NOPASSWD: ALL` dropped into `/etc/sudoers.d/`),
  which is why an unattended Homebrew or `chezmoi` run inside the guest never blocks on a password.
- **Auto-login** for `admin` (`autoLoginUser` + a pre-seeded `/etc/kcpassword`). This is directly
  relevant to the macOS 15+ keychain requirement (**G8**) below: the prebuilt images boot into a real
  GUI login session, which is the condition under which `login.keychain` is unlocked.

```bash
tart clone ghcr.io/cirruslabs/macos-sequoia-xcode:latest my-vm
tart run my-vm
tart ip my-vm
```
The image reference above is listed verbatim under
[quick-start/#vm-images](https://tart.run/quick-start/#vm-images) — it is not composed from command
patterns (ledger: `tart-quickstart-lists-sequoia-xcode-image`). The page also documents version-pinned
tags alongside `:latest`, e.g. `ghcr.io/cirruslabs/macos-monterey-xcode:15`.

## Shared directories (`--dir`)

```bash
tart run my-vm --dir=name:/path/on/host
tart run my-vm --dir=name:/path/on/host:ro   # read-only
```
Repeat `--dir` for multiple mounts. macOS guests auto-mount shares under
`/Volumes/My Shared Files/<name>`; Linux guests require a manual mount at `/mnt/shared`.
— [tart.run/quick-start/](https://tart.run/quick-start/)

## OCI registry push/pull

Tart works with any OCI-compatible registry (not a proprietary format).
— [tart.run/faq/](https://tart.run/faq/)

```bash
tart login registry.io
tart push local-vm registry.io/org/name:tag
tart clone registry.io/org/name:tag local-name    # pull + materialize as a local VM
```
— [tart.run/quick-start/](https://tart.run/quick-start/)

## Networking: NAT vs bridged

- **Default: NAT.** Reach host services via the router IP: `netstat -nr | awk '/default/{print $2; exit}'`.
- **Bridged:** `tart run my-vm --net-bridged=en0`. IP resolution needs the ARP resolver instead of the
  default DHCP lookup: `tart ip my-vm --resolver=arp`. Bridged IP resolution "heavily relies on the
  level of VM's activity on the network" — an idle bridged VM may not answer ARP promptly.
- Linux guests on bridged networking may need Samba installed for ARP resolution to work, and Ubuntu
  guests can exhibit DUID-EN DHCP identifier issues.

— [tart.run/faq/](https://tart.run/faq/)

`tart ip` takes **three** resolvers, not two: `tart ip <vm> --resolver <dhcp|arp|agent>`, defaulting to
`dhcp` (`tart ip --help`). The third, `agent`, asks the Tart guest agent for the address rather than
inferring it from the host's DHCP lease file or ARP table — see below.

## The Tart guest agent

Tart ships a guest agent, [`tart-guest-agent`](https://github.com/openai/tart-guest-agent), and **the
prebuilt `base` and `xcode` images preinstall it**: `templates/base.pkr.hcl:167` runs
`brew install cirruslabs/cli/tart-guest-agent` and installs it twice, as a `LaunchDaemon`
(`org.cirruslabs.tart-guest-daemon`) and as a `LaunchAgent` (`org.cirruslabs.tart-guest-agent`).
— [`templates/base.pkr.hcl`](https://github.com/cirruslabs/macos-image-templates/blob/main/templates/base.pkr.hcl)

The agent's canonical repo is now `openai/tart-guest-agent`; `tart run --help` and the Homebrew formula
still spell it `cirruslabs/...`, which redirects. `cirruslabs/tart` itself likewise redirects to
`openai/tart`. **This has licensing implications that [04](04-tart-licensing-risk.md) does not yet
account for** — see the open question recorded there.

It backs three capabilities referenced elsewhere in these specs:

- `tart ip <vm> --resolver=agent`, the third resolver above.
- **`tart exec <vm> <command>`** — `tart exec --help` states *"Requires Tart Guest Agent running in a guest
  VM."*
- Clipboard sharing, which `tart run --help` states "requires spice-vdagent package on Linux and
  `https://github.com/cirruslabs/tart-guest-agent` on macOS".

This is the structural asymmetry with the UTM lane, and `exec` is where it bites hardest. A UTM
**Apple-backend** macOS guest cannot run the QEMU guest agent that `utmctl exec` / `file` / `ip-address`
require, so those verbs are unavailable there (see [05 §4](05-utm-automation.md) and the ADR in
[10](10-tart-vs-utm-adr.md)). Tart ships the equivalent agent, preinstalls it in the images the harness
actually uses, and exposes `tart exec` on top of it. The two lanes are not "different syntax for the same
capability" — one has in-guest command execution and IP resolution, the other structurally cannot.

Note the `vanilla` variant does **not** include the agent; it is added by `base.pkr.hcl`, which is layered
on top of `vanilla`. `tart exec --help` says the same from the tool's own mouth: *"all non-vanilla Cirrus
Labs VM images already have the Tart Guest Agent installed."* So a harness that clones `vanilla` gets
neither `tart exec` nor `--resolver=agent`.

## Disk resize (recovery-partition path)

Manual procedure via recovery boot:
```bash
diskutil list physical                       # identify disk (run inside guest)
tart run my-vm --recovery                     # boot into recovery
# inside recovery:
diskutil eraseVolume free free disk0s3        # remove recovery partition
yes | diskutil repairDisk disk0               # repair
diskutil apfs resizeContainer disk0s2 0       # expand container to fill disk
```
— [tart.run/faq/](https://tart.run/faq/)

The FAQ notes the Packer builder's `disk_size_gb` and `recovery_partition` directives are the
alternative to doing this by hand — see [02-packer-tart-builder.md](02-packer-tart-builder.md).
— [tart.run/faq/](https://tart.run/faq/)

## `~/.tart` layout and pruning

- `~/.tart/vms/` — local VM images (created via `clone`/`create`).
- `~/.tart/cache/OCIs/` — pulled remote images cached by digest/tag.

Tart auto-prunes least-recently-accessed cached images when disk space runs low.

**`--prune-limit` is not a cache-size cap.** The FAQ says `tart clone` *"limits this automatic pruning to
100 GB by default **to avoid removing too many cached items**"* — the 100 GB bounds how much a single
automatic prune may **reclaim**, not how large the cache may grow. `tart clone --help` agrees: *"limit
automatic pruning to n gigabytes (default: 100)"*. The flag lives on `tart clone` only; it is absent from
`tart pull --help` and `tart run --help`.

Disable auto-pruning entirely with the `TART_NO_AUTO_PRUNE` environment variable, either exported
globally or set per `tart pull` / `tart clone` invocation. Explicit pruning is a separate verb,
`tart prune`, whose `--space-budget <n>` *is* a size budget.
— [tart.run/faq/#automatic-pruning](https://tart.run/faq/#automatic-pruning), `tart clone --help`,
`tart prune --help`

## Headless mode and the macOS 15+ keychain requirement (G8)

Starting with the host running **macOS 15 (Sequoia) or later**, Virtualization.Framework carries an
*"undocumented requirement […] to have an unlocked `login.keychain` available at the times when running a
VM."* Running headless (no GUI session, e.g. over SSH or in CI) without one fails with
`SecKeyCreateRandomKey_ios failed`, `Failed to generate keypair`, or
`Interaction is not allowed with the Security Server`.

Mitigations documented in the FAQ:
- Ensure a GUI login session has unlocked the keychain, or
- Create *and unlock* a keychain non-interactively. This is a **three-command sequence** — `create-keychain`
  alone neither unlocks the keychain nor makes it the login keychain, so a runner that issues only the
  first command still fails to boot:
  ```bash
  security create-keychain -p '' login.keychain
  security unlock-keychain -p '' login.keychain
  security login-keychain -s login.keychain
  ```
  The FAQ notes this approach is *"fully automated, but might stop working at some point in the future"*,
  and that `-p ''` creates a keychain with an **empty password** — supply a real value, or omit `-p` to be
  prompted.

— [tart.run/faq/#headless-machines](https://tart.run/faq/#headless-machines)

This directly affects the dotfiles-test harness (see
[08-dotfiles-test-harness.md](08-dotfiles-test-harness.md)): any headless/CI runner driving `tart run`
on a macOS 15+ host must unlock/create a login keychain as part of its bootstrap, or VM boot will fail.

## Nested virtualization limits (G8)

Nested virtualization is **supported only on M3 or M4 chips**, running **macOS 15 (Sequoia) or later**,
and **only for Linux guest VMs** — not macOS guests. Enable with the `--nested` flag on `tart run`.
— [tart.run/faq/](https://tart.run/faq/)

## Gaps in these two sources

The quick-start and FAQ pages do not document: exact `tart create` flag syntax for CPU/RAM/disk sizing,
`tart set` full flag reference, or VNC/display flags beyond what's implied. Where the harness or builder
spec (02) needs those, it either cites the Packer builder field reference (which overrides `tart create`
defaults) or marks the claim `<!-- UNVERIFIED -->`.
