# IPSW lane: builds from a pinned macOS restore image instead of cloning a cirruslabs OCI base,
# for the exact-point-release case macos-versions.toml's `[image."sequoia-15.6.1"]` shape
# describes (specs/macos-ci/12-tooling-and-agent-loop.md#macos-versionstoml---declarative-image-selection).
#
# `ipsw_url` has no default on purpose: the real MrMacintosh-sourced URL and its sha256 are not
# yet pinned in macos-versions.toml (that entry doesn't exist yet — template-half only, per this
# team's Step 6a split). Pass it explicitly: `packer build -var ipsw_url=... packer/ipsw/sequoia-15.6.1.pkr.hcl`.
#
# boot_command cribbed from ~/dev/markkenny/macos-virtualisation/Packs/vanilla-26.1.pkr.hcl
# (read-only reference, Setup Assistant navigation only — no MDM enrollment, that's not part of
# this harness). Every wait token below was checked against that file's own typo as a cautionary
# tale: its "Are you sure you want to skip signing in with an Apple ID?" step sends `<wai7s>`
# (a stray "7" where "t" belongs) instead of `<wait7s>` — corrected here.

packer {
  required_plugins {
    tart = {
      version = ">= 1.11.1"
      source  = "github.com/cirruslabs/tart"
    }
  }
}

variable "ipsw_url" {
  type        = string
  description = "Path or URL to the macOS IPSW restore image."
}

variable "vm_name" {
  type    = string
  default = "dotfiles-sequoia-15-6-1"
}

variable "ssh_username" {
  type    = string
  default = "admin"
}

variable "ssh_password" {
  type    = string
  default = "admin"
}

source "tart-cli" "ipsw" {
  from_ipsw = var.ipsw_url
  vm_name   = var.vm_name
  cpu_count = 4
  memory_gb = 8
  # 120GB, not the golden-image template's 60GB: this path performs a full macOS install from
  # scratch (Setup Assistant + first-boot provisioning), unlike the golden image's clone of an
  # already-installed base — matches markkenny/macos-virtualisation's vanilla-26.1.pkr.hcl sizing
  # for the same from_ipsw shape.
  disk_size_gb = 120
  # Only "raw" (default) or "asif" (macOS 26/Tahoe+ host only) apply here — and, unlike the
  # golden-image template's clone-from-vm_base_name lane where disk_format is inert
  # (specs/macos-ci/13-build-secrets.md#disk_format-does-not-mean-what-this-spec-used-to-say-it-meant),
  # this from_ipsw path is exactly where the field is live (specs/macos-ci/02-packer-tart-builder.md).
  # Set explicitly rather than relying on the implicit default.
  disk_format  = "raw"
  headless     = true
  ssh_username = var.ssh_username
  ssh_password = var.ssh_password
  ssh_timeout  = "120s"

  recovery_partition = "delete"

  # Setup Assistant, English (US), skip Apple ID / Location Services / Analytics, UTC, create the
  # admin account with ssh_username/ssh_password. Enables Voice Over briefly (leftAltOn f5) as the
  # accessibility-navigation trick that lets keystrokes drive Setup Assistant's non-standard
  # widgets, then disables it once through.
  boot_command = [
    "<wait60s><spacebar>",
    "<wait20s>italiano<esc>english<wait1s><enter>",
    "<wait30s>united states<leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait5s><tab><tab><tab><spacebar><tab><tab><wait1s><spacebar>",
    "<wait5s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait5s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait5s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait5s><tab><tab><tab><tab><tab><tab>${var.ssh_username}<tab>${var.ssh_username}<tab>${var.ssh_password}<tab>${var.ssh_password}<tab><tab><spacebar><tab><tab><wait1s><spacebar>",
    "<wait60s><leftAltOn><f5><leftAltOff>",
    "<wait6s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait7s><tab><spacebar>",
    "<wait6s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait6s><tab><spacebar>",
    "<wait6s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait6s><tab><wait1s><spacebar>",
    "<wait6s><tab><tab><tab>UTC<enter><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait6s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait6s><tab><tab><wait1s><spacebar>",
    "<wait6s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    "<wait6s><tab><tab><wait1s><spacebar>",
    "<wait20s><spacebar>",
    "<wait6s><leftAltOn><f5><leftAltOff>",
  ]

  run_extra_args    = ["--no-audio"]
  create_grace_time = "23s"
}

build {
  sources = ["source.tart-cli.ipsw"]

  provisioner "shell" {
    inline = [
      "echo 'ipsw lane: Setup Assistant automation only — no software provisioning yet'",
    ]
  }
}
