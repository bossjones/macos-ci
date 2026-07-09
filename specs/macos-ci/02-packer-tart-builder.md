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
| `pull_concurrency` | number* | Number of layers to pull concurrently from the OCI registry. <!-- UNVERIFIED: HashiCorp page lists this as boolean, which looks like a docs typo for a concurrency count; flagged rather than silently "corrected". --> |

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
| `disk_format` | string | `"raw"` (default) or `"asif"`. ASIF (Apple Sparse Image Format) is faster but requires macOS 26 (Tahoe)+. |
| `recovery_partition` | string | `"delete"` (allows disk resize, smaller image, breaks OS updates) / `"keep"` (blocks resize, larger image, updates work) / `"relocate"` (moves partition to end of disk). |

Display/boot:

| Field | Type | Description |
|---|---|---|
| `display` | string | `<width>x<height>`, e.g. `1200x800`. |
| `headless` | bool | Hide the GUI. Useful to disable when debugging `boot_command`. |
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

SSH communicator:

| Field | Type | Description |
|---|---|---|
| `ssh_username` | string | SSH user for provisioning steps. |
| `ssh_password` | string | SSH password for provisioning steps. |

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

— all fields: [developer.hashicorp.com](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart)

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
