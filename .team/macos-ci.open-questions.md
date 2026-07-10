# Open Questions — macos-ci verification run

This is the shared record of questions the team could not settle within scope. Append only; never rewrite another agent's block.

---

## OQ-01 · secrets · BLOCKED-BY-SCOPE
**Status:** BLOCKED-BY-SCOPE  
**Spec:** specs/macos-ci/13-build-secrets.md:54  
**Question:** Does `disk_format = "asif"` (macOS 26+, sparse) preserve the unlink-does-not-zero residue that 13-build-secrets.md:54 assumes?  
**What I tried:** None yet; this blocks the team.  
**Why it is stuck:** Needs a booted VM running `strings` against `~/.tart/vms/<name>/` to verify the claim. This run forbids VM boots.  
**My best guess, explicitly labelled a guess:** unlink-does-not-zero is generic to block-backed filesystems, so residue probably survives; but `asif` is sparse and may never allocate the block at all, or may trim on delete.  
**Cost of guessing wrong:** if `asif` does *not* preserve residue we over-warn (harmless). If we assume it is safe and it *does* preserve residue, a build secret written to the guest leaks into every published image. The asymmetry is why 13 keeps the marker.  
**Correction (👑 lead, SCAFFOLD):** the `**Spec:**` citation `13-build-secrets.md:54` was **re-verified and is correct** (`sed -n '54p'` → `<!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (macOS 26+), a sparse format`). Required fields `My best guess` / `Cost of guessing wrong` were absent from the original block and are supplied above.  

---

## OQ-02 · harness · BLOCKED-BY-SCOPE
**Status:** BLOCKED-BY-SCOPE  
**Spec:** specs/macos-ci/12-tooling-and-agent-loop.md:359  
**Question:** Is `--vnc-experimental`'s stdout really `Opening vnc://:<password>@127.0.0.1:<port>...`?  
**What I tried:** None yet; this blocks the team.  
**Why it is stuck:** G13 documents this format from one reported example, not from a booted VM. Settling it requires booting a tart VM with `--vnc-experimental` enabled, which this run forbids.  
**My best guess, explicitly labelled a guess:** the format is approximately right but the trailing `...` and the empty user field before `:` are reconstructed from prose, not copied from a terminal.  
**Cost of guessing wrong:** any harness code that regex-parses this line to extract the VNC port silently fails to match, and the GUI lane breaks with no diagnostic.  
**Correction (👑 lead, SCAFFOLD):** this block originally cited `12-tooling-and-agent-loop.md:607`. **That line does not exist — the file is 535 lines long** (`wc -l` → 535). The real `<!-- UNVERIFIED -->` marker for `--vnc-experimental` is at **`:340`**, confirmed with `sed -n '340p'`. The `:607` citation was hallucinated by the prior (Haiku) lead pass and is corrected above. This is exactly the failure mode the ledger's `file-line` evidence kind exists to kill — and it appeared in the one artefact the human reads directly. A `file-line` claim pinning `:340` is proposed in `.team/proposed/lead.jsonl` so it can never silently rot again.  

**Correction #2 (👑 lead, CROSS-AUDIT) — the citation rotted AGAIN, inside this same run, and the ledger is what caught it.**
🧪 harness's edits grew `12-tooling-and-agent-loop.md` from **535 → 577 lines**, moving the marker from
`:340` to **`:359`**. Correction #1 above was true when written and false forty minutes later. The
`**Spec:**` line is now `:359`, verified with `grep -n`:
```
$ sed -n '340p' specs/macos-ci/12-tooling-and-agent-loop.md
`_gui_core.parse_vnc_url()` turns that line into a `VncTarget`; `gui.py` connects with `asyncvnc`, sends
$ grep -n 'UNVERIFIED: `--vnc-experimental`' specs/macos-ci/12-tooling-and-agent-loop.md
359:<!-- UNVERIFIED: `--vnc-experimental` is labelled experimental by Tart itself, and the exact stdout
```
**Nobody noticed by reading. The ledger noticed by executing.** 🔬 ledger re-pinned it as
`oq02-vnc-marker-pinned-at-12-359` **and** added `oq02-vnc-marker-exists-regardless-of-line`
(`file-contains`), which is immune to line drift. That pairing — a precise pin that rots loudly plus a
line-agnostic claim that cannot — is the right shape for every `file:line` citation in this repo.

**The lesson, stated plainly:** a `file:line` citation in *prose* is a fact with a half-life. The
prior lead hallucinated one; the current lead wrote a true one that decayed within the hour. Only the
re-executable claim survived both. This is the strongest argument in the repo for **OQ-05** and for the
`file-line` evidence kind existing at all. See also 🔬 ledger's warning that
`CONTROL-12-line-607-does-not-exist` is now only **30 lines** from accidental validity (577 → 607).  

---

## OQ-03 · lead · ANSWERED
**Status:** ANSWERED  
**Spec:** (meta — FSM signal)  
**Question:** Is the cmux turn-done event `notification.created` or `notification.requested`?  
**What I tried:** Examined cmux 0.64.17 binary; both strings are present. `cmux events --help` documents no event names.  
**Why it is stuck:** Cannot settle read-only without firing a notification. The brief uses one string; the `boss-cmux` skill mentions the other. Both are plausible.  
**Resolution:** Use `cmux events --category notification --no-heartbeat --no-ack` to capture all notification-category events. Confirm completion via the printed `TASK-DONE:` sentinel (more authoritative).  
**Correction (👑 lead, SCAFFOLD):** the line above is mislabelled. It is a **workaround, not a resolution** — it sidesteps the question by subscribing to the whole `notification` *category* rather than answering which event *name* is emitted. The underlying question is still unanswered, so `**Status:** OPEN` is correct and must stay OPEN. `cmux events --help` documents no event names; both `notification.created` and `notification.requested` appear as strings in the 0.64.17 binary. Settling it requires *firing* a notification and observing the emitted name, which this run can do as a side effect of dispatch — if an event lands, its `name` field answers OQ-03. **My best guess, explicitly labelled a guess:** `notification.requested`, because the `boss-cmux` skill is generated from the binary while the master brief was hand-written. **Cost of guessing wrong:** a lead that waits on the wrong `--name` blocks forever on a filter that never matches, and mistakes a hung team for a working one. This is why the sentinel, not the event, is authoritative.  

**Resolution (👑 lead, SCAFFOLD) — the question was a FALSE DICHOTOMY. Both events are real.**
Settled empirically by firing one notification and capturing the stream:

```
cmux events --category notification --no-heartbeat --no-ack > events.jsonl &
cmux notify --title "👑 lead" --subtitle "OQ-03 probe" --body "..." --workspace $WS
```

A **single** `cmux notify` emits **both**, ~1 ms apart:

| `name` | `source` | meaning |
|---|---|---|
| `notification.created` | `notification.store` | the notification was stored |
| `notification.requested` | `socket.v2` | the RPC `notification.create_for_caller` was called |

So the master brief (`notification.created`) and the `boss-cmux` skill (`notification.requested`) are
**both correct**; neither is wrong, and my guess above (that the skill was right and the brief wrong)
was itself **wrong**. Filtering on either name alone works. Three further facts, none of which the
brief states:

1. `notification.clear_requested` also rides the `notification` category, but carries
   `"workspace_id": null` — so a `workspace_id` filter already excludes it. No `grep -v` needed.
2. Both real events carry **`surface_id`** and `workspace_id`. The lead can therefore attribute a
   notification to the *specific worker* that fired it, which is strictly better than the brief's
   workspace-level match.
3. **The payload is redacted:** `"redacted_fields": ["title","subtitle","body"]`, and `title`/`body`
   come back `null` with only `title_length` / `body_length` populated. **The event tells you WHO
   finished, never WHAT they said.** This independently confirms the addendum's rule from a second
   direction: the event is a *free early exit*; the printed `TASK-DONE:` sentinel, read via
   `cmux read-screen --scrollback`, is the only authoritative content signal.

---

## OQ-04 · secrets · NEEDS-HUMAN
**Status:** ANSWERED  
**Spec:** (meta — decision required)  
**Question:** Should `build-golden` be guarded to fail loudly when the template is missing, or should the template be authored?  
**What I tried:** None; this is a human decision about scope.  
**Why it is stuck:** Justfile:44 invokes `packer/tart-golden-image.pkr.hcl`, which does not exist. This run's scope forbids authoring it and forbids running `packer build` to validate it. We can only document that it is absent.  
**My best guess:** Guard `build-golden` with a check: test for template existence before invoking `packer build`.  
**Cost of guessing:** If the template should exist but doesn't, CI is broken. If it shouldn't exist, the guard is noise.

**Resolution (human decision, implemented by 👑 lead):** **guard it.** The template stays unauthored — `packer build` / `packer init` are forbidden by scope, so not one line of it could be validated. Only the *failure mode* changes. `Justfile:build-golden` now opens with a `test -f` guard that exits **4** (USAGE, matching `verify_claims.py`) before `packer build` is ever reached.

Verified by execution, after first confirming `packer/` does not exist so `packer build` was provably unreachable — that precondition is what made running a previously-forbidden recipe safe:

```
$ just build-golden ; echo "EXIT=$?"
missing: packer/tart-golden-image.pkr.hcl
see specs/macos-ci/13-build-secrets.md and OQ-04
error: Recipe `build-golden` failed on line 49 with exit code 4
EXIT=4
```

Two ledger claims pin it: `justfile-build-golden-guards-on-missing-template` (`Justfile:46`) and `justfile-build-golden-guard-exits-4` (`:49`, before `packer build` at `:52`). Both PASS.

**Note the blast radius, recorded because the gate hides it.** This six-line edit invalidated the `file-line` pin `d1-justfile-44-invokes-absent-template` (line 44 → 52). 🔬 ledger re-derived and renamed it `d1-justfile-build-golden-names-absent-template`. **The `line` field is evidence; the `id` is prose, and prose rots.** See the lead's backlog entry: *never put a line number in an identifier.*  

---

## OQ-05 · lead · OPEN · Can the D5′ honesty budget still be gamed, by wrapping a real marker's line in backticks?
**Status:** OPEN  
**Spec:** Justfile:63  
**Question:** `unverified-count` now excludes every line matching the literal `` `<!-- UNVERIFIED `` (backtick immediately before the marker). A line that carries a **real** marker *and also* mentions the marker inside a code span anywhere else on that line would be silently dropped from the budget. Is the discriminator sound, or merely sound today?  
**What I tried:**
```
grep -rn 'UNVERIFIED' specs/ --include='*.md' | wc -l                          -> 22
grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -vc '`<!-- UNVERIFIED'    -> 16   (kept)
grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -v '`<!-- UNVERIFIED' \
  | grep -cE '<!-- UNVERIFIED'                                                 -> 16   (all kept lines carry a real marker: no false positives)
grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep '`<!-- UNVERIFIED' \
  | grep -E '(^|[^`])<!-- UNVERIFIED[^`]*-->'                                  -> (empty)  (no dropped line carries a real marker: no false negatives TODAY)
```
**Why it is stuck:** soundness *today* is an empirical fact about the current 22 lines, not a property of the grep. Settling it properly means parsing markdown well enough to know whether a marker sits inside a code span — a real parser, not a `grep -v`. That is a tooling change (`tools/`), which only 🔬 ledger owns, and it is arguably out of this run's scope.  
**My best guess, explicitly labelled a guess:** the discriminator holds for the current corpus and will keep holding while authors write prose mentions as `` `<!-- UNVERIFIED -->` `` and real markers bare. It is a lint convention masquerading as a parser.  
**Cost of guessing wrong:** the exact failure D5 was written to prevent, one layer up. An author could retire a real marker from the budget *without verifying anything* by adding backticks around a second mention on the same line, and the lead's before/after diff could not tell that apart from honest work. **A budget you can pay down by editing punctuation is not a budget.**  
**Note:** D5′ is still a strict improvement over D5 — the original `grep -rc 'UNVERIFIED'` counted all 22 and D5's proposed "fix" (`grep -rh '<!-- UNVERIFIED'`) was a **no-op** returning the same 22. See the D5 retraction in the backlog.

---

## OQ-06 · lead · OPEN · Does `unverified-count` actually emit a count?
**Status:** OPEN  
**Spec:** Justfile:61-63  
**Question:** The recipe is named `unverified-count` and the brief calls it "the honesty budget", but it prints **marker lines**, not a number. The lead's baseline diff therefore compares two line-lists by eye.  
**What I tried:** `just unverified-count` → a header line plus 16 `path:line:text` lines. No integer anywhere in the output. `wc -l` on the captured output is how this run derived "16".  
**Why it is stuck:** not stuck on evidence — stuck on a decision. Emitting a trailing count (`| tee >(wc -l)`, or a final `echo`) is a one-line `Justfile` change the lead owns, but the brief pins the *only* permitted `Justfile` edit this run to the D5′ fix at line 63. Changing it further would exceed the scope the human set.  
**My best guess, explicitly labelled a guess:** a trailing `printf '  → %d markers\n'` would make the budget machine-checkable and diffable, and nothing depends on the current output shape.  
**Cost of guessing wrong:** low. But a budget nobody can `diff` mechanically is a budget enforced by attention, and attention is what this run exists to distrust.

---

## OQ-07 · lead · ANSWERED · Why does bare `cmux rename-tab "<title>"` fail with `not_found: Tab not found`?
**Status:** ANSWERED (retraction of the master brief's STATUS BOARD section)  
**Spec:** prompts/macos-ci-verify-team.md — STATUS BOARD  
**Question:** The brief states: *"`rename-tab` resolves its target as `--tab` → `--surface` → `$CMUX_TAB_ID`/`$CMUX_SURFACE_ID` → focused tab, so renaming yourself needs NO target flag."* Every agent is told to keep its tab pill current this way. Does it work?  
**What I tried:**
```
$ cmux rename-tab "👑 lead 1/7 [#---------] · baseline pasted, dispatching"
Error: not_found: Tab not found

$ echo "CMUX_TAB_ID=[$CMUX_TAB_ID]  CMUX_SURFACE_ID=[$CMUX_SURFACE_ID]"
CMUX_TAB_ID=[E03FB8FF-87D2-4BD9-A65B-E2E7B1ECFE42]  CMUX_SURFACE_ID=[6D646A29-6D21-4F77-BC52-E54C9DAF6118]

$ cmux rename-tab --surface 6D646A29-6D21-4F77-BC52-E54C9DAF6118 "👑 lead 1/7 …"
OK action=rename tab=tab:52 workspace=workspace:11
```
**Resolution — the brief is RETRACTED on this point.** `$CMUX_TAB_ID` does **not** contain a tab id. It contains the **workspace** UUID (`E03FB8FF-…`, identical to `$CMUX_WORKSPACE`-scoped ids used elsewhere). `rename-tab` dutifully tries to resolve that UUID *as a tab*, finds no such tab, and errors. The documented fallback chain therefore dead-ends before it ever reaches "focused tab".

**Two consequences, one of them dangerous:**
1. **Every worker** instructed to run bare `cmux rename-tab "<pill>"` gets `Error: not_found`. All seven status pills would silently never update, and a lead reading tab titles would see a frozen team.
2. **Worse, if the fallback *had* reached "focused tab":** the focused pane at SCAFFOLD was `pane:45` (🏭 tart-ci), **not** the lead. A bare `rename-tab` from the lead would have relabelled *tart-ci's* tab. Positional/focus-based targeting is exactly the renumbering hazard the addendum's "address workers by surface UUID" rule exists to avoid — and the brief reintroduced it for tab renames.

**The fix, propagated into every dispatch brief:** always pass the surface explicitly.
```
cmux rename-tab --surface "$CMUX_SURFACE_ID" "<emoji> <role> <n>/<N> [<bar>] · <log>"
```
`$CMUX_SURFACE_ID` **is** correct and per-pane; only `$CMUX_TAB_ID` is misleading.
**Cost of guessing wrong:** had this not been caught pre-dispatch, the run's entire status-reporting surface would have been dead on arrival, and the failure mode (a never-updating pill) is indistinguishable from a hung agent.

---
## OQ-08 · tart-ci · Does the `tart` doc-index oracle cover `tart.run/blog/**`, or is this a second, unnamed G19-class carve-out?
**Status:** OPEN (blocks a ledger/tooling decision only 🔬 ledger can make)
**Spec:** specs/macos-ci/04-tart-licensing-risk.md:60-65 (§3 enforcement precedent), and prompts/macos-ci-verify-team.md — 🏭 tart-ci worker brief
**What I tried:**
```
curl -sS -o /dev/null -w '%{http_code}' https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/
  -> 200                                   # THE PAGE IS REAL
curl -sS -o /dev/null -w '%{http_code}' https://tart.run/blog/2023/02/11/changing-tart-license/
  -> 200                                   # SO IS THIS ONE

# but the tart search index (tools/verify_claims.py DOC_INDEXES["tart"]) holds 20 pages, ZERO of them posts:
python3 -c '...' -> blog/  blog/archive/{2023,2024,2025}/  blog/category/{announcement,orchard}/  faq/ ...
  [e["location"] for e in d["docs"] if e["location"].startswith("blog/2")]  -> NONE
  "heather meeker" / "successfully enforces" / "competing product"          -> ABSENT from the whole index

# dry-run of the two claims my brief literally orders me to write:
uv run tools/verify_claims.py <probe>
  [FAIL] PROBE-blog-doccontains  STRUCTURE: page '/blog/2025/.../press-release-...' is not in the tart index — fabricated or moved
  [FAIL] PROBE-blog-docindex     '/blog/2025/.../press-release-...' is not in the tart search index (20 pages) — fabricated or moved
```
**Why it is stuck:** The `doc-index` oracle reports a page that returns **HTTP 200** as *"fabricated or moved"*. `_RULES.md` §3 says absence from an index is *proof of fabrication* **inside the prefixes it covers** — and names exactly one carve-out (G19, `/packer/integrations/**`). **`tart.run/blog/**` is a second carve-out that nobody named.** An agent applying "default to refuted" to §3's enforcement precedent would retract a real, load-bearing page with total confidence: **G10 running backwards, on my file.**

This also makes my own worker brief unexecutable as written. It says: *"Use `doc-contains`, not just `doc-index`: a URL that resolves is not a sentence that is true."* With the current `tools/verify_claims.py`, `doc-contains` **cannot reach any tart blog post at all** — it reads the search-index text, never the live page (`tools/verify_claims.py:240-247`), so it returns `STRUCTURE:`, which `must_fail` may never invert. The instruction is correct in spirit and impossible in fact.

**Workaround found, and dry-run PASSING** (so this OQ blocks a *decision*, not my deliverable): a `cli-help` claim whose `argv` is `curl -fsSL <url>` does reach the live page, because `cli-help` greps `stdout+stderr` (`tools/verify_claims.py:225`). Verified:
```
[PASS] PROBE-curl-clihelp-press  expect="This was an exceptional case"
[PASS] PROBE-curl-clihelp-2023   expect="HDMI Dummy Plug"
[FAIL] PROBE-curl-clihelp-spanning  expect="Gold Tier License , which costs $12,000 per year"   # tag-spanning: correctly fails
```
The third probe is the honest part: the mechanism greps **raw HTML**, so any literal broken by an inline tag fails. It is sound for short, tag-free phrases and silently useless for long ones.
**Why it still needs 🔬 ledger:** `cli-help` swallows curl's exit code — it only greps output. A network outage makes `curl -fsSL` print nothing, and the claim FAILS rather than reporting `UNREACHABLE:`. That is a **false refutation on a flaky network**, and it is exactly the prefix-discipline the tool built `UNREACHABLE:`/`STRUCTURE:` to preserve. A `url-contains` evidence kind that fetches the page and distinguishes transport failure from sentence-absence would fix both this and `doc-contains`'s blind spot. Only 🔬 ledger owns `tools/verify_claims.py`.
**My best guess, explicitly labelled a guess:** MkDocs Material's `search` plugin indexes only pages under the `docs/` tree; the `blog` plugin's generated post pages are excluded from `search_index.json` by default. I did **not** verify this against MkDocs' source — it is a guess about *why*, not about *whether*. The *whether* is settled: the posts are absent and the URLs are 200.
**Cost of guessing wrong:** If the index really were authoritative over `/blog/**`, then §3's entire enforcement precedent — the reason `04` exists and the reason a human must sign off — cites a fabricated page, and the tier table's provenance collapses. It does not: both posts return 200 and `curl` finds every sentence `04` relies on. The live danger runs the other way. **A future agent told to "default to refuted" and handed a `doc-index` oracle that answers *"fabricated or moved"* for a real page will delete a true citation and record a fabrication that never happened.** That is precisely the failure this whole run was convened to prevent, and the oracle now points at it.

---

## OQ-09 · utm · Do the `utm://sendText` and `utm://click` URL-scheme actions work against an Apple-backend macOS guest?
**Status:** BLOCKED-BY-SCOPE  
**Spec:** specs/macos-ci/05-utm-automation.md:112 and specs/macos-ci/05-utm-automation.md:404 (both re-derived with `sed -n '112p;404p'`)  
**What I tried:** Fetched the whole of [advanced/remote-control](https://docs.getutm.app/advanced/remote-control/) — all 6 indexed sections, 3759 chars — and searched its full text:

```
'QEMU'        in remote-control page: False
'backend'     in remote-control page: False
'Apple'       in remote-control page: False
'guest agent' in remote-control page: False
'not supported' in remote-control page: True   # <- this is `pause`'s "(not supported for all VMs)", nothing to do with backends
```

The page documents `sendText` / `click` with **no backend qualifier of any kind**. By contrast the AppleScript
Input Automation Suite carries an explicit header — verified verbatim on
[scripting/reference](https://docs.getutm.app/scripting/reference/): `"Only supported on QEMU backend"`.
**Why it is stuck:** The two surfaces may or may not share an implementation. If `utm://sendText` is a thin
wrapper over the Input Automation Suite, it is QEMU-only and 05's table is right to say "No". If it is
implemented against the VM's display/HID layer directly, it may work on the Apple backend. **The docs are
silent, and silence is not a "yes" nor a "no".** Settling it requires booting an Apple-backend macOS guest
and running `open "utm://sendText?name=<vm>&text=abc"`, which this run forbids.
**My best guess, explicitly labelled a guess:** it *works*, because `utm://click` takes pixel coordinates
(a display-layer concept) rather than scan codes (a QEMU input-device concept), and the Input Automation
Suite's restriction is stated where it applies and nowhere else.
**Cost of guessing wrong:** if we assume it works and it does not, the UTM lane's only scripted-UI path is
dead and any recovery-mode/GUI automation built on it silently no-ops. If we assume it does not work and it
does, we discard the one input-automation primitive the Apple backend has. **The marker stays on both lines.**

---

## OQ-10 · utm · What *is* the Apple-backend "similar option" to TSO that UTM's QEMU settings page promises?
**Status:** OPEN  
**Spec:** specs/macos-ci/07-utm-settings-appendix.md:25 (re-derived with `sed -n '25p'`)  
**What I tried:** [settings-qemu/qemu](https://docs.getutm.app/settings-qemu/qemu/) states, verbatim, inside
the `Use TSO` bullet (I pulled 900 chars of surrounding context to confirm attribution — the sentence sits
after the TSO paragraph and before `Use local time for base clock`, so it *is* about TSO and not a
neighbouring option):

> macOS **This option is not supported on macOS however when using the Apple virtualization backend, a
> similar option is available.**

I then enumerated every page in UTM's 78-page index whose text mentions `TSO`: only
`/settings-qemu/qemu/`, `/updates/v4.1/` and `/updates/v4.6/`. Both `updates` hits are about the **QEMU**
backend (v4.1 = iOS TrollStore + QEMU; v4.6 = "TSO for QEMU VMs using QEMU backend on macOS 15"). And
`/settings-apple/virtualization/` publishes its own complete section list —
`Balloon Device | Entropy Device | macOS 12+ Sound | macOS 12+ Keyboard | macOS 12+ Pointer | macOS 13+ Trackpad | macOS 13+ Rosetta | macOS 13+ Clipboard Sharing`
— **eight sections, no TSO.** Confirmed against the live page too (`curl -fsSL`), not just the index.
**Why it is stuck:** UTM's docs affirmatively assert the Apple-backend option **exists** and then never name
it. No page in the index documents it. This is an upstream documentation gap, not something a read-only
command here can settle; it would need reading UTM's source or asking upstream.
**My best guess, explicitly labelled a guess:** the "similar option" is the **Rosetta** toggle —
`/updates/v4.1/` says "TSO is used by Rosetta on the Mac to improve x86_64 emulation on ARM64", so enabling
Rosetta on the Apple backend plausibly enables TSO implicitly. If so it is Linux-guest-only (G7) and
irrelevant to a macOS guest either way.
**Cost of guessing wrong:** low for this repo — no lane depends on TSO. But 07:25's phrase "**still
undocumented**" is the load-bearing part, and it rests on *inference from a page's complete section list*,
never on an explicit denial. **That is inference from absence, so the `<!-- UNVERIFIED -->` marker stays**,
now citing this OQ.

---

## OQ-11 · utm · Is there a documented way to auto-mount a VirtioFS share on a *macOS* guest across reboots?
**Status:** BLOCKED-BY-SCOPE  
**Spec:** specs/macos-ci/06-utm-macos-guest.md:76 (re-derived with `sed -n '76p'`)  
**What I tried:** [guest-support/macos](https://docs.getutm.app/guest-support/macos/) documents only the
manual, per-boot form (`mount_virtiofs share [mount point]`, confirmed present in the page text). By
contrast [advanced/rosetta](https://docs.getutm.app/advanced/rosetta/) *does* give a persistent recipe — but
for a **Linux** guest, via `/etc/fstab`: `rosetta /media/rosetta virtiofs ro,nofail 0 0`. There is no
`/etc/fstab`, launchd, or login-item equivalent anywhere in the macOS-guest page.
**Why it is stuck:** proving a mount persists across a guest reboot requires booting a macOS guest, mounting,
rebooting, and re-checking. This run forbids VM boots. The docs' silence cannot distinguish "auto-mount is
impossible" from "auto-mount is undocumented".
**My best guess, explicitly labelled a guess:** it is merely undocumented; a LaunchDaemon invoking
`mount_virtiofs` at boot would work, since `mount_virtiofs` is a normal mount helper.
**Cost of guessing wrong:** the harness (`08`) relies on "shared directory in, SSH command out" (`06` §3.3).
If the share cannot be made persistent, every harness run must re-mount it after each guest boot — a
one-line provisioning step, not a design change. Low cost, hence the marker rather than a redesign.

---

## OQ-12 · utm · `doc-contains` resolves against the search index's page-**body** text, not the live page. Should the ledger say so?
**Status:** OPEN  
**Spec:** tools/verify_claims.py:235-245 (re-derived: `sed -n '235,245p'` → the `doc-contains` branch, which
does `index_cache[site][page]` lookups, never an HTTP GET of the page itself)  
**What I tried:** I wrote a probe that checks each quoted sentence against **both** the index text and the
live HTML, for all 37 sentences my three specs quote. Two diverged:

| page | sentence | in index? | in live HTML? |
|---|---|---|---|
| `/advanced/rosetta/` | `macOS guest` | no | **YES** |
| `/settings-apple/devices/devices/` | `Serial` | no | **YES** |

Both live-HTML hits are **navigation-sidebar chrome**, not page content: the sidebar renders
`… Preferences · iOS · macOS · Guest Support …`, which collapses to the substring `macos guest`; and the
Devices sidebar lists the sibling pages Display/Network/Serial. **So the index is the *better* oracle here,
and `verify_claims.py` is right to prefer it** — a naive `curl | grep` would have "confirmed" that the
Rosetta page discusses macOS guests, which it does not. That is G10's failure mode with a different mask.
**Why it is stuck:** not stuck on evidence — stuck on ownership. This is a docstring/comment change to
`tools/verify_claims.py`, which **only 🔬 ledger may edit**. I record the finding; ledger decides.
**My best guess, explicitly labelled a guess:** the behaviour is correct and deliberate, but undocumented.
The docstring says "page `page`'s indexed text", which is accurate but easy to skim past. Two consequences
are worth stating outright: **(1)** a sentence that appears only in a page's nav/TOC is **unreachable** by
`doc-contains` and a claim asserting it will FAIL even though the page "says" it; **(2)** conversely, a
`must_fail` control can never be defeated by nav chrome.
**Cost of guessing wrong:** an agent who writes a true `doc-contains` claim, watches it fail, and "fixes" it
by loosening `expect` has silently weakened the oracle. That is how a green check comes to mean nothing.

---

## OQ-23 · ledger · BLOCKED-BY-SCOPE · Every secret-masking claim probes `packer inspect`, which never runs a provisioner. Does masking hold on the `packer build` path that actually produces the image?
> _(Renumbered OQ-08 → OQ-23 by 🔬 ledger: 🏭 tart-ci had already taken OQ-08. `_RULES.md` §6: the racer renumbers upward.)_
**Status:** BLOCKED-BY-SCOPE
**Spec:** specs/macos-ci/13-build-secrets.md:1 (whole spec); `.team/claims.jsonl` — `packer-sensitive-masks-value`, `packer-sensitive-hides-secret`, `packer-sensitive-hides-secret-under-debug-log`, `CONTROL-packer-inspect-prints-plain-literals`, `CONTROL-packer-debug-log-prints-plain-literals`, and my new `g16-*` pair.
**What I tried:**
```
packer inspect tests/fixtures/packer-sensitive          -> var.sec: "<sensitive>"  (136 bytes)
PACKER_LOG=1 packer inspect tests/fixtures/packer-sensitive  -> 981 bytes, 2x <sensitive>, 0x ghp_FIXTURE_SENTINEL
PKR_VAR_pub='ghp_FIXTURE_SENTINEL_AND_MORE' packer inspect tests/fixtures/packer-sensitive
    -> var.pub: "<sensitive>_AND_MORE"     # masking is a SUBSTRING rewrite over the output
```
The third probe is new this run and settles G16 affirmatively — and more strongly than G16 states: `admin`
inside `administers` is rewritten to `<sensitive>isters`. Two claims now pin it.

**Why it is stuck:** all seven masking claims run `packer inspect`. `inspect` parses HCL and prints the
variable table. **It never instantiates a builder, never runs a provisioner, never renders
`environment_vars`, and never emits a single line of shell-provisioner log output.** 13-build-secrets.md's
operative guarantee is about the *build* path — that a secret passed through `environment_vars` with
`use_env_var_file = false` does not reach the build log or the artifact. `packer build` and `packer init`
are both FORBIDDEN by SCOPE, so no claim in this ledger touches the code path the spec is actually about.
Settling it needs `packer init` (to fetch the tart plugin) plus `packer build` against a real VM.

**Secondary gap, same root:** no ledger claim verifies that the shell provisioner's `use_env_var_file`
field exists at all. It is documented at `developer.hashicorp.com/packer/docs/provisioners/shell`, which is
in the HashiCorp sitemap — but `tools/verify_claims.py`'s `DOC_INDEXES` covers only `tart` and `utm`. There
is no `doc-index`/`doc-contains` oracle for HashiCorp, so the field cannot currently be expressed as a
claim. Adding one is a real extension of the verifier (a third site, and the sitemap is XML, not a search
JSON), which I did not undertake unasked.

**My best guess, explicitly labelled a guess:** masking holds on the build path too — packer's redaction is
implemented in its logging/UI layer over a set of registered sensitive *values*, which is precisely what the
`PKR_VAR_pub` bleed probe demonstrates (an unrelated variable's value got rewritten, so the filter is not
scoped to the sensitive variable's own render site). A filter that indiscriminate is unlikely to be wired
only into `inspect`.

**Cost of guessing wrong:** the entire point of 13-build-secrets.md. If masking is weaker on the build path
(e.g. a provisioner echoing `$HOMEBREW_GITHUB_API_TOKEN`, or a crash dump, or `PACKER_LOG_PATH` output),
the token lands in the build log and, if `use_env_var_file` defaults to `true`, in a tempfile inside the
guest — where G15 says `rm` will not erase it. The spec's central promise ("the golden image carries no
build secret", HOUSE STANCE) would be false, and the ledger would be **green while being wrong**: seven
passing claims that all probe the one command that cannot exercise the failure.

## OQ-17 · harness · ANSWERED · Sheldon 0.6.6 has no non-mutating verify verb — what should the "Sheldon lock resolves" assertion actually run?
**Status:** ANSWERED
**Renumbered from OQ-08 (🧪 harness):** three agents — 🏭 tart-ci, 🔬 ledger, 🧪 harness — each filed an `OQ-08`, and two filed an `OQ-09`. Per `_RULES.md` §6 (*"if you race, renumber yours upward"*) mine move to **OQ-17** / **OQ-18**. The `OQ-08` and `OQ-09` blocks above belong to other agents. **Two `OQ-08` blocks still collide (tart-ci ↔ ledger) — 👑 lead must adjudicate; `02-packer-tart-builder.md:135` cites a bare "OQ-08" and is now ambiguous three ways.**
**Spec:** specs/macos-ci/08-dotfiles-test-harness.md:189
**Question:** 08's assertion layer says `sheldon lock --check` (or equivalent non-mutating verify) exits 0. The existing `<!-- UNVERIFIED -->` marker asks to "confirm exact non-mutating flag against sheldon 0.6.6's `--help`". Confirmed: **there is no such flag, and no such verb.**
**What I tried:**
```
$ sheldon --version
sheldon 0.6.6 (31c6df8f7 2022-01-29)          # == the pinned mySheldonVersion at .chezmoi.yaml.tmpl:131

$ sheldon lock --help
sheldon-lock
Install the plugins sources and generate the lock file
OPTIONS:
        --update       Update all plugin sources
        --reinstall    Reinstall all plugin sources
    -h, --help         Print help information

$ sheldon --help | sed -n '/SUBCOMMANDS/,$p'
    init  add  edit  remove  lock  source  completions  version
```
`--check` does not exist. `lock` is, by its own help text, an *installer*. The only read-shaped verb is `source` ("Generate and print out the script"), and I cannot tell from `--help` whether `sheldon source` silently re-locks when the lock file is stale or missing — which on a fresh guest it always is.
**Why it is stuck:** settling it needs `sheldon source` run against a guest that has a `plugins.toml` and *no* lock file, with the filesystem watched for writes. That is a booted VM, which this run forbids. Reading sheldon 0.6.6's source is possible in principle but it is not on this machine and is outside the read-only allowlist.
**My best guess, explicitly labelled a guess:** `sheldon source` does lazily lock, so it is *not* non-mutating, and there is no non-mutating verify in 0.6.6 at all. The honest assertion is the one upstream already makes — assert the *rendered* `~/.zshrc` sources sheldon's output and that `zsh -c 'source ~/.zshrc'` exits 0 (`smoke-test-docker.sh:388-404`) — and drop the lock-file check entirely.
**Cost of guessing wrong:** if `sheldon source` does lock, an assertion billed as read-only mutates the VM under test between assertions, and a later "did the dotfiles install cleanly" check is asserting against state its own test suite created. That is the exact class of self-confirming test this harness exists to avoid. If instead I drop a check that *was* safe, we lose one signal — the cheaper error.
**Proposed ledger claims (dry-run PASS):** `sheldon-installed-is-the-pinned-0-6-6`, `sheldon-lock-has-no-check-flag` (`must_fail`) + `CONTROL-sheldon-lock-help-prints-reinstall`, `sheldon-lock-is-mutating`.

---

**Resolution (human, 2026-07-10) — YES: run the mutating `sheldon lock` in-guest and assert exit 0.**

The instinct behind this OQ — reach for the least-invasive probe — was the wrong instinct, and naming why
is the point of recording it. **The disposable clone exists precisely so that mutation is free.** `sheldon
lock` runs inside a tart clone that `08(d)` destroys moments later. Running the real installer tests
strictly *more* than a hypothetical read-only verb would, because installing the plugin sources **is** the
behaviour under test. A check that avoided the side effect would also have avoided the thing it checks.

My "best guess" above was *"drop the lock-file check entirely."* **That guess was wrong**, and wrong in an
instructive direction: it would have deleted a signal to preserve a purity the VM was already paying for.
The half I got right was the factual half — there is no non-mutating verb.

**Evidence added (all dry-run PASS).** The human asked for a `cli-help` on `sheldon lock --help` expecting
`--reinstall`. **That claim already existed**, merged, as `CONTROL-sheldon-lock-help-prints-reinstall`
(same `argv`, same `expect`) — so it was not re-proposed; duplicating it would be noise, and I am saying so
rather than quietly padding the count. What was genuinely missing is the *stronger* claim, now proposed:

- `sheldon-help-has-no-verify-subcommand` (`cli-help`, `must_fail`, `polarity: negative`) — sheldon 0.6.6
  exposes `init | add | edit | remove | lock | source | completions | version` and **no `verify` verb at
  all**, not merely no `--check` on `lock`. Paired with the positive control
  `CONTROL-sheldon-help-lists-lock-subcommand` (same `argv`, `expect: "lock"`), so *"no verify in the
  output"* cannot be satisfied by an empty `--help`. Mutation-tested: swapping the probe's pattern to one
  known present flips it to `FAIL` with `CONTROL PASSED — the oracle is broken`.
- If `sheldon` ever leaves `PATH`, both report `UNREACHABLE:` — never a silent pass, and never a
  refutation. That is the behaviour the human asked for, and it is `verify_claims.py`'s existing
  guarantee, not something I had to add.

**Marker retired.** `08`'s `<!-- UNVERIFIED: ... whether sheldon source lazily re-locks -->` is **deleted**,
because the question is moot: the harness does not run `sheldon source`. Per the honesty-budget rule, this
qualifies only because claims were *added* alongside it. The brief cited the marker at `08:174`; it was
actually at **`08:189`** (re-derived with `grep -n`) — the fourth false line number traced to the master
brief chain this run. See the backlog.

---

## OQ-18 · harness · ANSWERED · Should the golden image build on `-base` (which preinstalls mise) or `-vanilla` (cold start)?
**Status:** ANSWERED
**Renumbered from OQ-09 (🧪 harness)** — see the note in OQ-17. 🖥 utm's `OQ-09` keeps the number.
**Spec:** specs/macos-ci/08-dotfiles-test-harness.md:39-48
**Question:** 08 already names this as "recorded here as open, and deliberately not resolved" but it has never had an OQ number, so it is invisible in the one file the human reads. Filing it. `ghcr.io/cirruslabs/macos-*-base` preinstalls Homebrew, **mise**, rbenv and node@24. The claims ledger's own `base-image-preinstalls-mise` and `mise-installed-by-dotfiles-on-macos` are therefore in direct tension: the default `mise` lane never exercises its own install path from cold.
**What I tried:**
```
$ grep -n 'mise' /Users/bossjones/dev/cirruslabs/macos-image-templates/templates/base.pkr.hcl
(the ledger claim base-image-preinstalls-mise already passes against this file)
$ uv run tools/verify_claims.py            # mise-installed-by-dotfiles-on-macos: PASS
```
Both claims pass. Neither is wrong. They just describe two facts that make the default lane a weaker test than it reads as.
**Why it is stuck:** this is a cost/fidelity tradeoff, not a fact. `-vanilla` restores cold-start fidelity and re-adds the Homebrew + Xcode-CLT bootstrap cost that 08(a) spent a section arguing away. Only the human decides which they are buying.
**My best guess, explicitly labelled a guess:** build the golden image on `-vanilla`, install CLT + Homebrew + chezmoi + `retry` there, and deliberately do **not** install mise — that keeps the golden image's cost amortised while leaving the one path under test cold.
**Cost of guessing wrong:** on `-base`, `run_onchange_before_02-macos-install-mise.sh.tmpl` short-circuits on `command -v mise` and the harness reports green having never run `brew install mise`. A regression in the dotfiles' own mise bootstrap would be invisible to the suite whose entire purpose is to catch it.

**Resolution (human, 2026-07-10) — YES: build the golden image on `-vanilla`, and deliberately OMIT `mise`.**

The guess above was **upheld in full**, and the reasoning now lives in
[`08`](../specs/macos-ci/08-dotfiles-test-harness.md) rather than only here. The decisive point is that
this is not a fidelity preference — it is a **hole**:

> `-base` preinstalls `mise`. The dotfiles' installer short-circuits on `command -v mise`. So on `-base`,
> `run_onchange_before_02-macos-install-mise.sh.tmpl` **never runs**, and the suite reports **green having
> never executed `brew install mise`.** A regression in the dotfiles' own `mise` bootstrap would be
> **invisible to the suite whose entire purpose is to catch it.**

**Golden image: built once on `-vanilla`, carrying Xcode CLT + Homebrew + chezmoi + `retry`. Not `mise`.**
That amortises the expensive, stable bootstrap while leaving the one path under test **cold**.

**The two claims in tension both stay, because both are true.** `base-image-preinstalls-mise` and
`mise-installed-by-dotfiles-on-macos` are not a contradiction to resolve — they are the premises. `08` now
says the harness uses `-vanilla` **because** they are both true. What was missing is the third premise,
and it is the load-bearing one:

- `dotfiles-mise-script-short-circuits-on-existing-mise` (`file-line`, `:9`) — **new**. Without it, (1)+(2)
  merely look like redundancy. With it they compose into the hole above.
- `vanilla-image-preinstalls-no-software` / `base-image-is-derived-from-vanilla` (`file-line` on upstream's
  README `:8`, `:9`) — `-base` *is* `-vanilla` plus `brew`, so choosing `-vanilla` steps one rung down
  upstream's own line rather than forking off it.
- `vanilla-sequoia-template-installs-no-mise` (`absent`, `polarity: negative`) ↔
  `CONTROL-vanilla-sequoia-template-is-a-tart-cli-build` — *"no mise in the template"* would otherwise be
  satisfied by a wrong path returning an empty string. Mutation-tested: swapping the pattern to `tart-cli`
  (known present) flips it to `FAIL`.

**"Recorded here as open" is retired from `08`.** The brief cited that passage at `08:39-48`; `sed -n` puts
it at **`08:47-58`**. `12`'s `macos-versions.toml` now pins
`ghcr.io/cirruslabs/macos-{sequoia,tahoe}-vanilla:latest`.

---

## OQ-38 · harness · OPEN · A cross-file `file-line` pin has no owner, and rots whenever *anyone* edits the target above it.
**Status:** OPEN
**Spec:** .team/claims.jsonl — `oq02-vnc-marker-pinned-at-12-*`, `spec12-vnc-port-mention-is-at-*`
**Question:** `file-line` exists to kill hallucinated `file:line` citations, and it works — it caught the fabricated `12:607`. But it is **brittle against any edit above the pinned line**, so it renders two opposite findings identically: *"the citation rotted"* and *"the marker was deleted."* Is that trade acceptable, or must every `file-line` claim ship an edit-stable `file-contains` partner?
**What I tried:** I have now broken the same pin **twice in one run**, both times by making edits I was *instructed* to make.

```
# after the D2/D4 fix:
[FAIL] oq02-vnc-marker-pinned-at-12-340   line 340 is '`_gui_core.parse_vnc_url()` turns that line…'
# after the OQ-13/OQ-18 edits:
[FAIL] oq02-vnc-marker-pinned-at-12-359   line 359 is 'prefer the `pty` tier whenever…'
[FAIL] spec12-vnc-port-mention-is-at-349  line 349 is ''
```

`git diff` confirms **neither line's text ever changed.** The marker is byte-identical; it moved 340 → 359 → 364. Its edit-stable partner `oq02-vnc-marker-exists-regardless-of-line` (`file-contains`) **never failed once.**

The second failure is the worse one. `spec12-vnc-port-mention-is-at-349` sits in **🍎 tart-core's** `file` scope (`02-packer-tart-builder.md`) but pins a line in **🧪 harness's** `12-tooling-and-agent-loop.md`. **Neither agent owns both ends.** tart-core cannot know when harness edits 12; harness has no mandate to renumber tart-core's evidence. I proposed the re-pin anyway (`spec12-vnc-port-mention-is-at-354`) because leaving the gate red was worse — but that is one agent editing another's evidence, which `_RULES.md` §5 does not contemplate.

**Why it is stuck:** the fix is a policy choice with a real cost. Requiring a `file-contains` partner on every `file-line` claim roughly doubles those records and makes the ledger noisier. Not requiring it means the gate goes red for reasons that are not findings — and **a red gate that cries wolf gets suppressed**, the exact failure the human named in the OQ-37 reasoning. `tools/verify_claims.py` is 🔬 ledger's file alone.

**My best guess, explicitly labelled a guess:** require the pair only where the pinned line is an `<!-- UNVERIFIED -->` marker, or where the `target` lives outside the claim's own `file`. Those are the two cases where *moved* vs *deleted* changes what a reader should do. Elsewhere a bare `file-line` is fine: a rotted pin inside your own file is a defect you caused and can see.

**Cost of guessing wrong:** the next agent to add a paragraph to spec 12 turns the gate red, cannot tell whether a marker vanished or slid, and — under time pressure, one `expect` edit away from green — "fixes" the line number without checking whether the marker is still there. That is an honesty budget paid down with punctuation (OQ-05), one layer up.


---

<!-- 🔐 secrets: OQ-08 and OQ-09 were taken concurrently by tart-ci/ledger/harness and utm/harness.
     Per _RULES.md §6 ("if you race, renumber yours upward") mine are OQ-13 and OQ-14. -->

## OQ-13 · secrets · NEEDS-HUMAN · May `just check` take a network dependency on `raw.githubusercontent.com`?
**Status:** ANSWERED (human decision YES; implemented by 🔬 ledger)  
**Spec:** specs/macos-ci/13-build-secrets.md:104 (`use_env_var_file = false   # default; ... true writes a tempfile to the GUEST`)
**Question:** Spec 13's central safety property — that `use_env_var_file = true` writes the secret **into the guest** — is a statement about Packer's behaviour that no *local* evidence kind can reach. Should the ledger prove it by `curl`-ing Packer's own source pinned at tag `v1.15.4`, accepting that `just check` then fails without network egress to GitHub?
**What I tried:**
```
curl -sS -o /dev/null -w '%{http_code}' https://developer.hashicorp.com/packer/docs/provisioners/shell   -> 200
grep -qF 'Default: false'          shell.html  -> NO   (absent from the RAW HTML)
grep -qF 'This defaults to false'  shell.html  -> NO   (absent from the RAW HTML)
python3 (strip tags) -> "use_env_var_file (boolean) - If true, Packer will write your environment
                        variables to a tempfile and source them from that file ... Default: false ."
```
The prose **is** on the page, but only after stripping HTML tags — HashiCorp splits sentences across
`<code>`/`<span>` elements, so a substring `grep` of the raw HTML is **unsound**, and there is no
HashiCorp search-JSON index (the `doc-index`/`doc-contains` oracles cover only `tart` and `utm`).
Packer's pinned source *is* plain text and does answer it:
```
curl -sS -o /dev/null -w '%{http_code}' \
  https://raw.githubusercontent.com/hashicorp/packer/v1.15.4/provisioner/shell/provisioner.go   -> 200
grep -F 'comm.Upload(remoteVFName'  -> present   # the varfile is uploaded to the GUEST
grep -F '"rm -f %s", path'          -> present   # and cleaned up with an unlink, not a shred
```
**Why it is stuck:** three options, and the choice is a policy call, not an evidence call. (a) Accept the
network dependency — I have proposed `packer-shell-use-env-var-file-uploads-into-guest` and
`packer-shell-guest-cleanup-is-an-unlink` on this basis, and both dry-run PASS. (b) Teach
`tools/verify_claims.py` a `doc-http` kind that strips tags before matching: a tooling change only
🔬 ledger may make, and it *still* needs network. (c) Vendor the relevant source lines into
`tests/fixtures/` and claim against the local copy — offline and fast, but the copy silently rots away
from the real Packer, which is the exact failure this ledger exists to prevent.
**My best guess, explicitly labelled a guess:** (a), *because the URL is pinned to a tag* — that is the
whole difference between a citation and a moving target. `just check` already reaches the network for
`doc-index`, `doc-contains` and `just link-check`, so egress is an existing dependency, not a new one.
**Cost of guessing wrong:** if the human wants `just check` hermetic, two of my twelve proposals must be
withdrawn and 13's single most load-bearing sentence — *why `use_env_var_file` must stay `false`* — drops
back to `<!-- UNVERIFIED -->`.

**Resolution (🔬 ledger, human decision YES) — `http-contains` kind added; spec 13's central property is now executable.**
Grepping HashiCorp's rendered HTML is unsound (they split sentences across `<code>`/`<span>`), and there is no
HashiCorp search-JSON oracle. Packer's pinned source is plain text and answers it directly.
**Tag-pinned at `v1.15.4`, never `main`:**

```
https://raw.githubusercontent.com/hashicorp/packer/v1.15.4/provisioner/shell/provisioner.go   -> 200, 14,446 bytes
  :273  if err := comm.Upload(remoteVFName, r, nil); err != nil {      -> packer-shell-uploads-the-varfile-into-the-guest
  :401  Command: fmt.Sprintf("rm -f %s", path),                       -> packer-shell-cleans-the-varfile-with-an-unlink
```

The varfile is **uploaded into the guest** — which is why 13 mandates `use_env_var_file = false` — and it is
cleaned up with an **unlink, not a shred**, which is G15's whole point: `rm` drops the directory entry and
leaves the blocks, so the plaintext survives in `~/.tart/vms/<name>/` and `strings` still finds it.
Spec 13's central rule (never write the secret to the guest at all) is now proved by evidence a machine
re-executes, not by a docs page that never stated it.

A non-2xx yields `STRUCTURE:`, never a verdict on the sentence — verified: a 404 under `must_fail` is **not**
inverted into a pass. `just check` already needed network (lychee + the tart/utm oracles); this adds
`raw.githubusercontent.com`. Recording the new host in `12-tooling-and-agent-loop.md` is 🧪 harness's job;
noted in the backlog. **ANSWERED.**

---

## OQ-14 · secrets · OPEN · `cli-help`'s `env` overlay can SET a variable but never UNSET one. Are the "no-env" claims therefore at the mercy of the ambient shell?
**Status:** OPEN
**Spec:** tools/verify_claims.py:213 — `env = {**os.environ, **claim.get("env", {})}`
**Self-correction (🔐 secrets, before hand-off):** I first wrote `:211`. 🔬 ledger edited
`tools/verify_claims.py` while I was writing, and the line moved to **`:213`** (`sed -n '213p'` confirms;
`:211` is now `if isinstance(argv, str):`). **My own citation rotted inside a single run** — the exact
failure `file-line` exists to kill, committed by the agent complaining about it. Re-derived, not recalled.
Any line number in a *shared* file is a moving target unless a `file-line` claim pins it.
**Question:** The overlay is a dict merge, so a claim can *set* `PACKER_LOG=1` but can never *remove* a
variable the operator exported. Every claim that means "run this with no debug logging" is silently
environment-dependent. Should `cli-help` gain an `unset: [...]` list?
**What I tried:** measured with separate pipes, exactly as `subprocess.run(capture_output=True)` captures:
```
PACKER_LOG unset  -> stdout 136B, stderr   0B,  no '[INFO] Packer version:'
PACKER_LOG=""     -> stdout 136B, stderr   0B,  no '[INFO] Packer version:'
PACKER_LOG=0      -> stdout 136B, stderr   0B,  no '[INFO] Packer version:'
PACKER_LOG=1      -> stdout 136B, stderr 845B,     '[INFO] Packer version:' PRESENT
PACKER_LOG=off    -> stdout 136B, stderr 845B   # ANY other non-empty value ENABLES logging
```
(An earlier measurement of mine reported 136B of *stderr* with `PACKER_LOG` unset. That was my own
instrument lying: zsh MULTIOS turns `cmd 2>&1 >/dev/null | wc -c` into a count of **stdout**. Re-measured
with separate file redirections. This run's thesis, applied to me.)
**Why it is stuck:** `tools/verify_claims.py` is owned solely by 🔬 ledger; I may not edit it. A workaround
exists and I used it — pin `"env": {"PACKER_LOG": "0"}` on the negative probe
(`packer-debug-log-silent-when-overlay-disabled`) rather than omitting the key — but that is a per-claim
patch, not a property of the tool, and it only works for variables whose "off" state is *expressible as a
value*. It cannot express "this variable must be absent".
**My best guess, explicitly labelled a guess:** an `unset` list is about four lines
(`for k in claim.get("unset", []): env.pop(k, None)`) and would make the `packer-sensitive-hides-secret`
pair hermetic against a contaminated shell. I did not write it, because I do not own the file.
**Cost of guessing wrong:** an operator (or CI runner) with `PACKER_LOG=1` exported turns
`packer-sensitive-hides-secret` and `CONTROL-packer-inspect-prints-plain-literals` into debug-log runs.
Both still pass — masking really does hold under `PACKER_LOG=1` — so the failure is **invisible**: the
pair silently stops testing the no-debug-log case it was written to test, and the `-under-debug-log` pair
degenerates into a duplicate of it. A green check that means something subtly different from what it says.
**See also:** 🔬 ledger's OQ-08 (`packer inspect` never runs a provisioner, so no masking claim covers the
`packer build` path). That is the *other* half of this gap and I endorse it rather than duplicating it:
together they bound exactly how much of `sensitive = true` this ledger actually tests.

---

## OQ-15 · tart-core · BLOCKED-BY-SCOPE · Does `tart run --graphics` parse on tart 2.32.1, or does `headless = false` break the Packer build outright?
**Status:** BLOCKED-BY-SCOPE
**Spec:** specs/macos-ci/02-packer-tart-builder.md:135
**Question:** `packer-plugin-tart` v1.21.0 appends `--graphics` to `tart run` whenever `headless = false`. tart 2.32.1's `tart run --help` advertises `--no-graphics` and no `--graphics` option at all. Does tart's parser accept `--graphics` anyway?
**What I tried:**
```
sed -n '38,44p' .../packer-plugin-tart/builder/tart/step_run.go
    if config.Headless { runArgs = append(runArgs, "--no-graphics")
    } else {             runArgs = append(runArgs, "--graphics") }
git -C .../packer-plugin-tart describe --tags        -> v1.21.0
tart run --help | grep -E '^\s+--graphics'           -> (no match)
tart run --help | grep -c -- '--graphics'            -> 0
tart --version                                       -> 2.32.1
```
**Why it is stuck:** the only way to settle it is to invoke `tart run --graphics <vm>` and observe whether the argument parser rejects the flag before it reaches VM lookup. This run forbids `tart run` and forbids `packer build`, which is the only path that would exercise it. A `cli-help` probe cannot help: there is no `--help` output in which the flag appears.
**My best guess, explicitly labelled a guess:** tart's CLI is Swift ArgumentParser; a `@Flag(inversion: .prefixedNo)` declaration generates both `--graphics` and `--no-graphics` while `--help` renders only one member of the pair. So `--graphics` probably parses and the plugin probably works. **This is a guess about a library convention, not an observation.**
**Cost of guessing wrong:** if `--graphics` is rejected, then *every* `packer build` with `headless = false` fails at "Starting the virtual machine…" with an argument-parse error, and the documented advice to "disable `headless` when debugging `boot_command`" is advice that breaks the build precisely when someone is already debugging. The harness's own default (`headless = true`) never touches this path, so the bug would lie dormant until the first person tried to watch a build.
**Mitigation already applied:** 02 keeps `headless = true` and carries an `<!-- UNVERIFIED -->` marker naming this OQ.

---

## OQ-16 · tart-core · NEEDS-HUMAN · The `pre_tool_use` / `post_tool_use` hooks write the text of every command into `logs/*.json` under the CWD. Does that poison this run's own greps?
**Status:** ANSWERED (human decision YES; implemented by 🔬 ledger)  
**Spec:** (meta — verification infrastructure)
**Question:** A repo-wide `grep -rn '<string>'` run by an agent will match the hook's *own log of the agent typing that string*. Is any existing or proposed claim relying on such a grep, and should `logs/` be excluded repo-wide?
**What I tried:** while refuting G13 I ran, inside the `packer-plugin-tart` clone:
```
grep -rni 'vnc_port' .            -> 6 hits, ALL of them in ./logs/pre_tool_use.json
                                      and ./logs/post_tool_use.json — i.e. the hook's record of
                                      the three earlier commands in which *I* typed "vnc_port".
grep -rni 'vnc_port' . --exclude-dir=.git --exclude-dir=logs
                                  -> ZERO hits (the true answer)
```
The same artefact exists in this repo: `specs/macos-ci/logs/pre_tool_use.json` matched a `grep -rn 'vnc_port' specs/`, which is why `specs/**/*.md` must be scoped with `--include='*.md'` — as `Justfile:63` already does for `unverified-count`.
**Why it is stuck:** whether to exclude `logs/` (a `tools/` or `Justfile` change) is not mine to make — 🔬 ledger owns `tools/verify_claims.py`, 👑 lead owns the `Justfile`, and the hook itself is the human's. I can only report the hazard.
**Why it is not currently a live bug:** the `absent` evidence kind takes a **single file** target, never a directory, so no existing claim can be poisoned this way. The hazard is to *agents reasoning by grep*, which is exactly what "default to refuted" asks them to do. **A verifier that greps a tree the verifier is being logged into can confirm any string it searches for.**
**My best guess, explicitly labelled a guess:** harmless today, because `absent` is file-scoped and `unverified-count` is `--include='*.md'`-scoped. But it is one directory-valued `absent` target away from a claim that passes because an agent once typed the string it is asserting is missing.
**Cost of guessing wrong:** a self-confirming negative claim — the precise failure mode `must_fail`'s positive controls exist to prevent, arriving through a channel none of those controls watch.

**Resolution (🔬 ledger, human decision YES) — `logs/` evidence targets are now refused by the tool.**
`check_structure()` rejects any `file-contains` / `absent` / `file-line` whose `target` has a `logs` path
component. Exit **4** (USAGE). Verified adversarially: an `absent` claim over
`.../packer-plugin-tart/logs/out.txt` exits 4 with *"Logs are agent-writable; evidence must not be."*

Not a live bug today — 🍎 tart-core was right about the shape, and the orchestrator confirmed the concrete
instance: **this run's own `pre_tool_use` hook wrote `ghp_FIXTURE_SENTINEL` into a third-party clone**, in the
run whose thesis is *never write a secret to a filesystem you do not control*. Those `logs/` dirs were
quarantined (moved, not deleted). Re-verified read-only: `0` files under `dev/cirruslabs` contain the sentinel,
and `grep -rIn vnc_port packer-plugin-tart --exclude-dir=.git` returns **zero** hits — so `02:172-177` is
upheld with no `--exclude-dir=logs` needed.

Same principle as GB4: *a rule the tool does not enforce is a rule that will be forgotten.* We were one
directory-valued `absent` target away from a claim that passes because an agent once typed the string it
asserts is missing. **ANSWERED.**

---

## OQ-24 · ledger · OPEN · Does Packer's shell provisioner really default `use_env_var_file` to `false`, or is that an inference nobody has sourced?
> _(Renumbered OQ-09 → OQ-24 by 🔬 ledger: 🖥 utm had already taken OQ-09. `_RULES.md` §6: the racer renumbers upward.)_
**Status:** OPEN
**Spec:** specs/macos-ci/11-sources.md:150 (and the design it underwrites, specs/macos-ci/13-build-secrets.md)
**What I tried:**
```
curl -fsSL https://developer.hashicorp.com/packer/docs/provisioners/shell   # 318,342 bytes, HTTP 200
# strip tags, search every occurrence:
skip_clean         -> "This defaults to false (clean scripts from the system)."          <- stated
expect_disconnect  -> "Defaults to false."                                                <- stated
use_env_var_file   -> "If true, Packer will write your environment variables to a tempfile
                       and source them from that file, rather than declaring them inline"
                   -> "unless the user has set \"use_env_var_file\": true -- in that case,
                       the default execute_command is chmod +x {{.Path}}; . {{.EnvVarFile}} && {{.Path}}"
# NO sentence anywhere on the page states use_env_var_file's default.
```
The page demonstrably *does* state defaults when it means to (`skip_clean`, `expect_disconnect`). For
`use_env_var_file` it does not. 11-sources.md:150 lists it as one of "the two defaults the whole design
rests on", which presents inference as citation.

**Why it is stuck:** it cannot be expressed as a ledger claim. `tools/verify_claims.py`'s `DOC_INDEXES`
covers `tart` and `utm` only; `developer.hashicorp.com` ships no static search JSON (11-sources.md:37-41
documents why, and rejects the Algolia route). So there is no `doc-contains` oracle that could pin the
sentence — and there is no sentence to pin. Settling it *affirmatively* would need `packer build` with the
field omitted, observing whether a tempfile appears in the guest. `packer build` is FORBIDDEN by SCOPE.

**My best guess, explicitly labelled a guess:** the default is `false`. The page's `execute_command`
prose branches on "unless the user has set `use_env_var_file: true`", which only parses if the unset
state is `false`, and Go's `bool` zero value is `false`.

**Cost of guessing wrong:** bounded, and this is the important part. `13-build-secrets.md` sets
`use_env_var_file = false` **explicitly**, so the guarantee does not depend on the default at all. The
exposure is purely documentary: `11-sources.md` claims the docs told us something they never said, and a
future reader who *omits* the field while trusting that row would silently get a tempfile containing the
token written into the guest — where G15 says `rm` will not erase it. The remedy is to reword 11, not to
change the design.

---

## OQ-25 · ledger · OPEN · What does "47/47 URLs return 200" in `11-sources.md` count, and can it be re-derived?
> _(Renumbered OQ-10 → OQ-25 by 🔬 ledger: 🖥 utm had already taken OQ-10. `_RULES.md` §6: the racer renumbers upward.)_
**Status:** OPEN
**Spec:** specs/macos-ci/11-sources.md:13 and :178
**What I tried:**
```
grep -ohE '\]\(https?://[^)]+\)' specs/macos-ci/11-sources.md | sort -u | wc -l   -> 70   (markdown links)
grep -ohE 'https?://[^ )>"`|]+'  specs/macos-ci/11-sources.md | sort -u | wc -l   -> 73   (incl. bare)
just link-check                                                                   -> green (lychee, fragments on)
```
**Why it is stuck:** ":178 says "the 47 URLs actually **supplied for this research**" — i.e. the URL list
handed to the *previous* run, which is not on disk. So 47 is a historical count of an artefact this repo
does not contain, and no read-only command in this tree can confirm or refute it. But `:13` reads as a
live invariant about *this file* ("Every source URL in this research is live … 47/47 return `200`"), and
that reading is false today: the file carries 70 distinct linked URLs. Two readings, one number, no oracle.

**My best guess, explicitly labelled a guess:** 47 was accurate for the research run's supplied list and
has simply been overtaken as later passes added citations. It is stale, not fabricated.

**Cost of guessing wrong:** low in substance, high in trust. A frozen count that no command reproduces is
the same species as a hallucinated `file:line`: a number a reader will believe and cannot check. And it is
*already redundant* — `just link-check` proves the stronger property (every link, fragments included, is
live) over all 70, mechanically, on every run. Recommendation to 📚 synth: delete the count, cite the gate.

---

## OQ-26 · ledger · NEEDS-HUMAN · Should `verify_claims.py` gain an `http-status` evidence kind, so the two G19-class URLs can be claims instead of prose?
> _(Renumbered OQ-11 → OQ-26 by 🔬 ledger: 🖥 utm had already taken OQ-11. `_RULES.md` §6: the racer renumbers upward.)_
**Status:** ANSWERED (human decision YES; implemented by 🔬 ledger)  
**Spec:** tools/verify_claims.py (evidence kinds); specs/macos-ci/02-packer-tart-builder.md; specs/macos-ci/11-sources.md:32,82,83
**Question:** Two categories of load-bearing URL are **structurally unrepresentable** in the ledger today,
and both are exactly the kind that "default to refuted" will destroy:

1. `developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart` — the
   canonical field reference underpinning **all of spec 02**. Absent from the sitemap (0 of 337), returns
   **200**. This is G19, and it is *the single most load-bearing citation in the repo that has no claim.*
2. `tart.run/blog/2025/10/27/press-release-...-fair-source-license/` — the **sole** source for G4's
   "enforcement is not theoretical", the highest-risk human-sign-off item here. Absent from tart's search
   index (which contains zero `/blog/YYYY/MM/DD/` posts), returns **200**. A second G19, found this run.

**What I tried:**
```
curl -sS -o /dev/null -w '%{http_code}' <both URLs>   -> 200, 200
```
Neither can be a `doc-index` claim: for (1) there is no HashiCorp oracle at all; for (2) the tart oracle
does not cover the `/blog/<post>` prefix, so a `doc-index` claim would **FAIL and look like a fabrication**.
Both therefore live only as prose — protected by a carve-out in the brief that a future agent must
*remember to obey*. That is exactly the "verifier nobody verifies" shape.

**Why it is stuck — and why it is NEEDS-HUMAN, not a thing I should just do:** adding an `http-status`
kind is a ~10-line change to a file I own, and it would let `02`'s field reference and `04`'s enforcement
evidence become real, re-executable claims. But it changes what `just check` *is*: today the tool GETs two
static JSON indexes; an `http-status` kind makes the gate issue arbitrary HTTP requests to arbitrary hosts
named in the ledger, and makes `just check` fail when any cited site has an outage. That is a real
trade — network-coupled truth gate vs. an unclaimable citation — and my brief says to extend the tool only
if a new evidence **kind** is genuinely needed and to justify it first. **I am justifying it and stopping.**

**My best guess, explicitly labelled a guess:** worth it, gated. Add `http-status` with an allowlist of
hosts, treat any non-2xx/non-3xx **transport** failure as `UNREACHABLE:` (never invertible by `must_fail`,
same rule as the file-missing fix I landed this run), and assert only on the status code. That keeps a
site outage from being read as a fabricated URL — which is the failure mode the kind exists to prevent.

**Cost of guessing wrong:** if we add it carelessly, `just check` becomes flaky and the team learns to
ignore a red gate — strictly worse than no claim. If we never add it, the two highest-risk citations in
the repo stay defended by a paragraph of prose telling future agents *not* to apply the oracle rule, and
G10-in-reverse remains one obedient agent away. I would rather the human chose which risk to hold.

**Resolution (🔬 ledger, human decision YES) — `http-status` kind added; both G19-class URLs are now claims.**
Neither URL can be a `doc-index` claim: such a claim would FAIL and **look like a fabrication**.

| URL | evidence |
|---|---|
| `developer.hashicorp.com/packer/integrations/.../builder/tart` (underpins all of spec 02; 0 of 337 sitemap entries) | `g19-tart-builder-integrations-page-returns-200` — **upgraded** from a `cli-help` shell-out to `curl` |
| `tart.run/blog/2025/10/27/press-release-...` (the SOLE source for G4's enforcement claim; zero `/blog/YYYY/MM/DD/` posts in the index) | `g4-enforcement-press-release-returns-200` (new) |

**A 200 proves the page EXISTS, never that it SAYS anything.** So the press release also carries
`tart-2025-enforcement-press-release-is-live`, **upgraded** to the new `http-contains` kind: existence and
content are different propositions and now have different claims. Upgrading rather than adding avoided
creating the duplicate-evidence groups I had just finished deleting.

`http-status`/`http-contains` hosts are an explicit **allowlist** (`developer.hashicorp.com`, `tart.run`,
`raw.githubusercontent.com`, `cirruslabs.org`). A typo'd host is a loud structural rejection (exit 4), never
a silent `UNREACHABLE:` that `must_fail` might invert — verified adversarially. **ANSWERED.**

---

## OQ-19 · harness (cross-audit of 🏭 tart-ci) · NEEDS-HUMAN · A `must_fail` `doc-contains` aimed at a *zero-text indexed page* passes SILENTLY. The `STRUCTURE:` guard does not catch it.
**Status:** ANSWERED (closed by 🔬 ledger, GB5 — enforced structurally in tools/verify_claims.py)  
**Spec:** tools/verify_claims.py:242-247 (🔬 ledger owns the file); surfaced auditing `04-tart-licensing-risk.md:94-99`
**Question:** `tools/verify_claims.py` models two ways a `doc-contains` claim can fail without being evidence: `UNREACHABLE:` (network/binary) and `STRUCTURE:` (the page is absent from the index). Neither is inverted by `must_fail`. **There is a third state nobody modelled: the page is *in* the index and its indexed text is empty.** In that state the check falls through to the ordinary "sentence not found" branch — so `must_fail` inverts it, and the control goes **green**.
**What I tried:** `tart.run`'s index has 20 distinct pages, **six of which carry no body text at all** — `/blog`, `/blog/archive/{2023,2024,2025}`, `/blog/category/{announcement,orchard}`. Their indexed text is just the title (`'Blog'`, `'2023'`, …). Two probes, run from the repo root:

```
$ uv run tools/verify_claims.py <scratch>/mf.jsonl
[PASS] MUTANT-CONTROL-on-empty-page    (doc-contains)          # page=/blog/  expect="literally anything at all"
[FAIL] MUTANT-CONTROL-on-missing-page  (doc-contains)
         STRUCTURE: page '/no/such/page' is not in the tart index — fabricated or moved
```

A `must_fail` control asserting that `/blog/` does not contain **"literally anything at all"** *passes*. It would pass for every string ever written. And the non-`must_fail` diagnostic is actively misleading:

```
[FAIL] C-doc-contains-against-blog-shell  (doc-contains)
         page /blog exists but does not contain 'Fair Source 100' — upstream may have reworded; re-read it
```

*"Upstream may have reworded"* is the one message that tells an auditor the URL is fine and only the wording moved. The page never had text.

**Why it is stuck:** the fix is a third guard in `evaluate()` — something like `if not index_cache[site][page].strip(): return Result(..., f"STRUCTURE: page {page!r} is indexed but carries no body text")` — and `tools/verify_claims.py` is owned **solely by 🔬 ledger**. It is also a change to the verifier itself, which the master brief says to extend "only if a new evidence KIND is genuinely needed". This is not a new kind; it is a missing guard on an existing one. A human should say whether that is in scope for this run.

**Blast radius, checked, not assumed.** The four live `doc-contains` controls are safe **today** — their pages are text-rich (`/integrations/cirrus-cli` 2378 chars, `/licensing` 5225, `/quick-start` 10863). So nothing is currently green-for-the-wrong-reason. The hazard is that the guard which is supposed to make that impossible does not exist, and the page-text length of an upstream site is not something this repo controls.

**My best guess, explicitly labelled a guess:** MkDocs Material emits a zero-text index entry for every *generated* page (blog index, archives, category listings). `docs.getutm.app` (Just the Docs) probably has the analogous shape for its own generated pages, so the same hole likely exists on the `utm` site — I did not check, and I am labelling that a guess rather than checking it, because the fix is the same either way.

**Cost of guessing wrong:** exactly the failure the `must_fail` mechanism exists to prevent, one level up. `_RULES.md` §5 says *"a verifier nobody verifies is just a second thing to trust."* A control that passes because its page has no text is a verifier that verifies nothing, and it reports `PASS`. If upstream ever restructures a cited page into a stub — precisely what happened to `settings-apple/devices/` in the G10 story, from the other direction — the guarding control silently starts approving.

**Related:** 🏭 tart-ci's `OQ-08` correctly identifies that `tart.run/blog/**` is a G19-class carve-out (posts return HTTP 200, absent from the index). This is the *other half* of that observation: the blog is not merely absent, it is **half-present**, and the half that is present is the dangerous half.

**Resolution (partial) — 🏭 tart-ci, cross-audit reply. Status stays NEEDS-HUMAN; the missing guard is real and only 🔬 ledger can add it.** Harness is right, and I confirmed its blast-radius check by *mutation-testing my own two `must_fail` controls* rather than trusting that their pages are text-rich. A control that cannot fail is not a control:

```
[PASS] MUT-A  CONTROL-licensing-page-never-says-commercial-use-free, as shipped        (sentence absent -> inverts -> PASS)
[FAIL] MUT-B  same control, expect= a sentence the page DOES contain                   ("CONTROL PASSED — the oracle is broken")
[PASS] MUT-C  CONTROL-tart-blog-is-outside-doc-index-domain, as shipped                (path absent -> inverts -> PASS)
[FAIL] MUT-D  same control, expect="/licensing/" which IS indexed                      ("CONTROL PASSED — the oracle is broken")
[PASS] MUT-E  /licensing/ contains "Fair Source License"                               (proves the page is NOT zero-text)
```

Both controls **flip to FAIL when the string they assert is absent is actually present**, so neither is vacuous, and MUT-E independently closes the zero-text hazard for `/licensing/`. Note `CONTROL-tart-blog-is-outside-doc-index-domain` is `doc-index`, not `doc-contains`, so the OQ-19 hole cannot reach it at all: `doc-index` tests path membership and never reads body text. **The hole is real; it does not currently touch tart-ci's claims. That is a fact I established by trying to break them, not by noting that their pages happen to be long.**

**Resolution (🔬 ledger, GB5) — CLOSED by structural enforcement, not by argument.** 👑 lead identified
GB5 and OQ-19 as the same defect, and they are. My GB4 fix exempted the `doc-contains` *kind* from the
positive-control requirement, justified as *"they ARE the controls and have no partner by construction"*.
That is true of the seven `CONTROL-*` oracle records and **false of the one negative probe**:
`utm-no-tso-toggle-on-apple-virtualization` (`doc-contains`, `must_fail`, `expect: "TSO"`). Its own claim
prose named `CONTROL-utm-apple-virtualization-page-has-toggles` as its partner — **and nothing enforced it.**
Break or delete that control and the gate stayed green at `243/243` while the probe went silently vacuous,
because a page with **zero indexed text** satisfies "the page does not say TSO" exactly as well as an honest
page does. That is the failure this OQ describes, and the one GB4 was raised to eliminate.

`tools/verify_claims.py`'s `needs_control()` now exempts the **oracle record**, not the kind:
a claim needs a `control` if `kind == "absent"`, or if it is `must_fail` and of kind `cli-help` /
`doc-contains` / `doc-index` — **unless** it is a `CONTROL-*` record of a doc kind. The exemption is
deliberately *not* a bare `CONTROL-` name check: two genuine negatives are named `CONTROL-*` by history
(`CONTROL-d1-packer-dir-does-not-exist`, `CONTROL-tart-builder-clone-step-ignores-disk-format`), and a name
is not a warrant. `must_fail` `doc-index` probes are covered too — today every such record is an oracle, so
it is moot, but the predicate is right for the next one.

`utm-no-tso-toggle-on-apple-virtualization` now carries
`"control": "CONTROL-utm-apple-virtualization-page-has-toggles"`. Verified adversarially: an unpaired
`must_fail` `doc-contains` probe exits `4`; a `CONTROL-*` doc oracle with no control field still exits `0`.
`just check` → exit `0`, `243/243`. **Status flipped OPEN → ANSWERED; the human decision it requested is
no longer needed, because the tool now refuses the shape.** The residual `STRUCTURE:` gap OQ-19 names is
unchanged and still correct: `STRUCTURE:` distinguishes *page gone* from *sentence gone*; it was never a
guard against *page empty*. The control is.

---

## OQ-20 · tart-ci · ANSWERED · Tart's code now belongs to OpenAI while tart.run still sells Cirrus Labs licences. Who is the counterparty this repo is accepting risk against?
<!-- renumbered OQ-09 -> OQ-20 by 🏭 tart-ci: 09/10/11 were taken concurrently by 🖥 utm and 🔬 ledger. Per _RULES.md §6, the racer renumbers upward. My OQ-08 (line 144) predates ledger's OQ-08 (line 290) in this append-only file and is retained; that collision is the lead's to adjudicate. -->
**Status:** ANSWERED
**Spec:** specs/macos-ci/04-tart-licensing-risk.md — §4b
**Question:** `04` requires human sign-off (**G4**) on a commercial-licensing exposure. The tier *numbers* did not move — all four rows re-verified today and every one now carries a ledger claim. But the **party** did.
**What I tried:** (all read-only, all reproducible)
```
curl -fsSL https://api.github.com/repos/cirruslabs/tart             -> "full_name": "openai/tart"   (6,061 stars, created 2022-02-01)
curl -fsSL https://api.github.com/repos/cirruslabs/tart-guest-agent -> "full_name": "openai/tart-guest-agent"
curl -fsSL https://raw.githubusercontent.com/openai/tart/main/LICENSE
  -> "Functional Source License, Version 1.1, ALv2 Future License"  /  "FSL-1.1-ALv2"
  -> "Copyright 2022-2026 OpenAI"
  -> "the Apache License, Version 2.0 that is effective on the second anniversary of"
  -> grep -ic 'cpu\|core'  =>  0        # the FSL text never mentions CPU cores
curl -fsSL https://tart.run/licensing/  -> still "Fair Source License", still 100-core Free Tier,
                                           still licensing@cirruslabs.org  (2 occurrences)
```
**Why it is stuck:** Nothing here is *contradictory*, which is exactly why it needs a human. FSL sits under the Fair Source umbrella, and the 100-core Free Tier is a **tier grant published on tart.run**, not a clause of the FSL text (0 core mentions). So both sources can be true at once. What no read-only command can settle is **who would enforce**: §3's precedent is a *Cirrus Labs* action taken under a *Cirrus Labs* licence, and the copyright notice now reads *OpenAI*. Settling it means asking `licensing@cirruslabs.org` — sending mail to a third party, which is outside this run's scope and not an agent's call.
**My best guess, explicitly labelled a guess:** Cirrus Labs retains the trademark, the licensing business and the `tart.run` tier grants; the GitHub org move reflects an acquisition or an employment transfer of the maintainer, and `licensing@cirruslabs.org` remains the correct contact. **I did not verify any of that** — no press release, acquisition notice, or `openai/tart` README statement was located, and I did not search for one beyond the two API calls above.
**Cost of guessing wrong:** Asymmetric, and that is the point. Guessing *right* buys nothing — §4's posture (2–3 hosts, <100 combined cores, never build a competing product) keeps this repo inside the Free Tier under **either** reading, and `FSL-1.1-ALv2`'s second-anniversary Apache-2.0 conversion *reduces* long-run exposure. Guessing *wrong* means the human signed off on **G4** believing the counterparty, the enforcement precedent, and the escalation contact all belong to one company, when the code's copyright holder is now a different and vastly better-resourced one. **A licence-cost decision is the human's; so is a licence-counterparty decision.**

---

**Resolution (👑 lead relayed the human's decision; 🏭 tart-ci re-verified every probe read-only before accepting it). Status: ANSWERED.**

**The counterparty is OpenAI, and this was settled by EVIDENCE, not by fiat.** Re-derived independently, not inherited from the briefing:

```
curl -sS -o /dev/null -w '%{http_code}' https://cirruslabs.org/          -> 200
curl -fsSL https://cirruslabs.org/   (tags stripped)
  -> "Cirrus Labs to join OpenAI"   "Official announcement April 7th, 2026"   "Fedor Korotkov @fedor"
curl -fsSL https://api.github.com/repos/cirruslabs/tart  -> "full_name": "openai/tart"
curl -fsSL https://raw.githubusercontent.com/openai/tart/main/LICENSE
  -> "Functional Source License, Version 1.1, ALv2 Future License"  /  "Copyright 2022-2026 OpenAI"
  -> grep -ic 'cpu|core'  =>  0
curl -fsSL https://tart.run/licensing/ | grep -c 'OpenAI'  ->  0        # the tier page is STALE
```

**Two corrections to the briefing that handed me these probes, found by running them rather than pasting them:**

1. `api.github.com/repos/cirruslabs/tart` returns **`301`**, not `200`, without `-L` (it redirects to `/repositories/454359710`). The briefing's `curl -fsSL` worked only because `-f -L` follows. **A bare `http-status` claim on that URL asserting `200` would have been false.** I did not propose one; the acquisition is carried by `cirruslabs.org` and the `LICENSE` instead.
2. The briefing described the announcement as *"by Fedor Korotkov (@fedor), **founder**"*. The word **`founder` does not appear on the page**, in rendered text or raw HTML. The page says he *started* Cirrus Labs in 2017. I did not quote the noun.

**Which half of my guess was wrong — recording this is the entire point.** My OQ-20 guess was: *"Cirrus Labs retains the trademark, the licensing business and the tart.run tier grants; the GitHub org move reflects an acquisition or an employment transfer of the maintainer, and `licensing@cirruslabs.org` remains the correct contact."*

| Half | Verdict |
|---|---|
| "an acquisition … of the maintainer" | ✅ **CONFIRMED** — announced 2026-04-07 |
| "`licensing@cirruslabs.org` remains the correct contact" | ❌ **NOT ESTABLISHED. Retracted; must not be asserted.** |

The contact half was never evidence — it was an inference drawn from the page's **staleness**, and a stale page is exactly as consistent with *"nobody updated it"* as with *"it is still correct."* Reading a page's silence as a page's assertion is the same error class as `04:36`'s fabricated quotation, one level up. The address is still **printed**; that it is still **answered by the party who can grant a licence** is unverified and now carries an `<!-- UNVERIFIED -->` marker at `04:186` citing this OQ.

**Tier numbers re-verified: UNCHANGED.** G4's dollar figures survive the acquisition. The 100-core Free Tier is a grant published on `tart.run`, **not** a clause of the FSL text (0 core mentions) — both instruments are true at once and `04` §4b no longer collapses them. The repo posture (2–3 hosts, <100 combined cores, never build a competing product) keeps us in the Free Tier **under either reading**, and FSL's second-anniversary Apache-2.0 conversion *reduces* long-run exposure. **G4 is signed off as an accepted, documented risk.**

**What remains open is narrower than the original question, and is what the marker names:** who enforces post-acquisition, and whether `licensing@cirruslabs.org` is still the right escalation contact. Settling it means corresponding with a third party. This OQ is ANSWERED on the counterparty; the enforcement contact is deliberately left unguessed.

Ledger claims (8 proposed, all dry-run PASS): `cirruslabs-org-is-live` (`http-status`) · `cirruslabs-org-announces-openai-acquisition` · `cirruslabs-org-announcement-dated-april-7-2026` · `openai-tart-license-copyright-notice-via-http` · `fsl-text-mentions-no-cpu-cores` · `tart-licensing-page-never-mentions-openai` (`must_fail`, `polarity=negative`) · `tart-licensing-page-still-says-free-tier` (its positive control, same URL) · `tart-licensing-page-still-lists-cirruslabs-contact`.


## OQ-21 · tart-ci · What transport does `cirrus run` use to copy the working directory into a Tart VM?
<!-- renumbered OQ-10 -> OQ-21 by 🏭 tart-ci (race with 🖥 utm / 🔬 ledger). -->
**Status:** OPEN
**Spec:** specs/macos-ci/03-tart-ci-and-orchard.md:53 (the `<!-- UNVERIFIED -->` marker this OQ backs)
**What I tried:**
```
# the docs page says THAT it copies, never HOW:
tart index /integrations/cirrus-cli  ->  "will copy over working directory"   FOUND
                                     ->  "rsync"                              ABSENT
                                     ->  "--dir"                              ABSENT
curl -fsSL https://tart.run/integrations/cirrus-cli/  ->  rsync/--dir/mounts/uploads all ABSENT

# the installed binary settles copy-vs-mount, but not the transport:
cirrus run --help
  --dirty   if set the project directory will be mounted in read-write mode, otherwise the project
            directory files are copied, taking .gitignore into account
```
**Why it is stuck:** `--help` proves the **semantics** (default copies; `--dirty` mounts read-write; `.gitignore` is honoured) and I have ledgered that (`cirrus-run-dirty-copies-unless-mounted`). It does not name the **mechanism**. Settling that needs either the `cirrus-cli` source (not cloned locally; `03` links the repo but this run reads only local clones) or observing a running VM, which scope forbids. The marker therefore stays, narrowed from "rsync vs `--dir`" to "transport unknown".
**My best guess, explicitly labelled a guess:** neither of the two the marker offered. `--dirty`'s wording ("mounted in read-write mode") hints the *default* is a **read-only mount or an in-guest copy**, plausibly implemented over tart's `--dir` and then copied inside the guest — but I have read no source that says so, and the marker's original either/or may simply be a false dichotomy.
**Cost of guessing wrong:** Low for correctness, real for the harness. The **verified** half is the part that bites: `.gitignore` is honoured, so **a gitignored file never reaches the VM**. A dotfiles harness that stages fixtures or a generated `.chezmoi.yaml` into an ignored path would silently test an empty directory and pass. That consequence stands on `cirrus run --help` and needs no guess.

---

## OQ-22 · tart-ci · Can a Cirrus **persistent worker** run a custom (non-Cirrus-managed) Tart image under hosted Cirrus CI?
<!-- renumbered OQ-11 -> OQ-22 by 🏭 tart-ci (race with 🖥 utm / 🔬 ledger). -->
**Status:** OPEN
**Spec:** specs/macos-ci/03-tart-ci-and-orchard.md:144 (the `<!-- UNVERIFIED -->` marker this OQ backs)
**What I tried:**
```
cirrus --help              ->  worker    Persistent worker mode
cirrus worker --help       ->  pause | resume | run
cirrus worker run --help   ->  --token string   pool registration token
                           ->  --name string    worker name to use when registering in the pool
tart search index, whole corpus:  "persistent worker"   ABSENT
                                  "self-hosted"          FOUND — but only under integrations/gitlab-runner/
curl -fsSL https://tart.run/integrations/cirrus-cli/ -> "Cirrus CI only allows images managed and
                                                         regularly updated by us"   FOUND
```
**Why it is stuck:** The marker's *inherited reason* — "no source page describes self-hosted Cirrus CI runner registration" — is **false**, and I have retracted it in `03`: `cirrus worker run --help` is a source, it is installed, and it describes pool registration exactly. What remains genuinely unknown is whether the "only Cirrus-managed images" restriction is **lifted** for a persistent worker, since the worker runs on hardware we own. No tart.run page mentions Cirrus CI persistent workers at all, and cirrus-ci.org is outside every oracle this run trusts. Settling it needs the Cirrus CI docs or an actual pool registration — a network write and an account, both out of scope.
**My best guess, explicitly labelled a guess:** yes — the image restriction almost certainly exists because Cirrus's *own* macOS cloud hosts must run images Cirrus can vouch for, and that rationale evaporates on hardware the user owns. **This is a guess about a vendor's policy, and I found no sentence asserting it.**
**Cost of guessing wrong:** If persistent workers **cannot** use a custom image, `03`'s entire "how this repo would eventually use it" story loses its automated-CI leg: the golden image built in `02` could then only ever be driven by `cirrus run` on a developer's own Mac, never by a hosted pipeline, and the repo would need a different CI system (GitHub Actions self-hosted runner, GitLab Runner via `gitlab-tart-executor` — which *is* documented on tart.run). Inverting this guess changes which CI system the repo adopts, so it should be settled before `08`/`12` commit to one.

---

## OQ-27 · utm · `absent` claims carry NO control requirement. Should they?
**Status:** ANSWERED (diagnosis) · remediation = GATE-BLOCKER 4
**Spec:** `.team/claims.jsonl:8` (`no-macos-asdf-installer`); rule in `.team/dispatch/_RULES.md` §5
**What I tried:** `_RULES.md` §5 mandates a positive control only for a **negative `must_fail` probe over a `cli-help` command** — *"no secret in the output" is equally satisfied by no output at all.* The identical hazard exists for `absent`, and nothing guards it. Worked example, executed:

```
$ uv run tools/verify_claims.py <fixture>
[PASS] AS-MERGED-02-prefix        # absent("02-macos-install-asdf") in .chezmoiignore.tmpl
[FAIL] WITHOUT-02-PREFIX          # absent("macos-install-asdf")  -> line 8 matches!
         .chezmoiignore.tmpl unexpectedly contains 'macos-install-asdf'
```

`.chezmoiignore.tmpl:8` is `.chezmoiscripts/run_onchange_after_50-macos-install-asdf-plugins.sh`, which **contains the substring `macos-install-asdf`**. The merged claim survives only because of its `02-` prefix, and nothing in the claim says so. Worse, the claim's prose reads *"there is no macOS asdf installer script to ignore, **because none exists**"* — but it probes the **ignore list**, not `.chezmoiscripts/`. It would pass unchanged if someone added `02-macos-install-asdf.sh` and forgot to ignore it.
**Why it is stuck:** the remedy is a rule change plus possibly a new evidence kind (a `dir-lacks` / `glob` probe), and `tools/verify_claims.py` and `_RULES.md` are 🔬 ledger's and 👑 lead's respectively. I proposed the sound replacement instead — `xaudit-09-no-macos-asdf-installer-script-on-disk` (a `must_fail` `cli-help` over `ls .chezmoiscripts/`) with **two** positive controls (the macOS *mise* installer, and the *ubuntu* asdf installer), so the absence is provably macOS-specific and not "ls printed nothing".
**My best guess, explicitly labelled a guess:** every `absent` claim should be required to name a sibling positive claim over the **same target**, exactly as `must_fail` `cli-help` probes must. Of the `absent` claims in the ledger today I checked one; the rest are unaudited by me.
**Cost of guessing wrong:** low if the rule is added and redundant; high if not. An `absent` claim over an empty or wrong file is a permanently green check that asserts nothing — the precise failure the `must_fail` control discipline exists to prevent, sitting one evidence-kind over.

**Resolution (👑 lead, CROSS-AUDIT) — CONFIRMED. This is a GROUND-TRUTH-CLASS gap, and it is only *partly* mitigated.**
utm asked whether the hazard is real and noted *"the rest are unaudited by me."* I audited them and executed the probe.

**1. The gap is real at the level of the evidence KIND.** `check_absent` is one line — `return expect not in haystack` — so an `absent` claim passes against **any** file lacking the string, including a file that has been emptied or gutted:
```
[PASS] PROBE-absent-on-EMPTY-file    target=<zero-byte file>            expect=HOMEBREW_GITHUB_PACKAGES_TOKEN
[PASS] PROBE-absent-on-GUTTED-file   target=<content replaced>          expect=HOMEBREW_GITHUB_PACKAGES_TOKEN
2/2 claims verified   EXIT=0
```
Nothing in `tools/verify_claims.py` requires an `absent` claim to prove its target *is still the file we think it is*. `_RULES.md` §5 mandates a control only for a negative `must_fail` `cli-help` probe. **The rule stops one evidence-kind short.**

**2. The *missing-file* half is now closed — and it was WIDE OPEN at `HEAD`.** 🔬 ledger added a `FileNotFoundError → UNREACHABLE:` guard this run. Proven by running the **original** verifier from `git show HEAD:tools/verify_claims.py`:
```
# ORIGINAL code, line 249-250:  except FileNotFoundError as e: return Result(..., f"missing: {e}", ...)
#                                ^ no UNREACHABLE prefix, so must_fail INVERTS it
$ uv run tools/verify_claims.py <must_fail file-line claim whose target file does not exist>
[PASS] PROBE-mustfail-fileline-on-deleted-file  (file-line)
1/1 claims verified   EXIT=0
```
**A `must_fail` control whose target file is DELETED went GREEN.** That is ledger's *"controls green on deleted files"*: a 404 wearing a green check. Post-fix the same probe yields `UNREACHABLE: missing file: …`, exit **3**, never inverted.

**3. Empirical coverage of the 13 `absent` claims.** Twelve are guarded *by accident or diligence* — each has a sibling `file-contains`/`file-line` claim over the **same `target`**, which pins the file's identity and would fail loudly if it were emptied. **Exactly one is unguarded:**

| `absent` claim | target | positive control on same target |
|---|---|---|
| `prep-makefile-has-no-smoke-target` | `Makefile` | ***NONE*** |

That claim is satisfied today by a `Makefile` that exists and lacks a smoke target. It would be **equally satisfied by an empty `Makefile`**. → 🔬 ledger: add a positive control asserting a real `Makefile` token, and consider enforcing the pairing **structurally** so it cannot be forgotten (require every `absent` record to name a `control` id, and fail `USAGE` if it does not — the same way a bare negative `cli-help` probe is rejected as unfalsifiable).

**Status flipped to ANSWERED for the diagnosis; the remediation is tracked as GATE-BLOCKER 4 in the backlog.** utm's proposed replacement (`xaudit-09-no-macos-asdf-installer-script-on-disk`, a `must_fail` `cli-help` over `ls .chezmoiscripts/` with **two** positive controls) is the right shape and should be merged.


---

## OQ-28 · utm · `12:79` hard-codes the UNVERIFIED VNC stdout string into a pytest assertion, 280 lines from its marker. Is that safe?
**Status:** OPEN
**Spec:** specs/macos-ci/12-tooling-and-agent-loop.md:79 (`sed -n '79p'`), marker at :359 (`grep -n`)
**What I tried:**

```
$ grep -n 'Opening vnc' specs/macos-ci/12-tooling-and-agent-loop.md
79:    line = "Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415..."
337:Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415...
$ grep -n 'UNVERIFIED: `--vnc-experimental`' specs/macos-ci/12-tooling-and-agent-loop.md
359
```

The marker at `:359` correctly guards the §`gui` prose at `:337` — **G13 was NOT upgraded to fact, and `xaudit-12-vnc-stdout-stays-unverified` pins that.** But the string's *first* appearance, at `:79`, is inside "an obvious first failing test, before a line of implementation exists" — a TDD example whose `assert` encodes the unverified format as the specification of `parse_vnc_url`. A reader who implements `12` top-to-bottom meets the assertion 280 lines before the caveat.
**Why it is stuck:** whether that matters depends on a judgement I cannot make read-only — is `:79` illustrative prose, or is it the seed test someone will paste into `tests/unit/test_gui_core.py`? `12` presents it as the latter. Settling the *format itself* needs a booted VM (OQ-02, BLOCKED-BY-SCOPE); settling the *placement* is an editorial call for 🧪 harness.
**My best guess, explicitly labelled a guess:** harmless today, because the test would fail loudly on first contact with a real VM rather than silently. The risk is that a red test gets "fixed" by adjusting the regex to match whatever the VM printed, at which point the unverified format has been laundered into a passing test.
**Cost of guessing wrong:** exactly OQ-02's cost, one layer down: `parse_vnc_url`'s regex silently fails to match, and the GUI lane breaks with no diagnostic. A cheap mitigation is to repeat the marker at `:79`, or to write the example test as `pytest.mark.xfail(reason="format unverified; see OQ-02")`.

---

---

## OQ-29 · tart-ci (cross-audit of 🔐 secrets) · NEEDS-HUMAN · `packer-sensitive-hides-secret-under-debug-log` is blind, but `_RULES.md` §5 forbids weakening a `must_fail`. Keep it, retire it, or supersede it?
**Status:** ANSWERED (human decision YES; implemented by 🔬 ledger)  
**Spec:** specs/macos-ci/13-build-secrets.md:290-303 (the table secrets wrote); `.team/claims.jsonl`
**Question:** 🔐 secrets diagnosed the pair as under-powered and was **right**. I confirmed it by execution, not by reading. But the fix collides with a standing invariant: *"NEVER delete, weaken, or 'fix' a control"* (`_RULES.md` §5), and the brief names `packer-sensitive-hides-secret-under-debug-log` as one of the original six `must_fail` claims. **What do you do with a `must_fail` claim that passes for the wrong reason?**
**What I tried:** separate pipes, then a simulation. `packer inspect` is allowed; `packer build`/`init` were not run.
```
$ packer inspect tests/fixtures/packer-sensitive          > out 2> err      # stdout 136B, stderr   0B
$ PACKER_LOG=1 packer inspect tests/fixtures/packer-sensitive > out 2> err  # stdout 136B, stderr 845B
$ cmp out_plain out_log   ->  identical.   The overlay adds NOTHING to stdout.
```
Then I simulated *"a Packer that ignores `PACKER_LOG`"* by pinning `env={"PACKER_LOG":"0"}` and re-running the real claims' evidence:
```
[PASS] SIM-old-control-under-PACKER_LOG-0        expect=plain_FIXTURE_CONTROL   <- control is BLIND
[PASS] SIM-old-negative-under-PACKER_LOG-0       expect=ghp_FIXTURE_SENTINEL    <- must_fail probe is BLIND
[FAIL] SIM-new-discriminator-under-PACKER_LOG-0  expect=[INFO] Packer version:  <- successor SEES it
[FAIL] SIM-new-control-under-PACKER_LOG-0        expect=plain_FIXTURE_CONTROL   <- successor SEES it
[FAIL] MUT-new-negative-is-live                  (mutation)  "CONTROL PASSED — the oracle is broken"
```
**Both halves of the existing pair go green against a Packer that never emitted a debug log.** They are not vacuous in the *empty-output* sense — stdout is non-empty and really does print the control literal — they are vacuous in the *causal* sense: nothing in the evidence depends on `PACKER_LOG` having done anything.
**Why it is stuck:** the repair is not a code change, it is a **policy** call, and three rules point in different directions. (a) `_RULES.md` §5: never weaken a control. (b) The same section's rationale: *"a verifier nobody verifies is just a second thing to trust."* (c) Only 🔬 ledger may edit `.team/claims.jsonl`. Deleting the pair violates (a). Keeping it violates (b), because it reports `PASS` for a proposition it does not test, and its `id` — `…-under-debug-log` — actively misleads the next reader. I have proposed a **superseding** pair (`packer-sensitive-hides-secret-in-isolated-debug-log` + two controls) that isolates stderr with `sh -c '… 2>&1 1>/dev/null'` and dry-runs green, but I cannot decide whether the old pair should now be **retired**, **kept as a deliberately-documented weak check**, or **rewritten in place** (which §5 forbids).
**My best guess, explicitly labelled a guess:** keep both, and amend the old claim's `claim` prose to say it is superseded and why — prose is not evidence, so editing it weakens nothing. That preserves §5's letter (no `must_fail` deleted, no `expect` loosened) while removing the misleading green check's power to reassure. **I am guessing about the intent behind §5, not about the behaviour of Packer.**
**Cost of guessing wrong:** If the old pair is silently kept as-is, the ledger carries a claim whose name asserts *"masking survives PACKER_LOG=1"* and whose evidence would survive Packer removing `PACKER_LOG` support entirely. The underlying proposition **is true today** — I verified masking really does hold on the isolated stderr stream — so nothing is currently mis-stated in `13`. The danger is purely in the *verifier*: the day upstream changes debug-log behaviour, the check that exists to notice will not notice. **That is the exact failure `must_fail` was invented to prevent, wearing the costume of a passing test.**

**Resolution (🔬 ledger + 🏭 tart-ci, human decision YES) — blind pair KEPT, prose amended, successor added.**
🏭 tart-ci proved **by execution** that `packer-sensitive-hides-secret-under-debug-log` and its control are
**both blind**: pinning `PACKER_LOG=0` and re-running the real evidence left both still passing, because
`packer inspect` writes its debug log to **stderr** while the claims read **stdout** — byte-identical either way.

**The proposition is TRUE TODAY.** Masking really does hold on the isolated stderr stream; nothing in spec 13 is
mis-stated. *The rot is in the verifier: the day upstream changes debug-log behaviour, the check that exists to
notice will not notice.*

- **Kept** both old claims. `expect` untouched. `_RULES.md` §5 holds — never delete or weaken a control.
- **Amended their `claim` prose** to open with *"SUPERSEDED, DO NOT TRUST THIS GREEN CHECK"* and say why.
  Prose is not evidence, so editing it weakens nothing — but it strips a misleading green check of its power
  to reassure, which is the only harm it was doing.
- **Added** tart-ci's successor pair, which isolates stderr with `sh -c '… 2>&1 1>/dev/null'`:
  `packer-sensitive-hides-secret-in-isolated-debug-log` (`must_fail`, `polarity: negative`) with
  `CONTROL-packer-debug-log-stderr-prints-plain-literal` and `CONTROL-packer-debug-log-stderr-emits-info-banner`
  on the **same argv and env**. Confirmed by hand: that stream is 845 bytes under `PACKER_LOG=1`, 0 bytes
  without it, and contains the sentinel **zero** times.

Both new claims carry `polarity: negative` per OQ-37. **ANSWERED.**

---

## OQ-30 · tart-ci (cross-audit of 🔐 secrets) · Is `sh -c` inside a `cli-help` `argv` legitimate ledger evidence, or a hole?
**Status:** OPEN
**Spec:** `.team/proposed/tart-ci.jsonl` (4 new claims); `tools/verify_claims.py:209-225`
**Question:** `cli-help` runs `subprocess.run(argv, …)` with no shell, so redirection is impossible — which is precisely why no existing claim can separate stdout from stderr, and why the debug-log pair was under-powered in the first place. I closed that by making `argv` be `["sh","-c","… 2>&1 1>/dev/null"]`. It works, it dry-runs green, and it is read-only. **But it turns an evidence kind that runs *one binary* into one that runs *arbitrary shell*.**
**What I tried:**
```
argv = ["sh","-c","packer inspect tests/fixtures/packer-sensitive 2>&1 1>/dev/null"]
  env PACKER_LOG=1 -> 845 bytes captured (stderr only); contains [INFO], plain_FIXTURE_CONTROL, <sensitive>; NOT the sentinel
  env PACKER_LOG=0 ->   0 bytes captured
```
I also used it to add a **FETCH_FAILED guard** to two network probes, so an empty `curl` cannot masquerade as a pass — something a bare `cli-help` + `curl` claim **cannot** do, because it ignores curl's exit code (OQ-08).
**Why it is stuck:** it is a judgement call about the ledger's threat model, and 🔬 ledger owns `tools/verify_claims.py`. Shell in `argv` buys exactly two things nothing else offers — **stream separation** and **guarded network probes** — and costs shell-quoting fragility plus a much larger blast radius for a malformed record. A first-class `url-contains` kind (OQ-08) and a `stream: "stderr"` field on `cli-help` would give both benefits with none of the shell.
**My best guess, explicitly labelled a guess:** ledger should accept the four `sh -c` claims **now**, because they are the only thing standing between the repo and a green check that means nothing, and then replace them with a `stream` field when the verifier next changes. I have not read whether any sandbox or CI context would execute these differently.
**Cost of guessing wrong:** low and bounded, but real. If `sh -c` is rejected, the isolated debug-log pair cannot be expressed at all with today's verifier, and OQ-29's superseding claims evaporate — leaving the blind pair as the only thing guarding G16's most load-bearing behaviour. If it is accepted uncritically, every future claim can smuggle a pipeline into `argv`, and `just check` becomes a shell script nobody reviews.

---

## OQ-31 · secrets · OPEN · `file-line` + `must_fail` silently inverts an OUT-OF-RANGE line into a PASS. Is `CONTROL-12-line-607-does-not-exist` proving what it claims?
**Status:** OPEN
**Spec:** tools/verify_claims.py:126 (`check_line` out-of-range) and :289 (the inversion guard)
**Question:** `evaluate()` refuses to invert two failure prefixes — `UNREACHABLE:` and `STRUCTURE:` — because neither is evidence about the claim. **There is no third guard for "the line does not exist."** `check_line` returns a bare `line N out of range (file has M)` with no prefix, so `must_fail` flips it to PASS. A `must_fail` `file-line` control therefore cannot distinguish *"line N exists and says something else"* (the thing it means) from *"the file is shorter than N"* (a structural fact about the file).
**What I tried:** a mutation test against the live tools, in the scratchpad:
```
{"id":"MUT-C","kind":"file-line","must_fail":true,"target":"specs/macos-ci/12-tooling-and-agent-loop.md",
 "line":99999,"expect":"vnc_port"}
  -> [PASS]        # line 99999 does not exist. The control "passed".
{"id":"MUT-D","kind":"cli-help","must_fail":true,"argv":["tart-nonexistent",...]}
  -> [FAIL] UNREACHABLE: 'tart-nonexistent' not on PATH    # correctly NOT inverted
```
So `cli-help` is guarded against a missing binary and `doc-contains` against a missing page, but `file-line` is **not** guarded against a missing line.
**Why it is stuck:** `tools/verify_claims.py` is owned solely by 🔬 ledger. The fix looks like a
`RANGE:` prefix in `check_line`, added to the tuple at :289 — but whether `CONTROL-12-line-607-does-not-exist`
should then be *re-expressed* (it deliberately relies on 607 being out of range) is a design call, not
a bug fix I can make unilaterally.
**This is not hypothetical — it touches a live claim.** `CONTROL-12-line-607-does-not-exist` passes
**today via exactly this path**: spec 12 is 577 lines, so 607 is out of range. Its stated purpose —
recording that the prior lead's `:607` citation was fabricated — is served. But the same claim would keep
passing if spec 12 were truncated to three lines, and nobody would learn anything. It is a control whose
green means "607 ≥ len(file)", not "607 was fabricated".
**My best guess, explicitly labelled a guess:** add `RANGE:` and keep `CONTROL-12-line-607-does-not-exist`
by pairing it with a positive `file-line` at some line **greater than 607** — which is impossible while
the file is 577 lines. The honest alternative is to re-express it as `absent` over the *citation string*
rather than as a line probe.
**Cost of guessing wrong:** every `must_fail` `file-line` control in the ledger — including my own
`CONTROL-spec12-line-330-is-not-the-vnc-port-mention` — could go green on a deleted or truncated file. I
guarded mine by hand: its partner `spec12-vnc-port-mention-is-at-349` pins line **349 > 330**, so a file
that shrank below 330 fails loudly first. That guard is a coincidence of my line numbers, not a property
of the tool. **A control that passes because the file vanished is the `STRUCTURE:` bug, one evidence-kind
over.**

---

## OQ-32 · secrets · NEEDS-HUMAN · The `pre_tool_use` hook writes its command log INTO the read-only reference clones, poisoning `grep`-based evidence. Should the clones be treated as untrusted?
**Status:** ANSWERED
**Spec:** (environment — affects every `file-contains` / `absent` claim targeting a reference clone)
**Question:** `/Users/bossjones/dev/cirruslabs/packer-plugin-tart/logs/{pre,post}_tool_use.json` did not exist before this run. They are **untracked** (`git status` → `?? logs/`, 0 tracked files) and were created at 21:24 today. They contain the **verbatim text of every Bash command an agent ran while `cwd` was inside that clone** — including the greps we ran *looking for* strings. Should the reference clones still be treated as authoritative evidence?
**What I tried:** I nearly filed a false refutation because of this. Auditing 02:172-177 (*"no `vnc_port*` key … anywhere in the plugin's source"*):
```
grep -rIn 'vnc_port' /Users/bossjones/dev/cirruslabs/packer-plugin-tart --exclude-dir=.git
  -> logs/pre_tool_use.json:30   ... "command": "... grep -rn 'vnc_port' ..."
  -> logs/post_tool_use.json:66  ... (idem)
```
Two hits. **Both are recordings of the very greps run to prove there were none.** Excluding `logs/`:
```
grep -rIn 'vnc_port|VNCPortMin|VNCPortMax' ... --exclude-dir=.git --exclude-dir=logs
  -> ZERO hits.    # 02:172-177 UPHELD
```
The log also now contains the ledger's secret sentinel `ghp_FIXTURE_SENTINEL` (1 file), written to disk
inside a third-party checkout by the run whose thesis is *never write a secret to the guest filesystem*.
**Why it is stuck:** three separable decisions, all the human's. (a) Is a hook that mutates a directory
the brief calls read-only (*"read them, never WebFetch them"*) an acceptable side effect? (b) Should
`tools/verify_claims.py` refuse targets under a `logs/` path, or should the clones be `.gitignore`d /
relocated? (c) Should the sentinel be scrubbed? I did not delete anything: the `pre_tool_use` hook blocks
the deletion verb, and these files are outside this repo and outside my ownership.
**My best guess, explicitly labelled a guess:** the current *ledger* is unharmed — every `file-contains`
and `absent` claim resolves `target` to a **single file** via `_read()`, never a directory walk, so no
live claim can match a log. The exposure is to **prose claims and to humans**, i.e. to anyone who
reproduces a spec's "grep the source" argument by hand, as I just did.
**Cost of guessing wrong:** a self-fulfilling oracle. Any agent that greps a reference clone for a string
it has previously typed will find it, conclude the source contains it, and refute a true claim — or
"confirm" a false one. The evidence corpus is contaminated by the instrument that records the search.
This is G10's failure mode with a new cause: not a fabricated citation, but a **fabricated corroboration.**

---


**Resolution (performed by the human orchestrator; re-verified read-only by 👑 lead):** the reference clones were contaminated **by this run's own `pre_tool_use` hook**, which wrote `ghp_FIXTURE_SENTINEL` into a **third-party checkout** — during the run whose thesis is *never write a secret to a filesystem you do not control* (G15/G17, spec 13). **The irony is the finding.**

Provenance was established **before** anything was touched, and only this run's own artifacts were moved (`mv` into a scratchpad — nothing deleted):

| path | created | this run? | action |
|---|---|---|---|
| `cirruslabs/packer-plugin-tart/logs/` | Jul 9 21:46–21:48 | **yes** | moved to scratchpad |
| `cirruslabs/macos-image-templates/logs/` | Jul 9 22:23 | **yes** | moved to scratchpad |
| `zsh-dotfiles/logs/`, `zsh-dotfiles-prep/logs/` | oldest Sep 30 2025 | **no** | **left alone, deliberately** |

Lead's independent re-verification:
```
grep -rl 'ghp_FIXTURE_SENTINEL' /Users/bossjones/dev/cirruslabs/       -> 0 files
grep -rIn 'vnc_port' <packer-plugin-tart> --exclude-dir=.git           -> 0 hits
ls -d /Users/bossjones/dev/cirruslabs/*/logs                           -> no matches
ls -d .../zsh-dotfiles/logs .../zsh-dotfiles-prep/logs                 -> both present, untouched
```

So **`02:172-177` is UPHELD with no `--exclude-dir=logs` needed** — the near-false-refutation is gone *at the source*. A `--exclude-dir` workaround would have been **a spec accommodating a defect in our own tooling**. 🔬 ledger has since made `check_structure()` reject any evidence target with a `logs` path component (exit 4), so the class cannot recur silently. Recorded in `11-sources.md` by 📚 synth.
## OQ-33 · synth · Why does the ledger's control requirement exempt a `cli-help` probe whose `expect` is itself a negative, like `404`?
**Status:** ANSWERED (controlled by 🔬 ledger, GAP1 — predicate NOT tightened; see OQ-36)  
**Spec:** `.team/claims.jsonl` (`no-terraform-provider-at-cirruslabs-tart`, `no-terraform-provider-at-cirruslabs-orchard`); `tools/verify_claims.py` (`needs_control`)
**What I tried:**
```
# The two G1 probes, verbatim from the ledger:
curl -sS -o /dev/null -w '%{http_code}' https://registry.terraform.io/v1/providers/cirruslabs/tart      -> 404
curl -sS -o /dev/null -w '%{http_code}' https://registry.terraform.io/v1/providers/cirruslabs/orchard   -> 404
# Same argv shape against a provider that certainly exists:
curl -sS -o /dev/null -w '%{http_code}' https://registry.terraform.io/v1/providers/hashicorp/aws        -> 200
# And the live tool accepts the probe with NO control at all:
uv run tools/verify_claims.py <(echo '{"id":"probe-404","kind":"cli-help","argv":[...],"expect":"404"}')  -> EXIT 0
```
**Why it is stuck:** `needs_control()` fires on `absent`, and on `must_fail` + (`cli-help` | `doc-contains` |
`doc-index`). These two probes are **positive** `cli-help` records — `must_fail` is unset — so the
enforcement never fires. But their *semantic content* is a negative existence claim: "no provider is
published at this address." Negativity is a property of what the `expect` string **means**, not of the
`must_fail` flag, and the tool can only see the flag. Deciding whether to key the rule on meaning (how?)
or to hand-audit each `cli-help` whose expect is an error code is a design call on a file I do not own
(🔬 ledger owns `verify_claims.py`; I may not edit it).
**My best guess, explicitly labelled a guess:** the shape was never considered, because GB4's remediation
generalized from `absent` and from `must_fail` probes — the two shapes that had *already* burned the team
— rather than from the definition of negative evidence. The gap is a blind spot, not a decision.
**Cost of guessing wrong:** if the Terraform Registry ever moves `/v1/providers/` (to `/v2/`, or behind
auth), **both probes keep printing `404` and both keep passing** — now "proving" that no provider exists
when all they prove is that the endpoint moved. This is precisely the failure `STRUCTURE:` was invented to
stop for `doc-contains` ("the page vanished" ≠ "the sentence vanished"), and there is no `STRUCTURE:`
equivalent for an HTTP probe. G1 is the **first settled fact in `CLAUDE.md`** and the load-bearing premise
of the entire ADR. It currently rests on two uncontrolled negatives. The fix is one ledger record — a
`CONTROL-terraform-registry-serves-a-known-provider` on `hashicorp/aws` expecting `200`, same argv shape —
which I have empirically confirmed passes today. → 🔬 ledger.

**Resolution (🔬 ledger, GAP1) — CONTROLLED, but the predicate was NOT tightened, and that is deliberate.**
👑 lead is right and the diagnosis is exact. `no-terraform-provider-at-cirruslabs-tart` and
`...-orchard` are `cli-help` with `expect: "404"` and `must_fail` UNSET, so `needs_control()` never fires:
**it keys on the FLAG, not on what `expect` MEANS.** A 404 is a negative existence claim wearing positive
clothes. Reproduced against a deliberately-moved endpoint:

```
[FAIL] CONTROL-registry-serves-known-provider-MOVED   .../v1/MOVED/hashicorp/aws  did not emit '200'
[PASS] no-provider-probe-MOVED                        .../v1/MOVED/cirruslabs/tart  -> still 404, still PASSES
1/2 claims verified   EXIT=2
```

The probe passes while proving nothing. **Only the control turns the gate red.** Added
`CONTROL-terraform-registry-serves-a-known-provider` (`curl .../v1/providers/hashicorp/aws` -> `200`,
verified) and wired it as the `control` of both probes. `check_structure()` now validates a `control`
**whenever it is present**, not only when required — otherwise these two would name a partner nobody checked.

**I did NOT tighten `needs_control()`, and I am saying so plainly rather than shipping a clever heuristic.**
Every rule I could write is a guess about meaning: *`expect` matches `^[45]\d\d$`* misfires on a claim
asserting a page legitimately returns 404 as its subject; *argv contains `%{http_code}`* misses
`grep -c` returning `0`, and `absent`-in-spirit `file-contains` claims whose `expect` is a negation in
English. The flag is checkable; the meaning is not. A heuristic here would produce false positives that
agents learn to suppress — the same disease as a tripwire that cries wolf. **See OQ-36:** the durable fix
is a `polarity: negative` field an author must set, enforced the way `control` now is. That is a schema
change and a decision for the human, not something I should invent at 246 claims.

---

## OQ-34 · synth · G1 says "no Terraform provider for tart **or for UTM**". Where is the UTM half?
**Status:** OPEN
**Spec:** `CLAUDE.md:17`; `specs/macos-ci/10-tart-vs-utm-adr.md:16`; `.team/claims.jsonl`
**What I tried:**
```
# Every claim in the ledger mentioning terraform, by id:
no-terraform-provider-at-cirruslabs-tart       -> registry.terraform.io/v1/providers/cirruslabs/tart
no-terraform-provider-at-cirruslabs-orchard    -> registry.terraform.io/v1/providers/cirruslabs/orchard
# That is the complete list. Zero claims probe UTM.
curl -sS -o /dev/null -w '%{http_code}' https://registry.terraform.io/v1/providers/utmapp/utm   -> 404
```
**Why it is stuck:** I can produce the `404` above, but on its own it is worth no more than the two probes
in OQ-33 — it refutes exactly one guessed address. `utmapp/utm` is a **plausible** canonical name, not a
documented one; UTM's org could publish under any namespace. Settling "no provider exists" (rather than
"not at this address") needs the registry's **search** endpoint, whose parameters neither
`no-terraform-provider-*` claim's prose could pin down either — both explicitly scope themselves to "the
canonical address ONLY" and say the `q=` search parameter defeated them. So the same wall that stopped the
tart half stops the UTM half; the difference is that the tart half at least has *a* record and the UTM half
has none, while `CLAUDE.md` states both with equal confidence.
**My best guess, explicitly labelled a guess:** no UTM Terraform provider exists. The maintainer's own
"a long way off" reply on `utmapp/UTM#3618` (the IaC feature request, cited in `05` and the ADR) is far
better evidence for G1's UTM half than any registry probe, and it is *already sourced* — it is just not in
the ledger, because no evidence kind fetches a GitHub discussion.
**Cost of guessing wrong:** low for the decision (the ADR would still choose Tart on Packer + guest-agent
grounds alone), high for the epistemics. The repo asserts the UTM half as a **settled fact that must not be
re-litigated** while holding zero evidence for it. That is the exact shape of G10 — a confident,
unfalsifiable, uncheckable instruction — and G10 is why this run exists. Either add a probe and label its
scope honestly, or downgrade `CLAUDE.md:17` to cite `utmapp/UTM#3618` instead of asserting registry
absence. → 🔬 ledger + 👑 lead (`CLAUDE.md`).

---

## OQ-35 · synth · Why is `verify_claims.py`'s own behaviour asserted by grepping its source instead of by running it?
**Status:** ANSWERED (closed by 🔬 ledger, GAP3 — the tool is now verified BY the tool)  
**Spec:** `.team/claims.jsonl` (`verify-claims-missing-file-is-unreachable`); `tools/verify_claims.py`
**What I tried:**
```
# The ONLY claim about the tool's behaviour:
{"id":"verify-claims-missing-file-is-unreachable","kind":"file-contains",
 "target":"tools/verify_claims.py","expect":"UNREACHABLE: missing file:",
 "claim":"an absent target file yields an UNREACHABLE-prefixed failure, which must_fail never inverts..."}

# Claims whose argv EXECUTES the tool:  0
# And the tool trivially CAN test itself -- I ran this, read-only, against a scratch ledger:
uv run tools/verify_claims.py <ledger with one control-less `absent` record>
  -> "STRUCTURAL REJECTION - negative evidence without a positive control"
  -> EXIT 4
```
**Why it is stuck:** the claim's **prose** asserts a *behaviour* ("an absent target file yields an
UNREACHABLE-prefixed failure, which `must_fail` never inverts"). Its **evidence** is that a string appears
somewhere in the source. Move that literal into a comment, delete the `except FileNotFoundError` handler,
and the claim stays green while the behaviour it names is gone — and `CONTROL-12-line-607-does-not-exist`,
which that handler exists to protect, silently starts passing for the wrong reason. `tools/` is 🔬 ledger's
file and `tests/` holds one fixture directory, so I can neither add the fixture ledgers nor the claims.
**My best guess, explicitly labelled a guess:** the tool's invariants *were* adversarially tested — GB4's
`exit 4` matrix and GB3's four-case table are both written up on the board — but the tests were run **by
hand** and their results recorded **as prose**. Nobody converted them into claims because the tool felt
like the thing that checks claims rather than a thing that has them.
**Cost of guessing wrong:** the verifier is the one artifact in this repo with no verifier. Every one of
the other 242 claims inherits its trustworthiness from this tool's `must_fail` inversion, its
`UNREACHABLE:`/`STRUCTURE:` non-inversion, and its `needs_control()` rejection — three behaviours, zero
executing claims. The board's own Defect A was "the previous board **faked the gate** with a bracketed
paraphrase"; a hand-run test transcribed into prose on the board is the same evidence class, differing only
in the honesty of the transcriber. Three `cli-help` claims over checked-in fixture ledgers (`expect:
"STRUCTURAL REJECTION"`, `expect: "UNREACHABLE"`, `expect: "CONTROL PASSED"`) would close it, and each one
passes today. *A verifier nobody verifies is just a second thing to trust.* → 🔬 ledger.

**Resolution (🔬 ledger, GAP3) — CLOSED. The tool is now verified BY the tool.**
👑 lead's indictment is correct and it lands on the ledger, not on the lead.
`verify-claims-missing-file-is-unreachable` was `file-contains` over `tools/verify_claims.py`: it grepped
the **source** for the literal `UNREACHABLE: missing file:` while its prose asserted a **behaviour**. Move
that literal into a comment and delete the `except FileNotFoundError` handler and the claim stays green.
**Zero claims executed the tool.** Its three trust-bearing behaviours — `must_fail` inversion,
`UNREACHABLE:`/`STRUCTURE:` non-inversion, and `needs_control()` rejection — were adversarially tested by
hand and recorded **as prose on the board**. That is the evidence class of Defect A, where a previous lead
faked the gate with a bracketed paraphrase. It differs only in the honesty of the transcriber, and
**honesty is not an evidence kind.**

Five checked-in fixture ledgers now live under `tests/fixtures/verifier/`, and nine `cli-help` claims
EXECUTE `tools/verify_claims.py` against them and assert on its real stdout/stderr:

| claim | asserts |
|---|---|
| `verifier-missing-file-emits-unreachable` | absent target -> `UNREACHABLE: missing file:` |
| `verifier-missing-file-is-not-inverted-into-a-pass` | ...and `must_fail` does NOT invert it (`[PASS]` never printed) |
| `verifier-mustfail-inverts-a-plain-failure` | out-of-range line -> plain False -> inverted -> `1/1 claims verified` |
| `verifier-rejects-an-uncontrolled-negative` | uncontrolled `absent` -> the real `STRUCTURAL REJECTION` message |
| `verifier-uncontrolled-negative-never-reaches-evaluation` | ...and `claims verified` is never printed: a gate, not a warning |
| `verifier-accepts-a-wellformed-pair` | a controlled negative IS admitted -> `2/2 claims verified` |
| `CONTROL-verifier-oracle-fixture-executes` | the oracle fixture really runs |
| `verifier-exempts-oracle-control-from-structural-check` | ...and a `CONTROL-*` doc oracle is NOT rejected |

Every negative probe carries its positive control **on the same argv** — my own invariant, applied to
myself. `CONTROL-verifier-oracle-fixture-executes` deliberately asserts a claim id rather than
`1/1 claims verified`, so a network outage cannot make it silently vacuous.

`CONTROL-12-line-607-does-not-exist` now carries
`"control": "verifier-mustfail-inverts-a-plain-failure"`: the inversion it depends on is proved by
execution, not by the lead's hand-testing. The source-grep claim is **deleted**, not repaired — it could
never have proved what it said. **Status: ANSWERED.**

---

## OQ-36 · synth · `check_structure` proves a control *exists*. Should it also prove the control probes the *same substrate*?
**Status:** OPEN
**Spec:** `tools/verify_claims.py` (`check_structure`); `.team/claims.jsonl`
**What I tried:** GB4 put the positive-control rule in the tool. I tried to defeat it, and did — with a
control that satisfies every structural check while proving nothing about the negative it guards:
```
# ledger: an `absent` claim over an EMPTY file, whose control targets an UNRELATED file
{"id":"neg","kind":"absent","target":"<empty file>","expect":"ansible","control":"pos"}
{"id":"pos","kind":"file-contains","target":"Justfile","expect":"build-golden:"}

uv run tools/verify_claims.py <that ledger>   ->  2/2 claims verified,  EXIT 0
```
`neg` passes **vacuously** — the file is empty — and `pos` passes for a reason unconnected to it. The
tool checked that `control` names a resolvable, non-self, non-`must_fail` claim id. It never asked
whether that claim probes the same file, the same `argv`, or the same page.
**Why it is stuck:** the fix is not obvious, and it is not my file (🔬 ledger owns `verify_claims.py`).
Requiring `control.target == claim.target` would be correct for `absent`, but **wrong for exactly the
shape GB2 retracted**: a `grep -c` negative *cannot* share `argv` with its control, which is why the
brief's JOB 2 was a logical impossibility in the first place. So "same substrate" means same *file* for
`absent`, same *page* for `doc-contains`, and same *command shape against the same substrate* for
`cli-help` — three different predicates, one of which ("shape") a machine cannot check.
**My best guess, explicitly labelled a guess:** `absent` and `must_fail doc-contains`/`doc-index` can be
tightened mechanically (same `target` / same `page`), closing most of the gap, and `cli-help` must stay a
human-reviewed pairing with the partnership named in the `claim` prose — which is the discipline the 24
paired records already follow.
**Cost of guessing wrong:** this is **the same hole one level up, for the fourth time** — the exact
progression GB2 → GB4 → GB5 records, now recorded in `11-sources.md`. Each round the enforcement moved
outward and a new exemption became the soft spot. Here the soft spot is that `control` is a *pointer with
no semantics*. All 13 `absent` records were audited by hand when GB4 landed, so nothing is believed to be
vacuous today — but "audited by hand once" is the property GB4 existed to stop relying on. A ledger
whose controls are unchecked pointers is one careless merge from a green check that means nothing.
→ 🔬 ledger.

---

## OQ-37 · ledger · NEEDS-HUMAN · Should a claim declare its POLARITY, so `needs_control()` stops guessing from the `must_fail` flag?
**Renumbered by 👑 lead:** filed as `OQ-36`, which 📚 synth had already taken in a concurrent turn. The append-only rule says *"if you race, renumber yours upward"* — two agents raced and neither saw the other. Content untouched; only the number changed. **The collision is itself a finding:** an append-only file with human-assigned sequence numbers has no allocator, so uniqueness is enforced by attention. It held for 35 of 37 entries.
**Status:** ANSWERED (human decision YES; implemented by 🔬 ledger)  
**Spec:** tools/verify_claims.py — `needs_control()`; `.team/claims.jsonl` — `no-terraform-provider-at-cirruslabs-{tart,orchard}`
**Question:** `needs_control()` decides a claim is negative from `kind == "absent"` or `must_fail and kind in (cli-help, doc-contains, doc-index)`. Both are **syntax**. OQ-33 found a claim that is semantically negative and syntactically positive: `cli-help`, `expect: "404"`, `must_fail` unset. The tool cannot see that a `404` is an assertion of ABSENCE.
**What I tried:**
```
# reproduced the failure the flag-based predicate cannot catch:
[FAIL] CONTROL-registry-serves-known-provider-MOVED    .../v1/MOVED/hashicorp/aws  did not emit '200'
[PASS] no-provider-probe-MOVED                         .../v1/MOVED/cirruslabs/tart -> 404, PASSES
```
and then enumerated the heuristics I could write, and rejected each:
- `expect` matches `^[45]\d\d$` -> misfires on any claim whose subject legitimately IS a 4xx page.
- `argv` contains `%{http_code}` -> misses `grep -c` returning `0`, and misses `file-contains` claims whose `expect` is an English negation.
- id starts with `no-` -> a name is not a warrant. GB5 already taught this: `CONTROL-d1-packer-dir-does-not-exist` is a negative and `CONTROL-*` is not a warrant either.
**Why it is stuck:** the flag is checkable; the MEANING is not. Any heuristic I write produces false positives, and a check that cries wolf gets suppressed — the exact failure mode of the bare-`UNVERIFIED` tripwire in GB3. The lead's instruction was explicit: *if you cannot tighten it without false positives, say so plainly and leave an OQ rather than a clever heuristic.* I cannot, so I did.
**My best guess, explicitly labelled a guess:** the durable fix is an explicit `"polarity": "negative"` field the author sets, enforced exactly as `control` now is: if `polarity == "negative"` then a `control` is mandatory. It moves the judgement from the tool (which cannot make it) to the author (who can), and it is auditable — a reviewer can ask *why is this claim not marked negative?* That is a schema change touching every future record, so it is the human's call, not mine.
**Cost of guessing wrong:** if we add the field and authors forget it, we are exactly where we are now, with more ceremony. If we never add it, every future negative-in-positive-clothes claim is un-caught, and `G1` (the first settled fact in CLAUDE.md) is defended by two probes that a registry URL change would silently turn into decoration. The added control blocks that today, for these two claims only.

**Resolution (🔬 ledger, human decision YES) — `polarity` is now an author-set field, enforced.**
`needs_control()` inferred negativity from **syntax**: `kind == "absent"`, or the `must_fail` flag. OQ-33 found
a claim that is semantically negative and syntactically positive — `no-terraform-provider-at-cirruslabs-tart`
(`cli-help`, `expect: "404"`, no `must_fail`), defending **G1**, the first settled fact in `CLAUDE.md`.
I rejected four inference heuristics as false-positive-prone; the human upheld that and said **stop inferring**.

```python
if claim.get("polarity") == "negative":   # author-set, never inferred
    return True                            # -> a `control` is mandatory; missing -> exit 4
```

Backfilled `polarity: negative` on **55** claims: every `kind == "absent"`, every `must_fail`, and the four
semantically-negative-syntactically-positive records (both `no-terraform-provider-at-cirruslabs-*` probes,
`packer-no-debug-log-on-stderr-when-overlay-disabled`, `synth-justfile-has-no-doctor-recipe`).
An invalid `polarity` value is itself a structural rejection. Verified adversarially: a `polarity: negative`
claim with no `control` exits **4**. It moves the judgement from the tool, which cannot make it, to the author,
who can — and it is auditable: a reviewer can now ask *why is this claim not marked negative?* **ANSWERED.**
