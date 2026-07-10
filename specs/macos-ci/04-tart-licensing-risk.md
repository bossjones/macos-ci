# 04 — Tart / Orchard Licensing: Accepted Risk

Owner: tart-ci · Sources: `tart.run/licensing/`, `tart.run/blog/2023/02/11/changing-tart-license/`,
`tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/`,
`tart.run/orchard/quick-start/`

**Status: this section requires human sign-off (G4).** It documents a real commercial-licensing
exposure that this repo's CI design must stay inside, not a hypothetical.

---

## 1. The license model

Tart and Orchard ship under **Fair Source** (specifically "Fair Source 100" per the 2023 transition
announcement), not a permissive open-source license and not AGPL. (`tart.run/blog/2023/02/11/changing-tart-license/`)

**There is no open-source exemption.** Fair Source is source-available with a commercial-use ceiling —
reading or forking the code does not change the license terms. **THIS IS THE PRIMARY RISK THIS DOCUMENT
EXISTS TO FLAG.**

### What is unconditionally free

The 2023 post says, in full: *"Usage on personal computers and before reaching the 100 CPU cores limit
is royalty-free and does not have the viral properties of AGPL."*
([source](https://tart.run/blog/2023/02/11/changing-tart-license/), ledger:
`tart-2023-post-royalty-free-not-agpl`) It also promises "unlimited installations on personal computers."

Note the middle clause. An earlier draft of this section quoted the sentence as *"usage on personal
computers … is royalty-free"*, and the ellipsis swallowed **"and before reaching the 100 CPU cores
limit"** — the very qualifier this document exists to track.

### What triggers the paid tiers

The 100-core threshold applies specifically to **server installations**, which the 2023 post defines:
*"A 'server installation' refers to the installation of Tart on a physical device without a physical
display connected."* Its worked example: *"a Mac Mini with a HDMI Dummy Plug is considered a server, but
a Mac Mini on a desk with a connected physical display is considered a personal computer."*
([source](https://tart.run/blog/2023/02/11/changing-tart-license/), ledger:
`tart-2023-post-defines-server-installation`, `tart-2023-post-hdmi-dummy-plug-example`)

**This matters directly for this repo.** A typical macOS CI box is exactly the no-display server pattern
(a Mac mini or Mac Studio racked headless, or driven only via SSH/VNC). If this repo's Tart hosts are
headless, the free allowance is capped at **100 combined CPU cores across those hosts**, not "per host."

The licensing page's own wording is: *"organizations that exceed a certain number of server installations
(100 CPU cores for Tart and/or 4 hosts for Orchard) will be required to obtain a paid license."*
([tart.run/licensing/](https://tart.run/licensing/), ledger: `tart-free-tier-100-cores-4-workers`)

> **Retraction.** This paragraph previously read: *The current summary page states this as: "commercial
> use free up to 100 CPU cores (tart)."* **That sentence has never appeared on `tart.run/licensing/`,
> under any casing.** It was lifted verbatim from the verification brief's own **G4** and then attributed
> to the upstream page — a real URL decorated with an invented sentence. The ledger now guards it with
> `CONTROL-licensing-page-never-says-commercial-use-free` (`must_fail`), paired with
> `tart-licensing-page-exists` so a failure means *the sentence is absent*, not *the page is gone*.

## 2. Tier table

Every number in this table was re-verified against
[tart.run/licensing/](https://tart.run/licensing/) on 2026-07-09 and carries a ledger claim.
**No number had moved.**

| Tier | Annual cost | Tart CPU-core limit | Orchard worker limit | Ledger claim |
|---|---|---|---|---|
| Free (default) | $0 | 100 | 4 | `tart-free-tier-100-cores-4-workers` |
| Gold | $12,000/yr | 500 | 20 | `tart-gold-tier-costs-12000` · `tart-gold-tier-limits-500-cores-20-workers` |
| Platinum | $36,000/yr | 3,000 | 200 | `tart-platinum-tier-costs-36000` · `tart-platinum-tier-limits-3000-cores-200-workers` |
| Diamond | $12/core/yr (custom) | *not stated* | Unlimited | `tart-diamond-tier-12-per-core-per-year` |

The worker column is independently corroborated from a **second page**,
[tart.run/orchard/quick-start/](https://tart.run/orchard/quick-start/), via `ORCHARD_LICENSE_TIER=gold|platinum`
(ledger: `orchard-default-license-allows-4-workers`, `orchard-gold-tier-raises-limit-to-20-workers`,
`orchard-platinum-tier-raises-limit-to-200-workers`). Both pages agree.

Two precision corrections to this table as inherited:

- Diamond's Tart CPU-core cell said **"Unlimited"**. The page grants only *"the ability to run unlimited
  Orchard **Workers**"*; it says nothing about a core ceiling. "Unlimited cores" was an inference from
  per-core pricing. The cell now reads *not stated*.
- Diamond's price was written **"~$12/core/yr"**. The page states it exactly: *"costs $12 per CPU core
  per year."* The tilde was hedging a number that needed none.

*"All performance and energy-efficient cores of the host CPU are always counted towards the license
usage"* — count **every** core (P+E) of every headless Tart host, not just cores allocated to running VMs
at any instant. ([tart.run/licensing/](https://tart.run/licensing/), ledger:
`tart-all-cores-counted-toward-license`)

<!-- NOTE: the 2023 announcement blog post lists an older tier table (Gold at 100+ cores/$12K,
Platinum at 500+/$36K, Diamond at 3000+) that has since been superseded by the table above, taken from
the current tart.run/licensing/ page. The table above is authoritative; the 2023 numbers are historical
context only. -->

## 3. Enforcement is not theoretical

> **Do not refute this section by querying the tart search index.** The two blog posts §1 and §3 rest on
> return **HTTP 200** and are **absent from that index**, which covers 20 documentation pages and zero
> blog posts. `doc-index` reports them as *"fabricated or moved."* That is a **false negative**, and it is
> [G19](../../prompts/macos-ci-verify-team.md) running backwards on `tart.run`. This is recorded as
> **[OQ-08](../../.team/macos-ci.open-questions.md)** and permanently pinned by the `must_fail` control
> `CONTROL-tart-blog-is-outside-doc-index-domain`. Verify these URLs with `curl`, never with the index.

On 2025-10-27 Cirrus Labs published a press release: "Cirrus Labs Successfully Enforces Its Fair Source
License." A company "used Tart in a manner that exceeded the license's free-use limits, in order to
create a competing product" after a prior licensing request had been **declined**. The dispute was
resolved via a paid settlement (confidential terms) after months of negotiation involving named outside
counsel (Jordan Raphael of Byron Raphael LLP, and open-source/source-available licensing specialist
Heather Meeker).
([source](https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/),
ledger: `tart-2025-enforcement-press-release-is-live`, `tart-2025-enforcement-names-competing-product`)

Cirrus Labs' CEO characterized this as an exceptional case, not routine enforcement against ordinary
overage: "Most of our users have no trouble complying with our license, and even when they need
something more than our free use limits, we can almost always grant them a license that fits their
needs. This was an exceptional case." (same source) The distinguishing fact in the enforced case was
**building a competing product**, not merely running more than 100 cores. This repo does neither — it
is personal/internal CI tooling, not a competing virtualization product — but the core-count ceiling
itself is still a real, monitored term, and this press release is evidence Cirrus Labs will litigate
material violations.

## 4. What keeps this repo under the threshold

Recommendation, sized to this repo's actual stated scope (personal dotfiles CI, not a company fleet):

- **Stay on the free tier by design, not by luck.** Target a fleet of **at most 2-3 Tart/Orchard hosts**
  for dotfiles testing, each a machine in the 8-16 core class (typical Apple Silicon Mac mini/MacBook).
  That combined core count sits comfortably under 100 even with 3 hosts at the high end
  (3 × 16 = 48 cores).
- **If any host is headless** (no monitor — the common CI pattern), it counts as a "server installation"
  and its full core count applies toward the 100-core ceiling per §1. Budget accordingly; do not assume
  a "just SSH into it" Mac mini is exempt because no one is looking at the screen.
- **Orchard's separate 4-worker free ceiling is the tighter constraint in practice.** A personal fleet of
  2-3 physical hosts stays under both the 100-core Tart limit and the 4-worker Orchard limit
  simultaneously — no paid tier is needed for the orchestration layer either (spec `03`).
- **Concrete trigger condition that forces a re-decision:** if this repo's Tart usage ever grows to (a)
  more than 4 physical worker hosts, or (b) a combined CPU core count across headless hosts approaching
  100, **stop and re-evaluate before adding another host** — that is the signal to either request a Gold
  license ($12,000/yr for 500 cores / 20 workers) or reduce host count/keep hosts on-desk with a monitor
  attached. Given the Fair Source Oct-2025 enforcement precedent (§3), silently exceeding the limit and
  hoping not to be noticed is not an acceptable posture for this repo.
- **Do not build a "competing product."** The enforced case in §3 involved building a rival
  virtualization offering on top of Tart. This repo's use (internal dotfiles-install CI) is squarely
  personal/internal tooling and does not resemble that fact pattern, but it is worth stating explicitly
  as a boundary not to cross.

## 4b. Resolved: the counterparty is **OpenAI**. The tier grant is **unchanged**.

This subsection was previously titled *"Open question: the project moved to the `openai` GitHub org."* It
is no longer an open question. **Cirrus Labs was acquired by OpenAI**, announced on
[cirruslabs.org](https://cirruslabs.org/) — *"Cirrus Labs to join OpenAI"*, "Official announcement
**April 7th, 2026**", written by Fedor Korotkov (`@fedor`), who started Cirrus Labs in 2017.
(ledger: `cirruslabs-org-is-live`, `cirruslabs-org-announces-openai-acquisition`,
`cirruslabs-org-announcement-dated-april-7-2026`)

**Every fact below was re-verified read-only on 2026-07-10 and carries a ledger claim. Nothing here is
inherited.**

- The **copyright holder of tart is OpenAI.** `github.com/cirruslabs/tart` resolves to
  **`github.com/openai/tart`**; `cirruslabs/tart-guest-agent` likewise resolves to
  `openai/tart-guest-agent`. That repo's `LICENSE` is the **Functional Source License 1.1 with an
  Apache 2.0 future license (`FSL-1.1-ALv2`)** and its notice reads **`Copyright 2022-2026 OpenAI`**.
  (ledger: `cirruslabs-tart-redirects-to-openai-tart`, `openai-tart-license-is-fsl-1-1-alv2`,
  `openai-tart-license-copyright-notice-via-http`)
- **The tier numbers were re-verified and are UNCHANGED.** Every row of [§2](#2-tier-table) still matches
  [tart.run/licensing/](https://tart.run/licensing/) exactly: Free 100/4 · Gold $12,000 (500/20) ·
  Platinum $36,000 (3,000/200) · Diamond $12 per CPU core per year. **G4's dollar figures survive the
  acquisition.**
- **The 100-core Free Tier is a grant published on `tart.run`, not a clause of the FSL text.** The FSL
  mentions CPU cores **zero** times (`grep -ic 'cpu\|core'` → `0`). These are two different instruments,
  and **both are true at once** — do not collapse one into the other. `FSL-1.1-ALv2` governs the *code*;
  `tart.run/licensing/` publishes the *tier grant*. (ledger: `fsl-text-mentions-no-cpu-cores`)
- **`FSL-1.1-ALv2` converts each version to Apache 2.0 "effective on the second anniversary of" its
  release.** This *reduces* long-run exposure and §1 does not mention it. (ledger:
  `openai-tart-license-grants-apache-2-future`. The LICENSE never uses the phrase "two years"; this file
  once did, as a paraphrase. The paraphrase is accurate.)

### The wrinkle: `tart.run/licensing/` is stale relative to the acquisition

The tier-grant page contains the string **`OpenAI` exactly zero times.** It still says "Fair Source
License", still grants the 100-CPU-core Free Tier, and still directs purchasers and support to
`licensing@cirruslabs.org` / `support@cirruslabs.org`. (ledger:
`tart-licensing-page-never-mentions-openai` — a `must_fail` negative, paired on the **same URL** with the
positive control `tart-licensing-page-still-says-free-tier`, because *"OpenAI is absent"* would otherwise
be satisfied by an empty page, a 404, or a dead network. Also `tart-licensing-page-still-lists-cirruslabs-contact`.)

Those claims pin **what the page says**. They establish nothing about who would act on it.

<!-- UNVERIFIED: who would ENFORCE the Fair Source terms post-acquisition, and whether
licensing@cirruslabs.org is still the correct escalation contact. §3's enforcement precedent was a
*Cirrus Labs* action; the copyright is now OpenAI's; tart.run has not been updated to reflect either.
Settling this means corresponding with a third party, which this run may not do. See OQ-20. -->

> **Retraction of this file's own guess.** OQ-20 recorded, explicitly labelled a guess:
> *"Cirrus Labs retains the trademark, the licensing business and the `tart.run` tier grants; the GitHub
> org move reflects an acquisition or an employment transfer of the maintainer, and
> `licensing@cirruslabs.org` remains the correct contact."*
>
> **The guess was half right, and recording which half is the entire point.**
>
> | Half of the guess | Verdict |
> |---|---|
> | "an acquisition … of the maintainer" | ✅ **CONFIRMED** — announced 2026-04-07 on `cirruslabs.org` |
> | "`licensing@cirruslabs.org` remains the correct contact" | ❌ **NOT ESTABLISHED — must not be asserted** |
>
> The second half was never evidence. It was an inference from the page's *staleness*, and a stale page is
> exactly as consistent with *"nobody updated it"* as with *"it is still correct."* The address is still
> **printed**; that it is still **answered by the party who can grant a licence** is unverified, and now
> carries the marker above. **This is the same error class as `04:36`'s fabricated quotation, one level
> up: reading a page's silence as a page's assertion.**

### Consequence for the G4 sign-off — none. It stands.

The posture in [§4](#4-what-keeps-this-repo-under-the-threshold) is unchanged and needs no re-derivation:
**2–3 hosts, under 100 combined CPU cores, never build a competing product.** That keeps this repo inside
the Free Tier **under either reading of who the counterparty is**, and the FSL's second-anniversary
Apache-2.0 conversion only shrinks the long-run exposure. **G4 is signed off as an accepted, documented
risk.** What changed is *who you would be negotiating with if you ever left the free tier* — and that is
precisely the question the marker above refuses to guess at.

Re-verify (read-only; note the GitHub API returns **301** without `-L`, so a bare status probe on it is
not evidence of anything):

```bash
curl -sS -o /dev/null -w '%{http_code}' https://cirruslabs.org/                      # 200
curl -fsSL https://cirruslabs.org/ | grep -o 'Cirrus Labs to join OpenAI'            # the announcement
curl -fsSL https://api.github.com/repos/cirruslabs/tart | python3 -c 'import json,sys; print(json.load(sys.stdin)["full_name"])'
curl -fsSL https://raw.githubusercontent.com/openai/tart/main/LICENSE | head -8
curl -fsSL https://tart.run/licensing/ | grep -c 'OpenAI'                            # 0 — the page is stale
```

## 5. Consequence for the house stance

This accepted-risk section is a direct cost of the **TART IS PRIMARY** decision recorded in the ADR
(spec `10`, house stance). The counterfactual — UTM — has no equivalent licensing exposure (it is
GPLv2), but per **G1**/**G3**/**G5** it also has no IaC, no Packer builder, and no disposable macOS-guest
mode, which is why Tart remains primary despite this licensing surface. The mitigation above (small
fleet, explicit trigger condition) is the concrete control that makes accepting this risk reasonable at
this repo's scale.
