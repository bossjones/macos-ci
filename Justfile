set shell := ["bash", "-uc"]

# List available recipes
default:
    @just --list

# lychee scrapes github.com HTML unauthenticated by default, which rate-limits
# into spurious 404s. Passing a token makes lychee use the GitHub API instead.

# Check all links in markdown files using lychee
link-check:
    @echo "🚀 Checking all links in markdown files using lychee"
    @GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null)}" lychee --config lychee.toml '**/*.md'

# Check all links in markdown files with verbose output
link-check-verbose:
    @echo "🚀 Checking all links in markdown files with verbose output"
    @GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null)}" lychee --config lychee.toml --verbose debug '**/*.md'

# Re-check links ignoring the 7d cache (use after fixing a link).
# lychee has no --no-cache; ageing every entry out to 0s is the supported bypass.
link-check-fresh:
    @echo "🚀 Checking all links, bypassing the lychee cache"
    @GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null)}" lychee --config lychee.toml --max-cache-age 0s '**/*.md'

# Re-execute the evidence behind every claim in .team/claims.jsonl.
# Exit 0 all verified · 2 a claim failed · 3 evidence unreachable · 4 usage.
verify-claims:
    @echo "🔬 Re-checking every spec claim against its evidence"
    @uv run tools/verify_claims.py

# Same, machine-readable — this is what an agent reads instead of scraping prose.
verify-claims-json:
    @uv run tools/verify_claims.py --json

# The token reaches the guest only as a provisioner env var, never a file (specs/macos-ci/13).
# It is an optimisation, not a dependency: without it the build still works, against GitHub's
# 60 req/hr unauthenticated cap instead of 5,000.

# Build the golden Tart image, injecting HOMEBREW_GITHUB_API_TOKEN if one is available.
# The template is deliberately UNAUTHORED: `packer build`/`packer init` are forbidden by the
# verification run's scope, so not one line of it could be validated. Fail loudly rather than
# let `packer build` emit its own error for a file we know is absent. Exit 4 = USAGE, matching
# tools/verify_claims.py. See specs/macos-ci/13-build-secrets.md and OQ-04.
build-golden:
    @test -f packer/tart-golden-image.pkr.hcl || { \
       echo "missing: packer/tart-golden-image.pkr.hcl" >&2; \
       echo "see specs/macos-ci/13-build-secrets.md and OQ-04" >&2; \
       exit 4; }
    @echo "📦 Building the golden image"
    @HOMEBREW_GITHUB_API_TOKEN="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}" \
      packer build packer/tart-golden-image.pkr.hcl

# `rm` inside a guest unlinks an inode; it does not zero the blocks, so a secret written to
# the guest survives in the disk image. This proves we never wrote one. Scans the whole VM
# directory rather than a named disk file: tart documents ~/.tart/vms/ but not the file
# inside it, and disk_format may be raw or asif.

# Leak canary: assert the Homebrew token appears nowhere in a built VM's artifact.
verify-no-secrets vm:
    @tok="${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}"; \
     if [ -z "$tok" ]; then echo "⚠️  no token in the environment — nothing to search for"; exit 0; fi; \
     if [ ! -d ~/.tart/vms/{{vm}} ]; then echo "no such VM: {{vm}}" >&2; exit 4; fi; \
     if LC_ALL=C grep -r -a -l -F "$tok" ~/.tart/vms/{{vm}}/ 2>/dev/null; then \
       echo "🚨 LEAK: the token is present in the artifact above"; exit 2; \
     else echo "✅ clean: token absent from ~/.tart/vms/{{vm}}/"; fi

# Count unverified markers. A spec's honesty budget: these must be justified, not ambient.
unverified-count:
    @echo "🕵️  <!-- UNVERIFIED --> markers by file:"
    @grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -v '`<!-- UNVERIFIED' || echo "  none"

# The full truth gate. Everything an agent must pass before a spec is trustworthy.
check: link-check verify-claims unverified-count
