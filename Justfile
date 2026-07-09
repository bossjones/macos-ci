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

# Count unverified markers. A spec's honesty budget: these must be justified, not ambient.
unverified-count:
    @echo "🕵️  <!-- UNVERIFIED --> markers by file:"
    @grep -rc 'UNVERIFIED' specs/ --include='*.md' | grep -v ':0$' || echo "  none"

# The full truth gate. Everything an agent must pass before a spec is trustworthy.
check: link-check verify-claims unverified-count
