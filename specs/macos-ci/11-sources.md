# 11 — Sources

Every URL fetched (or attempted) across the research pass, grouped by bucket, each with a one-line
"what it gave us" and a grade:

| Grade | Meaning |
|---|---|
| `[meaty]` | Substantial, directly-cited content |
| `[thin]` | A stub, index, or TOC page — useful mainly as a pointer |
| `[cited-as-exclusion]` | Read only to establish what it does **not** support; never cited as evidence |

**Every source URL in this research is live**, and there is no `[404]` grade because nothing is dead —
see the retraction below for the URL that was wrongly believed to be. The live property is not asserted
here as a frozen count; it is **re-checked on every run** by `just link-check`, which walks every
markdown link in every spec (fragments included). Trust that, not a number in prose.

**Every URL below is a live markdown link on purpose.** `just link-check` runs
[lychee](https://github.com/lycheeverse/lychee) over this file; a bare-backtick URL would be invisible to
it, which is how the mistake in the retraction section below survived a full cross-check pass.

## Tart core

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/quick-start/](https://tart.run/quick-start/) | `[meaty]` | Install, full core CLI verb table, prebuilt ghcr.io image matrix + default creds, `--dir` shared-mount syntax, disk-resize recovery procedure — [01](01-tart-core.md) |
| [tart.run/faq/](https://tart.run/faq/) | `[meaty]` | NAT vs bridged networking, `~/.tart` layout + auto-pruning, macOS 15+ headless keychain requirement (G8), nested-virtualization M3/M4+Linux-only limit (G8) — [01](01-tart-core.md) |

## Packer + Tart builder

| URL | Grade | What it gave us |
|---|---|---|
| [github.com/cirruslabs/packer-plugin-tart](https://github.com/cirruslabs/packer-plugin-tart) | `[thin]` | Install snippet, macOS 15 host requirement, Sequoia local-network SSH workaround — explicitly defers config docs elsewhere — [02](02-packer-tart-builder.md) |
| [developer.hashicorp.com — tart builder](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart) | `[meaty]` | Canonical full field reference (source-VM, registry, resources, disk, display/boot, runtime, SSH, HTTP server, VNC) — [02](02-packer-tart-builder.md) |
| [github.com/markkenny/macos-virtualisation](https://github.com/markkenny/macos-virtualisation) | `[meaty]` | Real-world reference pipeline: `Packer.sh`/`Tarter.sh`, 15-20 min build time, IPSW sourcing, clone-and-run pattern, Ansible-during-build precedent, config toggles — [02](02-packer-tart-builder.md) |

### Verifying packer docs URLs

`developer.hashicorp.com` is a Next.js app, not MkDocs/Jekyll — it ships no static search-index JSON
like `tart.run` or `docs.getutm.app` do. Its client-side search is Algolia (index `product_PACKER`,
`searchOnlyApiKey` visible per-page in the embedded `__NEXT_DATA__` blob), but querying it needs the
Algolia `appId`, which is a build-time-inlined constant absent from every served HTML/JSON page —
extracting it would mean scraping a minified JS bundle, so this is rejected as a verification method.

The usable authoritative-page-list equivalent is its
[server-sitemap.xml](https://developer.hashicorp.com/server-sitemap.xml), advertised in `robots.txt`:

```bash
curl -fsSL https://developer.hashicorp.com/server-sitemap.xml |
  grep -o '<loc>https://developer.hashicorp.com/packer/docs[^<]*</loc>'
```

This returns **203 pages** under `/packer/docs`, out of **337** total `/packer/*` URLs.

**Anchor the path, or you will count a different product.** Two greps over the same sitemap return two
different totals, and only one of them answers the question "how many `/packer/*` pages are there?":

```bash
# (A) path-anchored — 337. These really are /packer/* pages.
grep -o '<loc>https://developer.hashicorp.com/packer[^<]*</loc>'

# (B) bare substring — 365. Over-counts by 28.
grep -o '<loc>[^<]*packer[^<]*</loc>'
```

The 28 extras in (B) are not `/packer/*` at all. They are `/hcp/docs/packer`,
`/hcp/docs/packer/manage/ancestry`, `/hcp/docs/packer/store/sbom` … — **HCP Packer, a different product
namespace** that merely contains the substring `packer`. Under both greps, `/packer/docs` is 203; if you
ever find yourself writing "203 out of 365", the question to ask is *203 out of **what***, and the answer
will send you back to (A).

**The sitemap does not cover `/packer/integrations/**`** — including the tart-builder page cited above as
the canonical field reference. **Zero** entries match `/packer/integrations`: under (A) and under (B), at
337 and at 365 alike. **That structural fact never depended on the total**, which is why it — and not any
count — is what the ledger pins (`g19-packer-integrations-absent-from-hashicorp-sitemap`, a `must_fail`
probe, paired with `CONTROL-hashicorp-sitemap-lists-packer-docs` so it cannot pass against an empty fetch;
and `synth-sitemap-substring-packer-also-matches-hcp-packer`, which pins the existence of the HCP namespace
that makes (B) over-count). Root cause, confirmed against the plugin's own GitHub repo:
[cirruslabs/packer-plugin-tart's `.web-docs/`](https://github.com/cirruslabs/packer-plugin-tart/tree/main/.web-docs)
directory (`components/`, `metadata.hcl`, `README.md`) — HashiCorp renders third-party
plugin/integration pages directly from that directory, per release tag, rather than from its own
CMS/sitemap. The plugin repo is the actual source of truth for that page, not
`developer.hashicorp.com` itself. Verify an integrations page with a plain
`curl -sS -o /dev/null -w '%{http_code}'` against the URL, or by reading the plugin repo's
`.web-docs/` directly — grepping the sitemap won't find it.

### The G19 class: absence from an index refutes only *inside* that index's domain

An index is authoritative **for the prefixes it covers.** Inside that domain, absence is proof of
fabrication — that is how the invented `settings-apple/devices/` URL was caught. **Outside it, absence is
evidence of nothing. Go fetch the URL.**

Refuting a live page by grepping an index that never claimed to list it is **G10 running backwards**:
declaring a *real* page fake, with total confidence, on the strength of a lookup that was never in scope.
Two URLs in this repo sit outside their index's domain. Both are load-bearing. Both return `200`:

| URL | Underpins | Index says | Reality |
|---|---|---|---|
| [developer.hashicorp.com — tart builder field reference](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart) | **all of [02](02-packer-tart-builder.md)** | absent from every `/packer/*` sitemap entry | **200** — rendered from the plugin repo's `.web-docs/`, not HashiCorp's CMS |
| [tart.run — Fair Source enforcement press release (2025-10-27)](https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/) | the **sole** source for G4's *"enforcement is not theoretical"* ([04](04-tart-licensing-risk.md)) | absent from tart's search index, which carries `/blog/` and `/blog/archive/YYYY/` but **zero** `/blog/YYYY/MM/DD/` posts | **200** |

The second is a **second G19, found this run** — the first was known, this one was not, and it guards the
single citation behind the licensing risk a human signed off on.

Both are now ledger claims rather than prose behind a carve-out a future agent must remember to obey
(`http-status` / `http-contains`, added for **OQ-26**). Note carefully **how** the absence is recorded:
`synth-enforcement-press-release-absent-from-tart-index` is a **`must_fail` `doc-index`** claim. A
*positive* `doc-index` claim on that URL would **fail, and read as a fabrication** — the tool would report
exactly what it reports for an invented page. Writing the absence as an inverted control says the true
thing ("the index does not list it") without ever implying the false one ("the page does not exist"). Its
positive control asserts the index *does* carry `/blog/`, so the absence is a fact about the post rather
than about an oracle that never indexed blogs at all.

**And a `200` proves a page exists, not that it says anything.** `http-status` is the weakest evidence in
the ledger. Where a page is plain text, prefer `http-contains` and quote the sentence.

Other avenues checked and rejected: `llms.txt` / `llms-full.txt` (404), a `.md` content-negotiation
suffix on doc pages (404), and a few guessed content/registry API paths (all 404).

## Tart CI integration and Orchard

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/integrations/cirrus-cli/](https://tart.run/integrations/cirrus-cli/) | `[meaty]` | `.cirrus.yml` macOS-task syntax, local/cloud parity, artifact extraction (`--artifacts-dir`) — [03](03-tart-ci-and-orchard.md). **Does not contain the "we recommend Cirrus CLI" sentence, nor `sshpass`** — those are on [tart.run/quick-start/](https://tart.run/quick-start/), and conflating the two is guarded by a `must_fail` control claim |
| [tart.run/quick-start/#ssh-access](https://tart.run/quick-start/#ssh-access) | `[meaty]` | The upstream recommendation to use Cirrus CLI for running scripts / retrieving artifacts in a Tart VM, **and** the `sshpass -p admin ssh …` + `tart ip` fallback it names (incl. `brew install cirruslabs/cli/sshpass` and the `< script.sh` stdin form) — [03](03-tart-ci-and-orchard.md) |
| [github.com/cirruslabs/cirrus-cli](https://github.com/cirruslabs/cirrus-cli) | `[thin]` | The tool's own repo. Install and `.cirrus.yml` reference; the Tart-specific framing lives on the two `tart.run` pages above — [03](03-tart-ci-and-orchard.md) |
| [tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/) | `[meaty]` | Controller/worker architecture, `orchard dev`, core VM commands, SSH/VNC proxy, worker license tiers by env var — [03](03-tart-ci-and-orchard.md), [04](04-tart-licensing-risk.md) |

## Tart / Orchard licensing (G4)

| URL | Grade | What it gave us |
|---|---|---|
| [tart.run/licensing/](https://tart.run/licensing/) | `[meaty]` | Current tier table (Free/Gold/Platinum/Diamond), the "all cores always counted" clarification — [04](04-tart-licensing-risk.md) |
| [tart.run/blog/](https://tart.run/blog/) | `[thin]` | Blog index; the two posts below are what mattered |
| [Changing Tart's license (2023-02-11)](https://tart.run/blog/2023/02/11/changing-tart-license/) | `[meaty]` | Fair Source 100 transition, personal-use exemption, "server installation" definition (no connected display) — [04](04-tart-licensing-risk.md) |
| [Cirrus Labs enforces its Fair Source license (2025-10-27)](https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/) | `[meaty]` | Proof enforcement is not theoretical — competing-product violation, paid settlement, named counsel — [04](04-tart-licensing-risk.md) |

## UTM automation and the IaC gap

| URL | Grade | What it gave us |
|---|---|---|
| [docs.getutm.app/](https://docs.getutm.app/) | `[thin]` | Docs home; nav is the authoritative page index (and revealed pages the brief omitted) |
| [mac.getutm.app/](https://mac.getutm.app/) | `[thin]` | Product landing page — download, feature bullets. No automation content |
| [docs.getutm.app/installation/macos/](https://docs.getutm.app/installation/macos/) | `[thin]` | How a human installs UTM.app. No CLI/unattended install path |
| [scripting/reference/](https://docs.getutm.app/scripting/reference/) | `[meaty]` | Full AppleScript dictionary: UTM/Guest/Configuration/USB/Registry/Input suites, **the QEMU-guest-agent gate on the Guest Suite**, `apple configuration` field reference — [05](05-utm-automation.md), [06](06-utm-macos-guest.md) |
| [scripting/cheat-sheet/](https://docs.getutm.app/scripting/cheat-sheet/) | `[meaty]` | Worked AppleScript snippets for every suite, annotated for backend applicability — [05](05-utm-automation.md) |
| [advanced/remote-control/](https://docs.getutm.app/advanced/remote-control/) | `[meaty]` | `utm://` URL-scheme command table, Shortcuts/Automator recipes, improper-shutdown warnings — [05](05-utm-automation.md) |
| [advanced/headless/](https://docs.getutm.app/advanced/headless/) | `[meaty]` | Headless setup (delete display / serial-terminal device), dock-icon hiding — [05](05-utm-automation.md) |
| [preferences/macos/](https://docs.getutm.app/preferences/macos/) | `[thin]` | App-wide prefs incl. dock-icon toggle and UTM server remote-access settings — [05](05-utm-automation.md), [07](07-utm-settings-appendix.md) |
| [basics/actions/](https://docs.getutm.app/basics/actions/) | `[thin]` | GUI VM actions (start/pause/stop/clone/share). The AppleScript equivalents in `scripting/reference` supersede this for automation |
| [basics/controls/](https://docs.getutm.app/basics/controls/) | `[thin]` | GUI toolbar/input controls. No automation surface |
| [advanced/version/](https://docs.getutm.app/advanced/version/) | `[thin]` | How to read the UTM build version. No bearing on the harness |
| [utmapp/UTM discussion #3618](https://github.com/utmapp/UTM/discussions/3618) | `[meaty]` | The "Machines-as-code" IaC feature request and the maintainer's "a long way off" reply — direct source for **G1** — [05](05-utm-automation.md) |
| [utmapp/UTM issue #3718](https://github.com/utmapp/UTM/issues/3718) | `[thin]` | The tracked, still-open IaC-support issue referenced by the discussion above — [05](05-utm-automation.md) |

## UTM macOS guest support

| URL | Grade | What it gave us |
|---|---|---|
| [guest-support/macos/](https://docs.getutm.app/guest-support/macos/) | `[meaty]` | macOS 12+/Apple-Silicon-host requirement, IPSW sourcing, the master missing-features list, VirtioFS + network-sharing mount instructions, clipboard sharing steps — [06](06-utm-macos-guest.md) |
| [settings-apple/virtualization/](https://docs.getutm.app/settings-apple/virtualization/) | `[meaty]` | **The page the brief omitted.** Balloon, entropy, sound/keyboard/pointer (macOS 12+), trackpad (13+), Rosetta (13+), clipboard sharing — each with its guest-version gate — [06](06-utm-macos-guest.md) §9 |
| [advanced/disposable/](https://docs.getutm.app/advanced/disposable/) | `[thin]` | Single-sentence confirmation: disposable mode is QEMU-backend only — direct source for **G5** — [06](06-utm-macos-guest.md) |
| [advanced/multiple-displays/](https://docs.getutm.app/advanced/multiple-displays/) | `[thin]` | Single-sentence confirmation: no multi-display on Apple backend — direct source for **G6** — [06](06-utm-macos-guest.md) |
| [advanced/recovery/](https://docs.getutm.app/advanced/recovery/) | `[thin]` | 1TR recovery-mode boot, macOS 13+/Apple-backend-only, SIP-disable use case — [06](06-utm-macos-guest.md) |
| [advanced/serial/](https://docs.getutm.app/advanced/serial/) | `[thin]` | PTTY-vs-network-socket serial backends, `screen /dev/ttysNNN` connection pattern — [06](06-utm-macos-guest.md) |
| [advanced/rosetta/](https://docs.getutm.app/advanced/rosetta/) | `[thin]` | Confirms Rosetta (x86_64-on-ARM) applies to **Linux** guests only — direct source for **G7** |
| [guest-support/dynamic-resolution/](https://docs.getutm.app/guest-support/dynamic-resolution/) | `[thin]` | macOS 14+ Apple-backend auto-resolution vs QEMU's manual `xrandr` workaround — [06](06-utm-macos-guest.md) |
| [guides/guides/](https://docs.getutm.app/guides/guides/) | `[thin]` | Index of per-guest walkthroughs. All non-macOS except `classic-macos` |
| [guides/classic-macos/](https://docs.getutm.app/guides/classic-macos/) | `[thin]` | Confirmed out-of-scope: classic 68k/PPC Mac OS emulation, unrelated to macOS 12+ Apple-backend — [06](06-utm-macos-guest.md) |

## UTM settings pages (thin appendix)

| URL | Grade | What it gave us |
|---|---|---|
| [settings-apple/settings-apple/](https://docs.getutm.app/settings-apple/settings-apple/) | `[meaty]` | The Settings (Apple) index. Source of a load-bearing ADR claim: *"Apple Virtualization backend supports only virtualization and is less mature than QEMU. It is the only way to run macOS virtualized on Apple Silicon."* TOC = Boot, Devices, Drive, Information, Sharing, System, Virtualization |
| [settings-qemu/settings-qemu/](https://docs.getutm.app/settings-qemu/settings-qemu/) | `[thin]` | The Settings (QEMU) index; contrast-only |
| [settings-apple/boot/](https://docs.getutm.app/settings-apple/boot/) | `[thin]` | OS selection, IPSW field — [07](07-utm-settings-appendix.md) |
| [settings-apple/drive/](https://docs.getutm.app/settings-apple/drive/) | `[thin]` | Drive fields incl. macOS 26+ ASIF format — [07](07-utm-settings-appendix.md) |
| [settings-apple/system/](https://docs.getutm.app/settings-apple/system/) | `[thin]` | CPU/memory fields — [07](07-utm-settings-appendix.md) |
| [settings-apple/information/](https://docs.getutm.app/settings-apple/information/) | `[thin]` | Cosmetic name/notes/icon — [07](07-utm-settings-appendix.md) |
| [settings-apple/sharing/](https://docs.getutm.app/settings-apple/sharing/) | `[thin]` | Shared-directory list — [07](07-utm-settings-appendix.md) |
| [settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/) | `[thin]` | Index only: add/remove a device. TOC = Display, Network, Serial — [07](07-utm-settings-appendix.md) |
| [settings-qemu/system/](https://docs.getutm.app/settings-qemu/system/) | `[thin]` | Contrast-only: QEMU arch/CPU/memory fields — [07](07-utm-settings-appendix.md) |
| [settings-qemu/qemu/](https://docs.getutm.app/settings-qemu/qemu/) | `[thin]` | Contrast-only: logging/UEFI/RNG/balloon/TPM/TSO toggles — [07](07-utm-settings-appendix.md) |
| [settings-qemu/sharing/](https://docs.getutm.app/settings-qemu/sharing/) | `[thin]` | Contrast-only: SPICE WebDAV/VirtFS sharing — [07](07-utm-settings-appendix.md) |
| [settings-qemu/input/](https://docs.getutm.app/settings-qemu/input/) | `[thin]` | Contrast-only: USB bus version/limits, N/A to Apple backend — [07](07-utm-settings-appendix.md) |
| [settings-qemu/information/](https://docs.getutm.app/settings-qemu/information/) | `[thin]` | Byte-identical to the Apple-backend information page — [07](07-utm-settings-appendix.md) |
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | `[thin]` | Index only: add/remove a device. TOC = Display, Network, Serial, Sound |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | `[meaty]` | Contrast-only: QEMU drive creation, importing, deletion, boot order, removable, interface, image type, raw images |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | `[thin]` | Index over Clipboard / Directory / USB sharing; the children carry the content (SPICE WebDAV, VirtFS backends) |

## Build-time secrets

Consumed by [13](13-build-secrets.md). Everything in this bucket about Packer's own behaviour was also
**executed** against `packer` v1.15.4 and pinned in `.team/claims.jsonl`; the docs are cited for the
contract, the ledger for the fact.

| URL | Grade | What it gave us |
|---|---|---|
| [packer/docs/templates/hcl_templates/variables](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/variables) | `[meaty]` | `sensitive` ("obfuscated from Packer's output"), `PKR_VAR_<name>` as a lowest-priority assignment, and the full precedence table — [13](13-build-secrets.md) |
| [packer/docs/.../functions/contextual/env](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/functions/contextual/env) | `[meaty]` | `env()` is "the only function callable from a variable block", and only in `default`. Direct source for choosing the unprefixed name over `PKR_VAR_` — [13](13-build-secrets.md) |
| [packer/docs/.../functions/collection/compact](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/functions/collection/compact) | `[thin]` | "returns a new list with any empty string elements removed" — the mechanism that makes the token optional — [13](13-build-secrets.md) |
| [packer/docs/provisioners/shell](https://developer.hashicorp.com/packer/docs/provisioners/shell) | `[meaty]` | `environment_vars`; that `use_env_var_file = true` "writes your environment variables to a tempfile" **on the guest** — the behaviour [13](13-build-secrets.md) exists to avoid; and that `skip_clean` "defaults to false (clean scripts from the system)". **The page never states a default for `use_env_var_file`** — it states one for `skip_clean` and for `expect_disconnect`, so its silence here is not a house style. `false` is a strong inference from the documented `execute_command` branch, not a documented fact; [13](13-build-secrets.md) therefore sets the field explicitly rather than relying on it. See **OQ-24** |
| [packer/docs/.../legacy_json_templates/user-variables](https://developer.hashicorp.com/packer/docs/templates/legacy_json_templates/user-variables) | `[cited-as-exclusion]` | The JSON-era `"sensitive-variables"` list. Read only to confirm it is the *legacy* spelling, superseded by HCL's `sensitive = true`; not the API we use |
| [Homebrew/brew `docs/Manpage.md`](https://github.com/Homebrew/brew/blob/master/docs/Manpage.md) | `[meaty]` | `HOMEBREW_GITHUB_API_TOKEN` ("Homebrew doesn't require permissions for any of the scopes" — hence the scopeless-PAT advice), `HOMEBREW_GITHUB_PACKAGES_TOKEN` (GitHub Packages registry, i.e. private-tap bottles — which is why we don't need it), and `HOMEBREW_API_DOMAIN` (default `https://formulae.brew.sh/api`) — [13](13-build-secrets.md) |
| [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) | `[meaty]` | 60 requests/hour unauthenticated vs 5,000/hour authenticated — the entire justification for injecting a token — [13](13-build-secrets.md) |
| [git-config(1)](https://git-scm.com/docs/git-config) | `[meaty]` | `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_<n>` / `GIT_CONFIG_VALUE_<n>`: git configured wholly from the environment. This is why no `~/.gitconfig` or `~/.ssh/config` is copied into the guest — [13](13-build-secrets.md) |
| [tart.run/faq/#vm-location-on-disk](https://tart.run/faq/#vm-location-on-disk) | `[thin]` | "Local images that you can run are stored in `~/.tart/vms/`" — the directory `just verify-no-secrets` scans. Notably it does *not* name the disk file, which is why the canary globs the directory — [13](13-build-secrets.md) |
| [ivobeerens.nl — pass a GitHub variable to a Packer provisioner](https://www.ivobeerens.nl/blog/2024/06/pass-github-variable-to-packer-powershell-provisioner/) | `[thin]` | Prior art for the shape (sensitive var → provisioner env). PowerShell/Windows-flavoured, so the mechanism transfers but none of the commands do — [13](13-build-secrets.md) |

## Retraction — the G10 prune list was wrong

The research brief carried a ground truth **G10** instructing every agent that four URLs were 404 and
must not be fetched or cited. **Not one of them was a dead page.** Verified with
`curl -sS -o /dev/null -w '%{http_code}' -L`:

| URL | G10 claimed | Actual |
|---|---|---|
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | 404 | **200** |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | 404 | **200** |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | 404 | **200** |
| `docs.getutm.app/settings-apple/devices/` | 404 | 404 — **but this path never existed.** Not a link, hence not linked here |

That fourth entry is the interesting one. It does return 404, but it is not a page that died — it is a
**malformed path that was never in the source list**. The Settings (Apple) section is served at
[settings-apple/settings-apple/](https://docs.getutm.app/settings-apple/settings-apple/), and its Devices
child at [settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/). The
`404` was manufactured by requesting a URL nobody had ever published, and its "deadness" was then
generalized onto three live URLs sitting next to it in the list.

Not one URL actually supplied for this research is dead. The original write-up put a number on that
("47/47") — but the supplied list is not on disk, so the count can be neither reproduced nor disproved
from this repo, and it has since drifted — this file alone now cites well more than 47 (re-derive with
`grep -ohE '\]\(https?://[^)]+\)' specs/macos-ci/11-sources.md | sort -u | wc -l`). A frozen count is
exactly the kind of unfalsifiable number this section exists to warn about, so it has been replaced by
the live check: `just link-check`. See **OQ-25**.

**The two ways a number in a spec goes wrong, and they are mirror images.** Both were committed in this
file, one round apart:

> A number that was true when written and is never re-derived is indistinguishable from one that was
> never true.
>
> **And its converse:** a number re-derived by a *different query* is indistinguishable from one that was
> never checked.

`47/47` was the first. The second was `337`: it was **correct**, and this file briefly "retracted" it in
favour of `365` — a total produced by a looser grep that silently swept in HCP Packer, a different
product. The number had not drifted; **the query had.** The instinct to re-derive was right; the predicate
was wrong. See the [`/packer/*` sitemap counts](#verifying-packer-docs-urls) above, where both greps are
now written out precisely because either one alone looks authoritative.

**Re-derivation must re-derive the same question.** A re-run with a subtly different predicate is not a
re-derivation — it is a new claim wearing the old one's citation, and it will retract true sentences with
the same confidence it would have refuted false ones.

Two things made the error durable:

1. **The instruction was self-sealing.** "Do not fetch, do not cite" guaranteed no agent could ever
   surface evidence against it. The lead's cross-check ledger marked G10 `verified` — but verifying a
   *don't-look* rule only confirms nobody looked.
2. **The brief's URL list omitted
   [settings-apple/virtualization/](https://docs.getutm.app/settings-apple/virtualization/)**, the page
   that actually documents the Apple-backend balloon/entropy/sound/keyboard/pointer/trackpad/Rosetta/
   clipboard toggles. `06` was ordered to produce that content, could not find it, and correctly recorded
   the gap — blaming the wrong cause.

The mis-pruned pages turned out to be mostly thin index/TOC pages, so little substance was lost. The real
loss was `settings-apple/virtualization/`, now written up in [06](06-utm-macos-guest.md) §9. **G10 is
retracted**; the ledger row in `.team/macos-ci.board.md` is marked accordingly. `just link-check` now
guards against a repeat.

## Further retractions — G10 was not the only one

G10 is the famous one because it fabricated a URL. It is not the only ground truth the research brief got
wrong, and the rest are recorded here so no reader has to rediscover them. **In every case the brief lost
to a read-only command anyone could have run.**

### D5 — the marker baseline, wrong twice over

The brief asserted that `Justfile`'s marker count matched on the bare token with no `<!--` prefix, and
that tightening the pattern to `<!-- UNVERIFIED` would drop 5 prose lines, leaving 17. Both halves are
false. Counted both ways, the two patterns return the same **22** lines: every one of them already
carries the literal `<!-- UNVERIFIED`, so the set difference is empty and the proposed "fix" is a no-op.

The real discriminator is the **backtick**. A prose *mention* of the marker wraps it in a code span; an
actual marker does not. Excluding lines that match the backticked form leaves **16** real markers — which
is how `Justfile:63` counts today, and why this very paragraph does not inflate the budget it describes.

And the brief's enumeration of the prose lines was short by one: it named five, there are six (it missed
`specs/macos-ci.md:517`). Had that arithmetic been adopted, **17** would have become the baseline every
later diff was measured against. The honest baseline is **16**. `Justfile:63` now discriminates on the
backtick (ledger: `d5-justfile-63-discriminates-on-the-backtick`), which is sound today but fragile: a
line carrying a real marker *and* a backticked mention would be silently dropped. See **OQ-05**. *A
budget you can pay down by editing punctuation is not a budget.*

### G13 — partially retracted: `vnc_port_min` / `vnc_port_max` do not exist

The brief described VNC port-range fields on the Tart Packer builder. They are not in the builder's
published field reference, and not in its generated config schema. Checked against the local clone at
`c10d611`, not against memory (ledger: `g13-packer-tart-webdocs-has-no-vnc-port-fields`,
`g13-packer-tart-hcl2spec-has-no-vnc-port-fields` — each paired with a positive control asserting the
field `disable_vnc`, which the same files **do** document, so "no `vnc_port`" cannot pass against a
gutted file). What survives of G13 is only the part about VNC itself being present. The rest of the
`--vnc-experimental` question stays marked `<!-- UNVERIFIED -->` in
[12](12-tooling-and-agent-loop.md) — see **OQ-02**.

### G9 — the conclusion survives; the method that was prescribed would have failed

G9 says neither dotfiles repo uses Ansible. The brief instructed proving it with an `absent` claim over
the repos. That claim would **fail**: `ansible` appears twice in `zsh-dotfiles-prep`'s Brewfile — as
`brew "ansible"` and as the VS Code extension `redhat.ansible` (ledger:
`ansible-in-prep-brewfile-line-57`, `ansible-in-prep-brewfile-line-602`).

Installing a tool is not being provisioned by it. The defensible claim — the one the ledger actually
carries — is narrower: **neither repo is *provisioned by* Ansible.** There is no playbook
(`prep-repo-has-no-ansible-playbook`), no `become:` key (`prep-repo-has-no-become-key`), and no
`ansible` in `zsh-dotfiles`' tracked tree at all (`no-ansible-in-zsh-dotfiles-tracked`, plus an
uppercase variant, because `grep` is case-sensitive and a negative that misses a case is a negative that
lies). Each of those negatives ships a positive control on the same command shape.

### G14 — the brief asserted a host fact that a one-word command refuted

The research brief told every agent that `packer` was **not installed**, and pointed them at a
`just doctor` recipe to remedy it. Both halves are false, and each dies to a single command:

```bash
packer version          # -> Packer v1.15.4
just --summary          # -> build-golden check default link-check link-check-fresh
                        #    link-check-verbose unverified-count verify-claims
                        #    verify-claims-json verify-no-secrets
```

There is no `doctor` recipe (ledger: `synth-justfile-has-no-doctor-recipe`, paired with a positive
control on the same file so it cannot pass against a gutted `Justfile`), and packer is present at
**v1.15.4** (`synth-packer-version-is-1-15-4`). The sharp detail is the timing: **the ledger claim
`packer-is-installed` was already passing when the draft asserting the opposite was written.** The
evidence was sitting in the repo, green, and the prose contradicted it anyway.

That is this repo's thesis stated as a fact rather than a slogan: **the briefing is not privileged over
the evidence.** A ground truth is a hypothesis with good PR. When one contradicts a passing claim or a
read-only command, the ground truth is what gives way.

### The master brief itself — `must_fail` JOB 2, retracted in three rounds

The brief's rule (`must_fail` JOB 2) required a positive control for one shape only: a **negative
`cli-help` probe**. Each round of fixing it revealed the same hole one level further up. The progression
is the lesson, so it is recorded as one retraction rather than three:

| | The hole | Where it was |
|---|---|---|
| **GB2** | The rule is a **logical impossibility** for a `grep -c`-shaped probe. A true negative implies **empty output**, so no same-`argv` command can ever print anything to control against. | in the rule's wording |
| **GB4** | The identical hazard existed for the `absent` kind, entirely unguarded. An `absent` claim passes against an **empty or gutted file** as readily as an honest one. Worse: a `must_fail` control whose **target file was deleted** went **green**, because the missing-file handler returned a bare `missing:` with no `UNREACHABLE:` prefix — so `must_fail` dutifully inverted it. **Deleting a control's target file turned the control green.** | in the kinds the rule forgot |
| **GB5** | The GB4 fix then exempted the `doc-contains` **kind** rather than the **oracle records**, leaving exactly one `must_fail` `doc-contains` negative probe (`utm-no-tso-toggle-on-apple-virtualization`) guarded by prose alone. | in the fix's exemption clause |

**The pattern: each round, the hole moved one level up the abstraction.** From the rule, to the kinds the
rule omitted, to the exemption clause of the rule's own fix. **Every exemption clause is a place where
enforcement stops and prose resumes** — and prose is what G10 was made of.

So the invariant is not *"negatives need controls."* It is:

> **Every claim satisfiable by the absence of evidence must name the positive claim that proves the probe
> can see.**

It now lives in [`tools/verify_claims.py`](../../tools/verify_claims.py) (`needs_control` →
`check_structure` → exit `4`), not in a brief. Re-derived at HEAD rather than taken on trust:

```
absent claim, no `control` field                     -> exit 4   STRUCTURAL REJECTION
must_fail doc-contains, no `control` field           -> exit 4   (the GB5 hole, now closed)
must_fail file-line whose target file is DELETED     -> exit 3   UNREACHABLE, never inverted (the GB4 hole, now closed)
```

Two residual limits, stated because a fix nobody bounds becomes the next brief. First, the tool checks
that a control **exists**, not that it probes the **same substrate** — an `absent` claim over an empty
file is still accepted if its control names an unrelated target (see **OQ-36**). Second, the tool's own
behaviour is the one thing in this repo no claim executes (see **OQ-35**).

### OQ-20 — the counterparty is OpenAI, and **half** the guess was wrong

Tart's copyright holder is no longer Cirrus Labs. [cirruslabs.org](https://cirruslabs.org/) publishes
*"Cirrus Labs to join OpenAI"*, dated **April 7th, 2026**, by founder Fedor Korotkov;
`api.github.com/repos/cirruslabs/tart` reports `"full_name": "openai/tart"`; and
[openai/tart's LICENSE](https://raw.githubusercontent.com/openai/tart/main/LICENSE) reads *"Functional
Source License, Version 1.1, ALv2 Future License"*, *"Copyright 2022-2026 OpenAI"*.

**OQ-20 guessed: "Cirrus Labs retains the licensing business, and `licensing@cirruslabs.org` remains the
correct contact." Recording which half was wrong is the whole point.**

| Half of the guess | Verdict |
|---|---|
| The acquisition happened | ✅ **confirmed** (`synth-cirruslabs-announces-openai-acquisition`, `synth-cirruslabs-announcement-dated-april-2026`) |
| `licensing@cirruslabs.org` is still the right escalation contact | 🟡 **doubtful — do not assert** |

Because [tart.run/licensing](https://tart.run/licensing/) mentions **OpenAI zero times**. Three months
after the announcement it still says Fair Source, still grants the 100-core Free Tier, and still lists
`licensing@cirruslabs.org` (`synth-tart-licensing-page-never-mentions-openai`, a `must_fail` probe whose
positive control asserts the contact address *is* on the page — so "no OpenAI" cannot pass against an
empty index entry). **The tier-grant page is stale relative to the acquisition.** Who would now enforce,
and where escalation goes, is therefore marked `<!-- UNVERIFIED -->` in
[04](04-tart-licensing-risk.md), citing OQ-20. A guess here would be a guess about a counterparty's legal
posture, which is the worst possible place to be charitable.

G4's tier numbers were **re-verified and are unchanged**, and G4 is signed off as an accepted, documented
risk.

**One distinction worth keeping straight, because conflating it would invent a licence clause.** The
100-core Free Tier is a **grant published on `tart.run`**, not a term of the FSL text — the licence
mentions cores **zero** times (`synth-fsl-text-never-mentions-cores`, controlled by
`synth-openai-tart-license-is-fsl-1-1` on the same URL, so "no cores" cannot pass against a failed fetch).
Both sources are true at once: the licence grants rights, the website grants a ceiling. Reading a core
limit *into the licence* would be citing something that does not exist.

### OQ-32 — this run contaminated the reference clones, with its own fixture secret

The `vnc_port` refutation in [02](02-packer-tart-builder.md) nearly died to a false positive: the string
appeared inside `logs/` directories in two third-party checkouts. Those directories were written **by this
run's own `pre_tool_use` hook**, which wrote `ghp_FIXTURE_SENTINEL` — the fixture secret from
[13](13-build-secrets.md)'s own `packer inspect` masking tests — into working trees this repo does not own.

**The irony is the finding.** The run whose central thesis is *never write a secret to a filesystem you do
not control* (G15/G17, [13](13-build-secrets.md)) did exactly that, to someone else's git checkout, while
proving it.

Provenance was established **before** anything was touched, which is the only reason the cleanup was safe:

| Path | Created | This run? | Action |
|---|---|---|---|
| `cirruslabs/packer-plugin-tart/logs/` | Jul 9, 21:46–21:48 | **yes** | **moved** to scratchpad |
| `cirruslabs/macos-image-templates/logs/` | Jul 9, 22:23 | **yes** | **moved** to scratchpad |
| `zsh-dotfiles/logs/`, `zsh-dotfiles-prep/logs/` | predate the run | no | **left alone, deliberately** |

Moved, not deleted — nothing was destroyed, and a directory that predates the run is somebody else's data,
not our mess. Post-scrub, re-verified read-only: **zero** files under `/Users/bossjones/dev/cirruslabs`
contain the sentinel (`synth-packer-plugin-clone-free-of-fixture-sentinel`, whose control runs the same
`grep` shape over the same substrate with a pattern that *does* match — a `grep -rIl` negative emits zero
bytes, so no same-`argv` control is possible; this is the GB2 shape), and `grep -rIn vnc_port` over the
plugin clone returns **zero hits** without any `--exclude-dir`.

**So [02](02-packer-tart-builder.md)'s `vnc_port` refutation is upheld with no `--exclude-dir=logs`
needed.** That matters more than it looks. The tempting fix was to teach the spec's verification command to
skip `logs/` — **a spec accommodating a defect in our own tooling**, and a permanent invitation for the
next agent to wonder why. The contamination was removed at the source instead. `verify_claims.py` now
rejects any file-scoped evidence target with a `logs` path component outright (OQ-16), so the hazard cannot
return through the ledger.

**The pattern across G10, G14, D5, G13, G9, OQ-20's half-guess and the brief's own `must_fail` rule is one
pattern.** Each was a plausible sentence nobody had executed. Most would have been caught by the first
read-only command a skeptic would type. The rest were caught only because something was built that runs the
command every time — and OQ-32 is the reminder that the thing running the commands is itself part of the
system under test.

## Local working trees (read directly, not fetched — G11)

| Path | Grade | What it gave us |
|---|---|---|
| `/Users/bossjones/dev/bossjones/zsh-dotfiles` | `[meaty]` | `.chezmoiroot`, `.chezmoiversion`, `home/.chezmoi.yaml.tmpl` (the `stdinIsATTY` non-interactive contract), `scripts/smoke-test-docker.sh` (canonical non-TTY invocation + assertion vocabulary), `test_dotfiles.py`, `CLAUDE.md`, `.github/workflows/tests.yml` — [08](08-dotfiles-test-harness.md), [09](09-dotfiles-under-test.md) |
| `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep` | `[meaty]` | `bin/zsh-dotfiles-prereq-installer`, `Brewfile`, `Makefile`, `TESTING.md`/`DEBUG.md`, `Dockerfile-{centos-9,debian-12,ubuntu-2204}` (the existing Linux coverage this repo has no macOS equivalent of) — [09](09-dotfiles-under-test.md) |
| `/Users/bossjones/dev/cirruslabs/packer-plugin-tart` | `[meaty]` | The builder's own source tree, at `c10d611`. **`.web-docs/components/builder/tart/README.md` is the file HashiCorp renders as the `/packer/integrations/...` field reference cited in [02](02-packer-tart-builder.md)** — that page is absent from HashiCorp's sitemap, so this tree, not the CMS, is its ground truth (see [Verifying Packer docs URLs](#verifying-packer-docs-urls)). `builder/tart/builder.hcl2spec.go` is the generated config schema behind that reference; `step_run.go`, `step_clone_vm.go`, `step_disk_resize.go` are the build steps; `vnc.go` is the VNC/boot-command machinery behind [12](12-tooling-and-agent-loop.md)'s `gui.py`. Also `docs/builders/tart.mdx`, `example/`, `.cirrus.yml` |
| `/Users/bossjones/dev/cirruslabs/macos-image-templates` | `[meaty]` | The Packer templates that build every `ghcr.io/cirruslabs/macos-*` image, at `cd2d1c6`. **Ground truth for what is actually inside the prebuilt images**, where the prose docs only assert it. `templates/vanilla-tahoe.pkr.hcl` sets `ssh_password`/`ssh_username = "admin"` (the G8 default creds), enables Remote Login (which is what makes the `sshpass` path in [03](03-tart-ci-and-orchard.md) work at all), and enables passwordless sudo + auto-login (the latter bears on the macOS 15+ keychain requirement). `templates/base.pkr.hcl` preinstalls the **Tart guest agent** (`brew install cirruslabs/cli/tart-guest-agent`, as both LaunchDaemon and LaunchAgent — the component backing `tart ip --resolver=agent`, see [01](01-tart-core.md#the-tart-guest-agent)) *and* Homebrew, `mise`, `rbenv`, `node@24` — which is why `-base` is not a cold-start substrate for the dotfiles under test ([08](08-dotfiles-test-harness.md)). `README.md` documents the `vanilla → base → xcode → runner` layering |
| `/Users/bossjones/dev/motionbug/macad.uk2025` | `[meaty]` | "Silicon Sandbox: Mastering Mac virtualisation for Jamf workflows" (macad.uk 2025), at `270dc24`. `packer-templates/apple-tart-tahoe.pkr.hcl` is a complete `tart-cli` IPSW-lane template for macOS 26: `from_ipsw`, `recovery_partition = "keep"` (kept so `softwareupdate` still works), `create_grace_time`, and a fully variable-ised account/MDM-enrollment config. Its Setup Assistant `boot_command` — opening `"<wait60s><spacebar>"` — is a **second independent instance** of the brittle keystroke automation [12](12-tooling-and-agent-loop.md) flags via `markkenny/macos-virtualisation`, and evidence the fragility is inherent to the approach, not one author's typo |

The two bootstrap one-liners quoted verbatim in [09](09-dotfiles-under-test.md) (G9):

| URL | Grade | What it gave us |
|---|---|---|
| [chezmoi.io/get](https://chezmoi.io/get) | `[meaty]` | The chezmoi installer the `zsh-dotfiles` bootstrap pipes into `sh` |
| [github.com/bossjones/zsh-dotfiles](https://github.com/bossjones/zsh-dotfiles) | `[meaty]` | The chezmoi source repo the bootstrap one-liner targets |
| [zsh-dotfiles-prereq-installer](https://raw.githubusercontent.com/bossjones/zsh-dotfiles-prep/main/bin/zsh-dotfiles-prereq-installer) | `[meaty]` | The prereq installer the `zsh-dotfiles-prep` bootstrap pipes into `bash` |

## Read as counter-evidence, never cited as support (G2)

| URL | Grade | What it gave us |
|---|---|---|
| [tonyyo11 — Prepping for Learning Terraform (Oct 2025)](https://tonyyo11.github.io/posts/October-Learning-Terraform/) | `[cited-as-exclusion]` | Uses Terraform to manage **Jamf Pro resources**, not VMs. Establishes **G2**: it is not evidence of VM-as-code for either tool. Referenced only in [10](10-tart-vs-utm-adr.md) to preempt the misreading |
| [motionbug — Baking Up Your Perfect Jamf Pro Test VM](https://motionbug.com/the-cookbook-baking-up-your-perfect-jamf-pro-test-vm/) | `[cited-as-exclusion]` | A Jamf-Pro-flavored VM cookbook. Same trap as above: adjacent tooling, not a VM-as-code story for tart or UTM |

## Coverage — measured, not estimated

`docs.getutm.app` publishes **78 pages**. Enumerated from its own search index, not from the nav:

```bash
curl -fsSL https://docs.getutm.app/assets/js/search-data.json |
  python3 -c 'import json,sys; print(*sorted({v["relUrl"].split("#")[0] for v in json.load(sys.stdin).values()}), sep="\n")'
```

**39 of 78 are cited above.** The 39 uncited pages, grouped — none load-bearing for this harness, but
they exist and are unread, so no reader should infer they were judged and dismissed:

| Group | Pages |
|---|---|
| Apple-backend device children | `settings-apple/devices/{display,network,serial}` |
| QEMU-backend device children | `settings-qemu/devices/{display,serial,sound}`, `.../network/{network,port-forwarding}`, `settings-qemu/drive/resize-and-compress` |
| Non-macOS guest support | `guest-support/{linux,windows}`, `guest-support/sharing/{clipboard,directory}` |
| Per-guest walkthroughs | `guides/{classic-windows,debian,fedora,kali,ubuntu,windows,windows-10}`, `guide/windows` |
| iOS | `installation/ios`, `preferences/ios` |
| Remote / UTM server | `remote/`, `remote/server/` |
| Section landing pages | `advanced/advanced`, `basics/basics`, `installation/installation`, `preferences/preferences`, `guest-support/guest-support`, `advanced/scripting` |
| Release notes | `updates/updates`, `updates/v4.0`, `v4.1`, `v4.3`, `v4.4`, `v4.5`, `v4.6`, `v4.7` |

`guest-support/sharing/{clipboard,directory}` are the only ones with plausible future relevance — they
document the SPICE WebDAV / VirtFS directory-sharing backends. Tracked in `.team/macos-ci.backlog.md`.

Three pages moved out of this list when `utmctl` was documented in [05](05-utm-automation.md) §4:
`scripting/scripting` (the CLI's wrapper nature), `guest-support/sharing/usb` (USB is QEMU-only), and
`updates/v4.2` (the release notes that introduced the guest-agent-gated commands). Recount rather than
adjust by hand:

```bash
python3 - <<'EOF'
import json, re, urllib.request, pathlib

norm = lambda u: u.split("#")[0].rstrip("/") or "/"   # the site root is a real page ("What is UTM?")

idx = urllib.request.Request("https://docs.getutm.app/assets/js/search-data.json",
                             headers={"User-Agent": "coverage/1.0"})
pages = {norm(v["relUrl"])
         for v in json.loads(urllib.request.urlopen(idx, timeout=20).read()).values()}
cited = {norm(m.group(1))
         for f in list(pathlib.Path("specs").rglob("*.md")) + [pathlib.Path("CLAUDE.md")]
         for m in re.finditer(r"https://docs\.getutm\.app(/[^)\s\"'>|]*)", f.read_text())} & pages

print(f"{len(cited)} of {len(pages)} cited")
for p in sorted(pages - cited): print("  uncited:", p)
EOF
```
