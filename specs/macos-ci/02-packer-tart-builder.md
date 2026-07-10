# 02 — Packer `tart` Builder

Sources: [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart)
(installation/README — **thin stub**, see below),
[developer.hashicorp.com — tart builder component](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart)
(**canonical field reference**, used below),
[github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation) (reference
implementation). See [11-sources.md](11-sources.md) for the full audit trail.

## Which source is authoritative

The `packer-plugin-tart` GitHub README is a **thin stub**: install instructions, a macOS 15 requirement
note, and a local-network-permission workaround. It explicitly defers configuration docs to HashiCorp's
site: *"For more information on how to configure the plugin, please read the documentation located on
the HashiCorp's website."* — [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart)

All field definitions below are from the **HashiCorp integrations page**, which is the canonical
reference for this builder.
— [developer.hashicorp.com](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart)

## Install

```hcl
packer {
  required_plugins {
    tart = {
      version = ">= 1.11.1"
      source  = "github.com/cirruslabs/tart"
    }
  }
}
```
then `packer init`.

**Requirement: macOS 15 (Sequoia) or later** on the build host, and a recent Packer version.
— [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart)

### Known Sequoia issue: SSH "No route to host"

Sequoia's Local Network permission model can block the plugin's SSH provisioner connection to the guest,
surfacing as:
```
ssh: connect to host [...] port 22: No route to host
```
Workaround (requires reboot after applying):
```bash
sudo defaults write com.apple.network.local-network AllowedEthernetLocalNetworkAddresses -array "10.0.0.0/8" "172.16.0.0/12" "192.168.0.0/16"
sudo defaults write com.apple.network.local-network AllowedWiFiLocalNetworkAddresses -array "10.0.0.0/8" "172.16.0.0/12" "192.168.0.0/16"
```
— [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart)

This is separate from, but compounds with, the macOS 15+ headless keychain requirement documented in
[01-tart-core.md](01-tart-core.md#headless-mode-and-the-macos-15-keychain-requirement-g8) — a golden-image
build host on Sequoia+ may need both fixes applied before an unattended `packer build` succeeds.

## Full field reference

Source of truth VM (pick exactly one origin):

| Field | Type | Description |
|---|---|---|
| `vm_name` | string | Name of the VM to create (required when `from_ipsw`, `from_iso`, or `vm_base_name` is used) and run. |
| `vm_base_name` | string | Name of the VM used for initial cloning — local VM or a remote VM pulled from a registry. |
| `from_ipsw` | string | Path/URL/`latest` — IPSW to initialize a **macOS** VM from. |
| `from_iso` | list(string) | Absolute path(s) to ISO file(s) to initialize a **Linux** VM from. |

Registry/pull:

| Field | Type | Description |
|---|---|---|
| `allow_insecure` | bool | Connect to the OCI registry over insecure HTTP when cloning. |
| `always_pull` | bool | Always `tart pull` before `tart clone` so the base image is up to date before building. |
| `pull_concurrency` | number | Number of layers to pull concurrently from the OCI registry. Default `4`. The docs page annotates this **`(boolean)`** — that is an upstream docs bug, see below. |

> **`pull_concurrency` is a count, not a flag.** The field reference annotates it `(boolean)` and then, in
> the same sentence, says *"Default is 4 for Tart 2.0.0+"* — a boolean with a default of 4. The plugin's
> own source settles it: it is declared
> [`PullConcurrency uint16`](https://github.com/cirruslabs/packer-plugin-tart/blob/main/builder/tart/builder.go)
> (`builder/tart/builder.go:36`), typed `cty.Number` in the generated HCL2 spec
> (`builder/tart/builder.hcl2spec.go:190`), and forwarded verbatim to `tart clone --concurrency %d`
> (`builder/tart/step_clone_vm.go:24`) — whose own default is 4 per `tart clone --help`. Writing
> `pull_concurrency = true` would be rejected by the HCL decoder. The `(boolean)` annotation is an
> upstream documentation bug and is still live; it is recorded here rather than silently corrected.

VM resources (override `tart create` defaults when using `from_ipsw`/`from_iso`; override VM settings
when using `vm_base_name`):

| Field | Type | Description |
|---|---|---|
| `cpu_count` | number | Virtual CPUs for the new VM. |
| `memory_gb` | number | Unified memory (GB) for the new VM. |
| `disk_size_gb` | number | Disk size (GB) for the new VM. |

Disk/storage:

| Field | Type | Description |
|---|---|---|
| `disk_format` | string | `"raw"` (default) or `"asif"`. ASIF (Apple Sparse Image Format) is faster but requires macOS 26 (Tahoe)+. **Only applies when using `from_ipsw` or `from_iso`.** |
| `recovery_partition` | string | `"delete"` (allows disk resize, smaller image, breaks OS updates) / `"keep"` (blocks resize, larger image, updates work) / `"relocate"` (moves partition to end of disk). Defaults to `""`, *"currently equivalent to `"delete"`"* — upstream reserves the right to change that, so set it explicitly. |

> **`disk_format` does not reach a clone-from-base build.** The field reference states *"Only applies when
> using `from_ipsw` and `from_iso`."* The golden-image sketch below builds from `vm_base_name`, so its disk
> inherits the base image's format and `disk_format` is inert. This scopes
> [OQ-01](../../.team/macos-ci.open-questions.md): the question of whether `asif`'s sparse allocation
> preserves deleted-secret residue only arises for a `from_ipsw`/`from_iso` build, not for the clone-from-
> `ghcr.io` path this harness actually takes. `tart create --help` corroborates the format list and the
> macOS 26 floor independently of the HashiCorp page.

Display/boot:

| Field | Type | Description |
|---|---|---|
| `display` | string | `<width>x<height>`, e.g. `1200x800`. |
| `headless` | bool | `true` hides the GUI. Useful to disable when debugging `boot_command`. (The field reference's wording, *"Whether to show graphics interface of a VM"*, reads as the inverse of the field's name; the source settles it — `Headless` ⇒ `tart run --no-graphics`.) |
| `boot_command` | []string | Keystrokes typed on first boot — enough to kick off the OS installer, not the full install. |
| `boot_wait` | duration | Wait after boot before typing `boot_command`. Default `10s`. |
| `boot_key_interval` | duration | Delay between individual key presses. |
| `boot_keygroup_interval` | duration | Delay after sending a group of key presses. |

Runtime/behavior:

| Field | Type | Description |
|---|---|---|
| `create_grace_time` | duration | Extra wait after install finishes, to work around Virtualization.Framework's install process lingering in the background. |
| `recovery` | bool | Boot in recovery mode — useful to auto-disable SIP on already-created VMs. |
| `rosetta` | string | Enable Rosetta for a **Linux** guest VM (x86_64 binaries) — this is the same Linux-guest-only Rosetta feature as G7, not a macOS-guest capability. |
| `run_extra_args` | list(string) | Extra args passed to `tart run`, e.g. `["--net-bridged=en0"]` for bridged networking. |
| `ip_extra_args` | list(string) | Extra args passed to `tart ip`, e.g. `["--resolver=arp"]` when using bridged networking. |

> **`headless = false` may not work against tart 2.32.1.** When `headless` is false the plugin appends
> `--graphics` to `tart run` (`builder/tart/step_run.go:43`, plugin v1.21.0), but `tart run --help` on
> tart 2.32.1 advertises `--no-graphics` and **no `--graphics` option at all**. Whether tart's argument
> parser silently accepts `--graphics` as the inverse half of a flag pair, or rejects it, cannot be
> settled without invoking `tart run`, which this run's scope forbids.
> <!-- UNVERIFIED: whether `tart run --graphics` parses on tart 2.32.1; settling it requires invoking `tart run`, which scope forbids. See OQ-15. -->
> Keep `headless = true` (the harness default) and the question never arises.

SSH communicator:

| Field | Type | Description |
|---|---|---|
| `ssh_username` | string | SSH user for provisioning steps. |
| `ssh_password` | string | SSH password for provisioning steps. |
| `ssh_timeout` | duration | Not listed in the field reference's own table, but used by its own example (`ssh_timeout = "120s"`) and by every `vanilla-*` template in `macos-image-templates`. |

**Do not mark `ssh_password` `sensitive`.** Packer's masking is value-based and global, not
variable-scoped: it redacts every occurrence of the *string*, wherever it appears. Since the value here
is `admin` — the public, documented credential for every prebuilt tart image
([01](./01-tart-core.md)) — marking it sensitive would rewrite every build log's `admin` to
`<sensitive>` and protect nothing. See [13-build-secrets.md](./13-build-secrets.md#sensitive-masks-values-not-variables).

**Build-time secrets** (`HOMEBREW_GITHUB_API_TOKEN` and friends) are injected through the shell
provisioner's environment and never written to the guest disk:
[13-build-secrets.md](./13-build-secrets.md).

HTTP server (for serving install-time payloads to the guest, e.g. autoinstall/cloud-init files):

| Field | Type | Description |
|---|---|---|
| `http_directory` | string | Directory served over HTTP to the VM. |
| `http_content` | map[string]string | Inline path→content map, alternative to `http_directory` (mutually exclusive). |
| `http_port_min` / `http_port_max` | int | Port range for the HTTP server. Defaults `8000`/`9000`. |
| `http_bind_address` | string | Bind address, defaults `0.0.0.0`. |
| `http_network_protocol` | string | `tcp` (default) / `tcp4` / `tcp6` / `unix` / `unixpacket`. |

VNC:

| Field | Type | Description |
|---|---|---|
| `disable_vnc` | bool | Disable the VNC connection used to drive `boot_command`. Default `false`. Cannot use `boot_command` when `true`. |

> **There are no `vnc_port_min` / `vnc_port_max` fields.** The builder's entire VNC surface is
> `disable_vnc` plus `boot_key_interval`. No `vnc_port*` key appears in the field reference, nor anywhere
> in the plugin's source — including `builder/tart/builder.hcl2spec.go`, the generated spec that
> enumerates *every* field the builder accepts. Any spec asserting those fields is citing something that
> does not exist; see the CONFLICT filed against
> [12-tooling-and-agent-loop.md](12-tooling-and-agent-loop.md):330.

— all fields: [developer.hashicorp.com](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart)
(rendered from the plugin repo's own
[`.web-docs/`](https://github.com/cirruslabs/packer-plugin-tart/tree/main/.web-docs) — this page is
**absent from HashiCorp's sitemap yet returns HTTP 200**; see [11-sources.md](11-sources.md) on the G19
sitemap exception. Do not "refute" it by grepping the sitemap.)

### Golden-image build sketch

```hcl
source "tart-cli" "golden" {
  vm_base_name   = "ghcr.io/cirruslabs/macos-sequoia-base:latest"
  vm_name        = "dotfiles-golden"
  cpu_count      = 4
  memory_gb      = 8
  disk_size_gb   = 60
  headless       = true
  ssh_username   = "admin"
  ssh_password   = "admin"
  recovery_partition = "delete"
}

build {
  sources = ["source.tart-cli.golden"]
  provisioner "shell" {
    inline = ["xcode-select --install || true"]
  }
}
```
<!-- UNVERIFIED: composed example combining documented fields; not a block quoted verbatim from either source. -->

This golden-image approach — build once with Packer, then `tart clone` per test run — is the harness's
recommended pattern; see
[08-dotfiles-test-harness.md](08-dotfiles-test-harness.md#a-golden-image-vs-from-scratch-per-test).

### Future optimization: pre-pulling the base image (`tart pull`)

**Not implemented — DEFERRED, purely additive.** Recorded here so it isn't re-discovered the hard
way. Observed on this team's first `just build-golden` run against a cold host (not a ledger claim,
just this run's own `packer` output): the provisioner step (Xcode CLT + Homebrew + prereqs) is
comparatively fast next to the time spent pulling `ghcr.io/cirruslabs/macos-sequoia-vanilla:latest`
— 23.7GB compressed — over the network. Nothing about `packer/tart-golden-image.pkr.hcl` forces that
repull on every build; it happens because the image isn't in `tart`'s local cache yet on a clean
host, and every clean-cache rebuild pays for it again.

The fix is a pre-pull, not a template change — `tart` already caches OCI images locally:

```bash
tart pull ghcr.io/cirruslabs/macos-sequoia-vanilla:latest
```

`tart pull` fetches the image into `tart`'s local cache once. Every subsequent clone of
`vm_base_name = "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest"` — via `packer build
packer/tart-golden-image.pkr.hcl`, `tart clone` directly, or a re-run after `tart delete`-ing the
golden VM — then clones from that local cache instead of the network. This is the opposite lever
from `always_pull` (above), which forces a fresh pull on *every* build to guarantee freshness: pull
once, explicitly, and every later build skips the network by leaving `always_pull` unset (as
`packer/tart-golden-image.pkr.hcl` already does).

**Proposed `just images-cache` recipe** — not yet in the Justfile (🛠 harness-builder owns
`Justfile`; recorded here as the exact body to add, mirroring `macos-versions.toml`'s two `[image.*]`
entries):

```just
# Pre-pull every declared image's OCI layers into tart's local cache once, so future
# `build-golden`/`build-ipsw` runs clone locally instead of re-pulling tens of GB over the network.
images-cache:
    @echo "📥 Pre-pulling base images into the local tart cache"
    @tart pull ghcr.io/cirruslabs/macos-sequoia-vanilla:latest
    @tart pull ghcr.io/cirruslabs/macos-tahoe-vanilla:latest
```
<!-- UNVERIFIED: recipe body composed from the `tart pull`/`vm_base_name` cache relationship
documented above; not executed, and not yet added to the Justfile. -->

Manual equivalent, no Justfile change required: `tart pull ghcr.io/cirruslabs/macos-sequoia-vanilla:latest`
(swap `-tahoe-` for the other lane's ref in [macos-versions.toml](../../macos-versions.toml)).

This is purely additive: it changes nothing about `packer/tart-golden-image.pkr.hcl` or any build
already in flight, and only removes redundant network time from *future* builds.

## Reference implementation: markkenny/macos-virtualisation

This repo is a real-world Packer+Tart pipeline, useful as a second data point beyond the field reference.

**Scripts:**
- `Packer.sh` — sanity-checks the environment, lists local `.pkr.hcl` files, and drives the build to
  `~/.tart/vms/`. Documented build time: **15–20 minutes** (the author's stated goal was to get this
  under 10 minutes via faster `boot_command`/`boot_wait` tuning, but 15–20 min is what's documented).
- `Tarter.sh` — post-build utility: lists installed VMs, and offers clone / randomize-serial-and-MAC /
  run. Runs VMs under `nohup` so they outlive the invoking script. Host user folders are mounted at
  `/Volumes/My Shared Files/Home` (the same auto-mount convention documented in
  [01-tart-core.md](01-tart-core.md#shared-directories---dir)).

**IPSW sourcing:** local path or HTTPS URL; the project points at MrMacintosh's IPSW database as a
source for installer images.

**Clone-and-run pattern:**
```bash
CLONE="MyTest"
tart clone $MASTER $CLONE
tart set $CLONE --display-refit --random-serial --random-mac
tart run $CLONE
```
A cloned VM only runs for the lifetime of the `tart run` invocation; `tart list` shows all clones
regardless of run state.
— [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation)

**Ansible during build:** the project uses Ansible to apply macOS updates during the build, which
requires Python — installed transitively via Xcode Command Line Tools. Update provisioning is optional;
`playbook-system-updater.yml` defaults to admin credentials, overridable via environment variables.
— [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation)

This is a **different repo's** choice to use Ansible for OS-update provisioning during image *build*. It
is not evidence for or against Ansible in *this* repo's dotfiles-install *test harness* — that decision
is made independently in [08-dotfiles-test-harness.md](08-dotfiles-test-harness.md#e-decision-ansible--reject-it)
per G9.

**Config toggles:** exposed via a `.pkr.hcl.env` file:
- `enable_passwordless_sudo`
- `enable_auto_login`
- `enable_clipboard_sharing`
- Safari-automation and Spotlight-disable options

— [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation)
