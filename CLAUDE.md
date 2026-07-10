# macos-ci

Virtualized macOS images for testing things I don't want to run on my host yet — primarily a CI harness
for the `zsh-dotfiles` / `zsh-dotfiles-prep` install.

## Research: read before proposing anything about tart or UTM

| File | Why |
|---|---|
| [specs/macos-ci/00-overview.md](specs/macos-ci/00-overview.md) | Start here — the problem, the stack, the file map, the reading order |
| [specs/macos-ci/10-tart-vs-utm-adr.md](specs/macos-ci/10-tart-vs-utm-adr.md) | The decision: **tart is primary, UTM is the escape hatch**, and why |
| [specs/macos-ci/11-sources.md](specs/macos-ci/11-sources.md) | Every URL, graded `[meaty]`/`[thin]`/`[404]`, with what it gave us |
| [specs/macos-ci.md](specs/macos-ci.md) | The plan-format entry point; input to `/agent-harness:plan` |
| [specs/plans/macos-ci.html](specs/plans/macos-ci.html) | **Derived HTML rendering** of the plan, pinned at `f0b434a` — a snapshot, not a 15th spec. The markdown specs above are authoritative; on conflict, trust them. See [specs/plans/README.md](specs/plans/README.md) |

Settled facts that keep getting re-litigated — don't re-derive them:

- **No Terraform provider exists for tart or for UTM.** Tart's orchestration story is Orchard.
- **`packer-plugin-tart` is tart-only.** There is no UTM Packer builder.
- **UTM's disposable mode is QEMU-backend only**, so it never applies to a macOS guest.
- **UTM's AppleScript guest-exec and file-I/O require the QEMU guest agent**, which Apple-backend macOS
  guests do not have. UTM's macOS-guest automation surface is lifecycle plus host-side serial.
- **`utmctl` is a wrapper around that AppleScript interface, not a second automation surface.** UTM's own
  docs say so. `exec`/`file`/`ip-address` are the Guest Suite and need the QEMU guest agent;
  `start --disposable` and `usb` parse but are QEMU-backend-only. **A flag in `--help` proves it parses,
  not that it works.** `utmctl` cannot report a macOS guest's IP — there is no UTM-lane `tart ip`.
  See `05` §4.
- **Tart is Fair Source, not open source**, and is actively enforced. Free below 100 CPU cores.
- **Non-interactive chezmoi is already solved upstream** via `stdinIsATTY`. See `09` §"template contract".
- **Deleting a secret from the guest does not erase it.** `rm` unlinks an inode; it does not zero the
  blocks, so the plaintext survives in `~/.tart/vms/<name>/`'s disk image and `strings` still finds it.
  Never write a build secret to the guest filesystem — pass it through the shell provisioner's
  `environment_vars` (with `use_env_var_file = false`) and there is nothing to clean up. See `13`.
- **Packer's `sensitive = true` masks *values*, not variables.** It redacts every occurrence of the
  string, anywhere in the output, including under `PACKER_LOG=1`. So never mark a common word sensitive:
  `ssh_password = "admin"` marked sensitive would rewrite every `admin` in every log to `<sensitive>`.
- **The build needs no SSH key, `~/.gitconfig`, or `~/.ssh/config`**, and no
  `HOMEBREW_GITHUB_PACKAGES_TOKEN`. Every repo and tap involved is public; the one `git@github.com:` tap
  URL is rewritten to anonymous HTTPS via `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n`. See `13`.

## Build performance

The golden-image Packer build's wall-clock is dominated by the base OCI image pull, not the
provisioner: cloning `ghcr.io/cirruslabs/macos-sequoia-vanilla` pulls ~23.7GB compressed over the
network every time, and that alone can run to the majority of an hour-scale build (observed directly
during the 2026-07-10 macos-ci-build run, including several transient "network connection was lost"
layer retries that tart's own retry logic absorbed without failing the build).

**The image is immutable, so it only needs to be pulled once per host.** Pre-pulling/caching it —
`tart pull ghcr.io/cirruslabs/macos-sequoia-vanilla` (or a `just images-cache` recipe wrapping the same
call for every lane in `macos-versions.toml`) — lets every subsequent golden-image build clone from the
local cache in seconds instead of re-pulling, turning future builds into a minutes-scale provisioner run
rather than an hour-scale network pull. This is a deferred speed optimization, not a correctness change:
the golden-image smoke test and the `verify-no-secrets` canary (plant-then-fail-then-clean) still apply
in full regardless of whether the base image came from cache or a fresh pull. See
[specs/macos-ci/02-packer-tart-builder.md](specs/macos-ci/02-packer-tart-builder.md) for the builder
field reference this applies to.

## Verifying a claim against the upstream docs

**Don't guess a URL. Query the site's search index.** Both doc sites ship a static JSON index — the same
one their search box uses — so this needs no browser and no scraping.

```bash
# UTM docs (Just the Docs / Jekyll) — 281 entries, 78 pages
curl -fsSL https://docs.getutm.app/assets/js/search-data.json |
  python3 -c 'import json,sys; d=json.load(sys.stdin)
for v in d.values():
    if "trackpad" in (v["title"]+v["content"]).lower(): print(v["title"], "->", v["relUrl"])'
# -> macOS 13+ Trackpad -> /settings-apple/virtualization/#macos-13-trackpad

# Tart docs (MkDocs Material) — entries under .docs[]
curl -fsSL https://tart.run/search/search_index.json |
  python3 -c 'import json,sys; d=json.load(sys.stdin)
for e in d["docs"]:
    if "fair source" in (e["title"]+e["text"]).lower(): print(e["title"], "->", e["location"])'

# HashiCorp Packer docs — no static search JSON; the site's own sitemap is the page list
curl -fsSL https://developer.hashicorp.com/server-sitemap.xml |
  grep -o '<loc>https://developer.hashicorp.com/packer/docs[^<]*</loc>'
# -> 203 <loc> entries, e.g. .../packer/docs/commands/build, .../packer/docs/templates/hcl_templates
```

The index doubles as the **authoritative page list**: if a path is not in it, that page does not exist.
This is how `settings-apple/devices/` was proven to be a fabricated URL rather than a dead page, and how
`settings-apple/virtualization/` — omitted from the original research brief — was recovered. One query
for `trackpad` would have found it.
[developer.hashicorp.com's sitemap](https://developer.hashicorp.com/server-sitemap.xml) plays the same
role for HashiCorp's own Packer docs pages — see
[11-sources.md](specs/macos-ci/11-sources.md#verifying-packer-docs-urls) for the full writeup.

**Exception: `/packer/integrations/**` pages are not in that sitemap.** The Tart builder field
reference cited in [02](specs/macos-ci/02-packer-tart-builder.md) — `developer.hashicorp.com/packer/
integrations/cirruslabs/tart/latest/components/builder/tart` — is one of these: 0 of 337 `/packer/*`
sitemap entries match `/packer/integrations`. HashiCorp renders these pages from the plugin's own
GitHub repo instead of its own CMS —
[cirruslabs/packer-plugin-tart ships a `.web-docs/` directory](https://github.com/cirruslabs/packer-plugin-tart/tree/main/.web-docs)
that is the actual source. Verify one of these with a plain `curl -sS -o /dev/null -w '%{http_code}'`
against the URL, or by reading the plugin repo's `.web-docs/` directly — not by grepping the sitemap.

`docs.getutm.app` returns 403 to WebFetch; use `curl -fsSL`. For anything genuinely interactive, the
cmux browser surface is available, but the JSON index (or sitemap) answers almost every question
faster.

## Link hygiene

Specs cite sources inline. A wrong URL has already caused one false ground truth in this repo
(see the retraction in `11-sources.md`), so links are checked, not trusted:

```bash
just link-check          # lychee over every *.md
just link-check-fresh    # same, bypassing the 7-day cache
```

Write every URL as a markdown link, never a bare backticked path — lychee only sees real links. Internal
spec-to-spec links are checked too, **including `#anchor` fragments** (`scheme` includes `file`,
`include_fragments = "anchor-only"`); that combination caught two broken anchors that shipped in the
first PR.

## The claims ledger

Link hygiene proves a URL resolves. It does not prove the sentence citing it is true. `.team/claims.jsonl`
records every load-bearing assertion alongside evidence a machine can re-execute:

```bash
just check              # link-check + verify-claims + unverified-count. The truth gate.
just verify-claims      # re-run the evidence behind every claim
just verify-claims-json # same, for an agent to read instead of scraping prose
```

Evidence kinds: `file-contains`, `file-line` (catches hallucinated `file:line` citations), `absent`
(negative claims), `cli-help` (runs `argv` from the repo root, optionally under an `env` overlay),
`doc-index` (proves a doc page exists, via the search index above — this is what would have caught the
fabricated `settings-apple/devices/` URL), and `doc-contains` (proves a page *says* a given sentence).

**`cli-help` is unsound for backend questions, and `doc-contains` is the antidote.** `utmctl start
--help` advertises `--disposable` on a host that can only run Apple-backend macOS guests, while
[advanced/disposable](https://docs.getutm.app/advanced/disposable/) states "Disposable mode is only
supported on QEMU backend." A flag in `--help` proves the argument parser accepts it — nothing more. So
the ledger pairs each such `cli-help` claim with the `doc-contains` claim that settles the question, and
names the refutation in the `claim` prose. `doc-index` proves a page exists; `doc-contains` proves it
says it.

`must_fail` claims guard the doc oracles: one asserts the fabricated `settings-apple/devices/` URL
(`doc-index`), one asserts that the disposable page claims Apple-backend support (`doc-contains`). If
either ever starts passing, that oracle has broken and every claim of its kind is unreliable. A verifier
nobody verifies is just a second thing to trust.

`must_fail` does double duty: it is also the only way to write a **negative assertion** over a `cli-help`
probe, since `absent` takes a file. `packer-sensitive-hides-secret` asserts a secret does *not* appear in
`packer inspect` output. Such a claim is worthless alone — "no secret in the output" is equally satisfied
by *no output* — so **every negative probe must be paired with a positive control** running the same
command and asserting a non-sensitive literal *is* present. Both live next to each other in the ledger,
and the control names its partner. See `13`.

Two failure prefixes are never inverted by `must_fail`, because neither is evidence about the claim:
`UNREACHABLE:` (network down, binary missing) and `STRUCTURE:` (a `doc-contains` page is absent from the
index). The latter keeps "the page vanished" distinguishable from "the sentence vanished", and stops a
control from silently "passing" because its page 404'd.

Exit codes: `0` verified · `2` a claim failed · `3` evidence unreachable · `4` usage.

## Conventions

- Claims that cannot be verified from a source get an explicit `<!-- UNVERIFIED -->` marker on the line.
  Never present inference as fact. A claim you cannot express as a ledger entry is a claim that needs
  the marker.
- `just unverified-count` is an honesty budget. It should fall because claims got verified, never
  because markers got deleted.
- Prefer a shorter document that is entirely true over a longer one padded with plausible detail.
