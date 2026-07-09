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

Settled facts that keep getting re-litigated — don't re-derive them:

- **No Terraform provider exists for tart or for UTM.** Tart's orchestration story is Orchard.
- **`packer-plugin-tart` is tart-only.** There is no UTM Packer builder.
- **UTM's disposable mode is QEMU-backend only**, so it never applies to a macOS guest.
- **UTM's AppleScript guest-exec and file-I/O require the QEMU guest agent**, which Apple-backend macOS
  guests do not have. UTM's macOS-guest automation surface is lifecycle-only.
- **Tart is Fair Source, not open source**, and is actively enforced. Free below 100 CPU cores.
- **Non-interactive chezmoi is already solved upstream** via `stdinIsATTY`. See `09` §"template contract".

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
```

The index doubles as the **authoritative page list**: if a path is not in it, that page does not exist.
This is how `settings-apple/devices/` was proven to be a fabricated URL rather than a dead page, and how
`settings-apple/virtualization/` — omitted from the original research brief — was recovered. One query
for `trackpad` would have found it.

`docs.getutm.app` returns 403 to WebFetch; use `curl -fsSL`. For anything genuinely interactive, the
cmux browser surface is available, but the JSON index answers almost every question faster.

## Link hygiene

Specs cite sources inline. A wrong URL has already caused one false ground truth in this repo
(see the retraction in `11-sources.md`), so links are checked, not trusted:

```bash
just link-check          # lychee over every *.md
just link-check-fresh    # same, bypassing the 7-day cache
```

Write every URL as a markdown link, never a bare backticked path — lychee only sees real links. Internal
spec-to-spec links are checked too, **including `#anchor` fragments** (`scheme` includes `file`,
`include_fragments = true`); that combination caught two broken anchors that shipped in the first PR.

## Conventions

- Claims that cannot be verified from a source get an explicit `<!-- UNVERIFIED -->` marker on the line.
  Never present inference as fact.
- Prefer a shorter document that is entirely true over a longer one padded with plausible detail.
