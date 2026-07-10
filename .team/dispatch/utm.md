# 🖥 utm — YOUR BRIEF

**You are `utm`.** Surface `04FF0E1E-204E-49A3-B997-5ABB3CED2D8A` (`pane:46`).
**Read [`_RULES.md`](_RULES.md) in full first.** Then this.

## You own
- `specs/macos-ci/05-utm-automation.md`
- `specs/macos-ci/06-utm-macos-guest.md`
- `specs/macos-ci/07-utm-settings-appendix.md`

## Your job — you own the files that carried the G10 damage

**G10 was the fabricated URL that this entire run exists because of.** `settings-apple/devices/` was
never a dead page: **it never existed.** The clause *"do not fetch"* is exactly what prevented its
disproof. A downstream spec then cited the wrong page for the Apple-backend device toggles while the
page that actually documents them — `settings-apple/virtualization/` — went undiscovered.
**One query for `trackpad` would have found it.**

**For EVERY `docs.getutm.app` URL in your three files:**
1. Confirm it exists in the search index → propose a **`doc-index`** claim.
2. `curl -fsSL` the page and confirm it **actually says what the spec claims** → propose a
   **`doc-contains`** claim.

> **A URL that resolves is not a sentence that is true.** `doc-index` proves a page exists;
> `doc-contains` proves it *says it*.

**Any URL absent from the index was FABRICATED** — retract it loudly, find the real page via the index,
and file the correction. (This *is* inside the index's domain, so absence **is** proof here. The G19
carve-out applies only to `/packer/integrations/**`, which is not your problem.)

`07`'s table must carry **accurate link status**. Note `07:25` already carries an `<!-- UNVERIFIED -->`
reasoning that a **TSO toggle is absent** from `settings-apple/virtualization/` — that is an argument
from a page's *complete section list*, i.e. **inference from absence**. Decide honestly whether the
index/page supports it. If it is inference, the marker **stays** and you cite an OQ.

## Re-confirm from the pages themselves — not from the previous run's summary

- **G5** — disposable mode is **QEMU-backend only**; macOS guests need Apple Virtualization.framework.
- **G6** — UTM's Apple backend does **not** support multiple graphical displays.
- **G7** — `advanced/rosetta` is about running **x86_64 ELF binaries in LINUX guests**, not macOS guests.
- **G18** — `utmctl` is a **wrapper around UTM's AppleScript interface**, not a second automation
  surface. UTM's own docs say so. `exec` / `file` / `ip-address` are the **Guest Suite** and require the
  QEMU guest agent, which Apple-backend macOS guests **do not have**. `start --disposable` and `usb`
  **parse** but are QEMU-only. UTM's macOS-guest automation surface is **lifecycle + host-side serial**.
  **There is no UTM-lane `tart ip`:** `utmctl` cannot report a macOS guest's IP.

### G5 is the canonical `cli-help` trap — do not "resolve" it

`utmctl start --help` **advertises `--disposable`**. The docs say **QEMU-only**. **Both are true.** The
flag parses; the feature cannot work. **BOTH claims belong in the ledger, and each must name the other
in its `claim` prose.** The existing pair is
`utmctl-start-help-lists-disposable` ↔ `utmctl-disposable-is-qemu-only`. **Do not collapse it.**

> **A flag in `--help` proves the argument parser accepts it. Nothing more.**
> Any `cli-help` claim about what a flag *does* needs a `doc-contains` partner.

`utmctl` **is installed**; `utmctl --help` and `utmctl <verb> --help` are allowed.
`05:112` and `05:404` carry `<!-- UNVERIFIED -->` markers on the `utm://` input-automation path. Attack
them; if the docs are silent, the markers **stay** + an OQ.

**`docs.getutm.app` 403s WebFetch. Use `curl -fsSL`.**

## Then: CROSS-AUDIT 🧪 harness's files
`08-dotfiles-test-harness.md`, `09-dotfiles-under-test.md`, `12-tooling-and-agent-loop.md`.
`08` carries **four** `<!-- UNVERIFIED -->` markers (`:62`, `:97`, `:104`, `:174`) that all say
*"cross-check against `01-tart-core.md`"* — **that is a spec citing a sibling spec as its authority, not
a source.** Attack that. `tart <verb> --help` is installed and allowed: either it verifies, or the
marker is load-bearing and needs an OQ.
**Do not edit them** — file CONFLICTs in the backlog under `### 🖥 utm`.

## Warning inherited from the lead
The master brief has been caught with a **false line-number claim** (D5) and a **false CLI claim**
(`rename-tab`). **Re-derive every line number with `sed -n 'Np' <file>`.**

Propose claims to `.team/proposed/utm.jsonl`, and **dry-run them**:
```bash
uv run tools/verify_claims.py .team/proposed/utm.jsonl
```

End with exactly:
```
TASK-DONE: utm | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
