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

Personal computer usage is royalty-free and unlimited: "usage on personal computers ... is royalty-free
and does not have the viral properties of AGPL." (`tart.run/blog/2023/02/11/changing-tart-license/`)

### What triggers the paid tiers

The 100-core threshold applies specifically to **server installations** — the 2023 post defines a
server installation as "Tart running on a physical device without a connected display (e.g. Mac Mini
with HDMI dummy plug)." A Mac with a monitor attached, run interactively, stays free regardless of core
count. (`tart.run/blog/2023/02/11/changing-tart-license/`)

**This matters directly for this repo.** A typical macOS CI box is exactly the "no connected display"
server pattern (a Mac mini or Mac Studio racked headless, or driven only via SSH/VNC). If this repo's
Tart hosts are headless, the free allowance is capped at **100 combined CPU cores across those hosts**,
not "per host." The current summary page states this as: "commercial use free up to 100 CPU cores
(tart)." (`tart.run/licensing/`)

## 2. Tier table

| Tier | Annual cost | Tart CPU-core limit | Orchard worker limit |
|---|---|---|---|
| Free (default) | $0 | 100 | 4 |
| Gold | $12,000/yr | 500 | 20 |
| Platinum | $36,000/yr | 3,000 | 200 |
| Diamond | ~$12/core/yr (custom) | Unlimited | Unlimited |

(`tart.run/licensing/`, cross-checked against `tart.run/orchard/quick-start/` for the worker-count
column via `ORCHARD_LICENSE_TIER=gold|platinum`) "All performance and energy-efficient cores of the host
CPU are always counted towards the license usage" — i.e. count **every** core (P+E) of every headless
Tart host, not just cores actually allocated to running VMs at any instant. (`tart.run/licensing/`)

<!-- NOTE: the 2023 announcement blog post lists an older tier table (Gold at 100+ cores/$12K,
Platinum at 500+/$36K, Diamond at 3000+) that has since been superseded by the table above, taken from
the current tart.run/licensing/ page. The table above is authoritative; the 2023 numbers are historical
context only. -->

## 3. Enforcement is not theoretical

On 2025-10-27 Cirrus Labs published a press release: "Cirrus Labs Successfully Enforces Its Fair Source
License." A company "used Tart in a manner that exceeded the license's free-use limits, in order to
create a competing product" after a prior licensing request had been **declined**. The dispute was
resolved via a paid settlement (confidential terms) after months of negotiation involving named outside
counsel (Jordan Raphael of Byron Raphael LLP, and open-source/source-available licensing specialist
Heather Meeker). (`tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/`)

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

## 5. Consequence for the house stance

This accepted-risk section is a direct cost of the **TART IS PRIMARY** decision recorded in the ADR
(spec `10`, house stance). The counterfactual — UTM — has no equivalent licensing exposure (it is
GPLv2), but per **G1**/**G3**/**G5** it also has no IaC, no Packer builder, and no disposable macOS-guest
mode, which is why Tart remains primary despite this licensing surface. The mitigation above (small
fleet, explicit trigger condition) is the concrete control that makes accepting this risk reasonable at
this repo's scale.
