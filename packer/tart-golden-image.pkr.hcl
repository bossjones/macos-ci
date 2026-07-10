# Golden-image build: clones the cirruslabs `-vanilla` Sequoia base (macos-versions.toml's
# `default` image) and provisions the tooling the dotfiles-install harness needs, once, so every
# test run can `tart clone` this image instead of repeating the Homebrew/Xcode CLT install.
#
# Field reference: specs/macos-ci/02-packer-tart-builder.md
# Secrets design:  specs/macos-ci/13-build-secrets.md

packer {
  required_plugins {
    tart = {
      version = ">= 1.11.1"
      source  = "github.com/cirruslabs/tart"
    }
  }
}

# The public, documented credential for every prebuilt tart image (specs/macos-ci/01-tart-core.md).
# Never mark this `sensitive` — Packer's masking is value-based, not variable-scoped, and would
# rewrite every occurrence of the word "admin" in every build log to `<sensitive>`
# (specs/macos-ci/13-build-secrets.md#sensitive-masks-values-not-variables).
variable "ssh_username" {
  type    = string
  default = "admin"
}

variable "ssh_password" {
  type    = string
  default = "admin"
}

# Optimization, not a dependency: without a token the build still works, against GitHub's
# 60 req/hr unauthenticated cap instead of 5,000 (specs/macos-ci/13-build-secrets.md).
# Reaches the guest only via the shell provisioner's process environment for the life of one
# command — never a file on disk (use_env_var_file stays false, below).
variable "homebrew_github_api_token" {
  type      = string
  sensitive = true
  default   = env("HOMEBREW_GITHUB_API_TOKEN")
}

source "tart-cli" "golden" {
  vm_base_name = "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest"
  vm_name      = "dotfiles-golden"
  cpu_count    = 4
  memory_gb    = 8
  disk_size_gb = 60
  headless     = true
  ssh_username = var.ssh_username
  ssh_password = var.ssh_password
  ssh_timeout  = "120s"

  # disk_format is inert on this lane (clone from vm_base_name, not from_ipsw/from_iso) — see
  # specs/macos-ci/13-build-secrets.md#disk_format-does-not-mean-what-this-spec-used-to-say-it-meant.
  # recovery_partition is set explicitly per specs/macos-ci/02's warning that the "" default is
  # only "currently equivalent to delete", not guaranteed to stay that way.
  recovery_partition = "delete"
}

build {
  sources = ["source.tart-cli.golden"]

  # ONE idempotent provisioner: Xcode CLT, Homebrew, chezmoi, and the smoke-test-docker.sh:142-143
  # brew prereq list. Deliberately does NOT install zsh-dotfiles-prep — that's a separate, optional
  # matrix leg, not part of the golden image.
  provisioner "shell" {
    # Must stay false — `true` would write the token to a tempfile and upload it into the guest,
    # then "clean up" with an `rm -f` that only unlinks, not shreds it
    # (specs/macos-ci/13-build-secrets.md#packers-own-cleanup-is-that-antipattern).
    use_env_var_file = false

    # compact() drops the empty string, so an unset token omits the variable entirely rather than
    # exporting HOMEBREW_GITHUB_API_TOKEN= and sending an empty Authorization header. The
    # GIT_CONFIG_* triplet rewrites the one git@github.com: tap URL
    # (zsh-dotfiles-prep/Brewfile:4) to anonymous HTTPS with nothing written to disk — harmless
    # here since this build doesn't touch that Brewfile, but wired now so the token path needs
    # authoring only once (specs/macos-ci/13-build-secrets.md#the-design).
    environment_vars = compact([
      var.homebrew_github_api_token != "" ? "HOMEBREW_GITHUB_API_TOKEN=${var.homebrew_github_api_token}" : "",
      "GIT_CONFIG_COUNT=1",
      "GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf",
      "GIT_CONFIG_VALUE_0=git@github.com:",
    ])

    inline = [
      "set -euo pipefail",

      "echo '==> Xcode Command Line Tools'",
      # Non-interactive install via softwareupdate — `xcode-select --install` pops a GUI prompt
      # that never resolves headless (specs/macos-ci/12's seed failure signature:
      # \"xcode-select: note: install requested\").
      "if ! xcode-select -p >/dev/null 2>&1; then",
      "  touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress",
      "  PROD=$(softwareupdate -l 2>/dev/null | grep '\\*.*Command Line Tools' | tail -n1 | sed 's/^[^C]*\\(Command Line Tools.*\\)/\\1/' | tr -d '\\n')",
      "  softwareupdate -i \"$PROD\" --verbose",
      "  rm -f /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress",
      "else",
      "  echo 'CLT already present, skipping'",
      "fi",

      "echo '==> Homebrew'",
      "if ! command -v brew >/dev/null 2>&1; then",
      "  NONINTERACTIVE=1 /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
      "fi",
      "eval \"$(/opt/homebrew/bin/brew shellenv)\"",

      "echo '==> brew prerequisites (smoke-test-docker.sh:142-143)'",
      "brew tap kadwanev/brew",
      "brew install wget curl kadwanev/brew/retry go openssl@3 readline libyaml gmp autoconf tmux",

      # >= 2.20.0 per zsh-dotfiles/.chezmoiversion; `brew install` tracks Homebrew's current
      # formula, which is well past that floor.
      "echo '==> chezmoi'",
      "brew install chezmoi",
      "chezmoi --version",
    ]
  }
}
