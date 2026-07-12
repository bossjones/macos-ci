# IPSW lane: builds from a pinned macOS restore image instead of cloning a cirruslabs OCI base,
# for the exact-point-release case macos-versions.toml's `[image."sequoia-15.6.1"]` shape
# describes (specs/macos-ci/12-tooling-and-agent-loop.md#macos-versionstoml---declarative-image-selection).
#
# `ipsw_url` has no default on purpose: the real MrMacintosh-sourced URL and its sha256 are not
# yet pinned in macos-versions.toml (that entry doesn't exist yet — template-half only, per this
# team's Step 6a split). Pass it explicitly: `packer build -var ipsw_url=... packer/ipsw/sequoia-15.6.1.pkr.hcl`.
#
# PROVENANCE (rewritten 2026-07-11, specs/prereq-mvp.md WS-A). The boot_command and the system
# provisioners below are adopted from the canonical upstream template
# ~/dev/cirruslabs/macos-image-templates/templates/vanilla-sequoia.pkr.hcl — the template that
# builds the very `macos-sequoia-vanilla` image the golden lane clones, and which pins the SAME
# 15.6.1 restore image this lane targets (donor line 16: UniversalMac_15.6.1_24G90_Restore.ipsw).
# The previous revision cribbed its keystrokes from a Tahoe 26.1 donor and was materially wrong for
# Sequoia: it typed the account fields with Tahoe's tab layout, and — fatally — it carried no
# post-Setup-Assistant tail at all, so the guest booted with Remote Login OFF and Packer's SSH
# communicator could never connect. Every build would have died at ssh_timeout.
#
# HONESTY: this sequence is adopted from the canonical template but has NOT been observed
# end-to-end on this host — a live from_ipsw build is an hours-long affair, out of scope for the
# rewrite. What IS proven: `packer validate` accepts it, and the two load-bearing steps (Remote
# Login, Gatekeeper) are pinned by ledger claims. The mitigation for the rest is that these
# keystrokes are cirruslabs' own, monthly-rebuilt against this exact IPSW, not authored here.

packer {
  required_plugins {
    tart = {
      # >= 1.16.0, not the golden lane's >= 1.11.1: the `<click 'Select Your Country or Region'>`
      # token in boot_command below was introduced in plugin v1.16.0. An older plugin cannot drive
      # that step.
      version = ">= 1.16.0"
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
  # already-installed base.
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
  ssh_timeout  = "180s"

  # "keep", deliberately diverging from the golden lane's "delete": per the donor, keeping the
  # recovery partition is what makes `softwareupdate` work inside the guest — and this lane's third
  # provisioner installs the Xcode CLT via exactly that command.
  recovery_partition = "keep"

  # Setup Assistant navigation, adopted from the donor (lines 24-106) with exactly two
  # substitutions: the account-creation fields and the two sudo-password prompts interpolate
  # var.ssh_username / var.ssh_password instead of being hardcoded to "admin".
  boot_command = [
    # hello, hola, bonjour, etc.
    "<wait60s><spacebar>",
    # Language: most of the times we have a list of "English"[1], "English (UK)", etc. with
    # "English" language already selected. If we type "english", it'll cause us to switch
    # to the "English (UK)", which is not what we want. To solve this, we switch to some other
    # language first, e.g. "Italiano" and then switch back to "English". We'll then jump to the
    # first entry in a list of "english"-prefixed items, which will be "English".
    #
    # [1]: should be named "English (US)", but oh well 🤷
    "<wait30s>italiano<esc>english<enter>",
    # Select Your Country or Region
    "<wait30s><click 'Select Your Country or Region'><wait5s>united states<leftShiftOn><tab><leftShiftOff><spacebar>",
    # Transfer Your Data to This Mac
    "<wait10s><tab><tab><tab><spacebar><tab><tab><spacebar>",
    # Written and Spoken Languages
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Accessibility
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Data & Privacy
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Create a Mac Account. Sequoia types the full name FIRST, then account name, then the password
    # twice — with no leading tabs. (The Tahoe layout this file used to carry opened with six
    # <tab>s and would have dropped every keystroke into the wrong field.)
    "<wait10s>${var.ssh_username}<tab>${var.ssh_username}<tab>${var.ssh_password}<tab>${var.ssh_password}<tab><tab><spacebar><tab><tab><spacebar>",
    # Enable Voice Over
    "<wait120s><leftAltOn><f5><leftAltOff>",
    # Sign In with Your Apple ID
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Are you sure you want to skip signing in with an Apple ID?
    "<wait10s><tab><spacebar>",
    # Terms and Conditions
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # I have read and agree to the macOS Software License Agreement
    "<wait10s><tab><spacebar>",
    # Enable Location Services
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Are you sure you don't want to use Location Services?
    "<wait10s><tab><spacebar>",
    # Select Your Time Zone
    "<wait10s><tab><tab>UTC<enter><leftShiftOn><tab><tab><leftShiftOff><spacebar>",
    # Analytics
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Screen Time
    "<wait10s><tab><spacebar>",
    # Siri
    "<wait10s><tab><spacebar><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Choose Your Look
    "<wait10s><leftShiftOn><tab><leftShiftOff><spacebar>",
    # Update Mac Automatically
    "<wait10s><tab><spacebar>",
    # Welcome to Mac
    "<wait10s><spacebar>",
    # Disable Voice Over
    "<leftAltOn><f5><leftAltOff>",
    # Enable Keyboard navigation
    # This is so that we can navigate the System Settings app using the keyboard
    "<wait10s><leftAltOn><spacebar><leftAltOff>Terminal<enter>",
    "<wait10s>defaults write NSGlobalDomain AppleKeyboardUIMode -int 3<enter>",
    "<wait10s><leftAltOn>q<leftAltOff>",
    # Now that the installation is done, open "System Settings"
    "<wait10s><leftAltOn><spacebar><leftAltOff>System Settings<enter>",
    # Navigate to "Sharing"
    "<wait10s><leftCtrlOn><f2><leftCtrlOff><right><right><right><down>Sharing<enter>",
    # Navigate to "Screen Sharing" and enable it
    "<wait10s><tab><tab><tab><tab><tab><tab><tab><spacebar>",
    # Navigate to "Remote Login" and enable it. This is the step that makes the guest reachable at
    # all: a from_ipsw guest boots with Remote Login OFF, so without it Packer's SSH communicator
    # never connects and the build dies at ssh_timeout. Pinned by the ledger claim
    # ipsw-boot-command-enables-remote-login.
    "<wait10s><tab><tab><tab><tab><tab><tab><tab><tab><tab><tab><tab><tab><spacebar>",
    # Quit System Settings
    "<wait10s><leftAltOn>q<leftAltOff>",
    # Disable Gatekeeper (1/2)
    "<wait10s><leftAltOn><spacebar><leftAltOff>Terminal<enter>",
    "<wait10s>sudo spctl --global-disable<enter>",
    "<wait10s>${var.ssh_password}<enter>",
    "<wait10s><leftAltOn>q<leftAltOff>",
    # Disable Gatekeeper (2/2)
    "<wait10s><leftAltOn><spacebar><leftAltOff>System Settings<enter>",
    "<wait10s><leftCtrlOn><f2><leftCtrlOff><right><right><right><down>Privacy & Security<enter>",
    "<wait10s><leftShiftOn><tab><leftShiftOff><leftShiftOn><tab><leftShiftOff><leftShiftOn><tab><leftShiftOff><leftShiftOn><tab><leftShiftOff><leftShiftOn><tab><leftShiftOff><leftShiftOn><tab><leftShiftOff><leftShiftOn><tab><leftShiftOff>",
    "<wait10s><down><wait1s><down><wait1s><enter>",
    "<wait10s>${var.ssh_password}<enter>",
    "<wait10s><leftShiftOn><tab><leftShiftOff><wait1s><spacebar>",
    # Quit System Settings
    "<wait10s><leftAltOn>q<leftAltOff>",
  ]

  run_extra_args = ["--no-audio"]

  # A (hopefully) temporary workaround for Virtualization.Framework's installation process not
  # fully finishing in a timely manner (the donor's own rationale, donor line 108).
  create_grace_time = "30s"
}

build {
  sources = ["source.tart-cli.ipsw"]

  # SYSTEM provisioners only, adopted from the donor (lines 119-164). Deliberately NO software:
  # Homebrew/mise/CI agents live in the donor's base.pkr.hcl, which is built ON TOP of vanilla —
  # not here. This lane's output is meant to be vanilla-equivalent, i.e. interchangeable with the
  # cirruslabs base that packer/tart-golden-image.pkr.hcl clones and layers tooling onto.
  # The donor's fourth provisioner (ansible system-updater) is intentionally not adopted.
  provisioner "shell" {
    inline = [
      # Enable passwordless sudo
      "echo ${var.ssh_password} | sudo -S sh -c \"mkdir -p /etc/sudoers.d/; echo '${var.ssh_username} ALL=(ALL) NOPASSWD: ALL' | EDITOR=tee visudo /etc/sudoers.d/${var.ssh_username}-nopasswd\"",
      # Enable auto-login.
      #
      # This hex is NOT interpolated, on purpose: it is the kcpassword-obfuscated form of the
      # LITERAL password "admin" (see https://github.com/xfreebird/kcpassword). If ssh_password is
      # ever overridden to something else, this line silently encodes the WRONG password and
      # auto-login breaks — the hex would have to be regenerated for the new value.
      "echo '00000000: 1ced 3f4a bcbc ba2c caca 4e82' | sudo xxd -r - /etc/kcpassword",
      "sudo defaults write /Library/Preferences/com.apple.loginwindow autoLoginUser ${var.ssh_username}",
      # Disable screensaver at login screen
      "sudo defaults write /Library/Preferences/com.apple.screensaver loginWindowIdleTime 0",
      # Disable screensaver for the admin user
      "defaults -currentHost write com.apple.screensaver idleTime 0",
      # Prevent the VM from sleeping
      "sudo systemsetup -setsleep Off 2>/dev/null",
      # Launch Safari to populate the defaults
      "/Applications/Safari.app/Contents/MacOS/Safari &",
      "SAFARI_PID=$!",
      "disown",
      "sleep 30",
      "kill -9 $SAFARI_PID",
      # Enable Safari's remote automation
      "sudo safaridriver --enable",
      # Disable screen lock
      #
      # Note that this only works if the user is logged-in,
      # i.e. not on the login screen.
      "sysadminctl -screenLock off -password ${var.ssh_password}",
    ]
  }

  provisioner "shell" {
    inline = [
      # Ensure that Gatekeeper is disabled. This asserts the boot_command's `spctl --global-disable`
      # pass actually landed, rather than trusting that the keystrokes hit the right widget.
      "spctl --status | grep -q 'assessments disabled'"
    ]
  }

  provisioner "shell" {
    inline = [
      # Install the Xcode command-line tools via softwareupdate, not `xcode-select --install` —
      # the latter pops a GUI prompt that never resolves headless (specs/macos-ci/12's seed failure
      # signature: "xcode-select: note: install requested"). This is what recovery_partition =
      # "keep" is for.
      "touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress",
      "softwareupdate --list | sed -n 's/.*Label: \\(Command Line Tools for Xcode-.*\\)/\\1/p' | xargs -I {} softwareupdate --install '{}'",
      "rm /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress",
    ]
  }
}
