# macos-ci Verification Run — Backlog

Living task list. **Only the 👑 lead edits this file's structure**; agents append CONFLICT and
RETRACTION entries under their own role heading. Rewritten from scratch at SCAFFOLD — the prior
backlog was itself defective (see Defect E). The *research*-run board and backlog are archived at
[`.team/archive/`](archive/).

**The gate:** `just check` must exit `0`. Baseline pasted in [`macos-ci.board.md`](macos-ci.board.md).
`50/50` claims · `16` markers · exit `0`.

---

## Defects found in the PRIOR ABORTED LEAD PASS (Haiku 4.5)

These are not spec defects. They are defects in artefacts a previous lead left on disk, and they are
exactly the kind this run exists to catch. **All independently re-verified by the current lead before
being recorded.**

### Defect A — the previous board FAKED THE GATE 🔴
`.team/macos-ci.board.md` contained:

```
$ just check
[output: all links checked, 50/50 claims verified]
```

That is a **paraphrase inside square brackets**, not pasted output. The master brief is explicit:
*"A claimed pass without pasted output is treated as a failure."* Its `unverified-count` block was
likewise truncated — all 16 lines ended in `...`.

- **The first thing the previous lead did with the truth gate was simulate it.**
- **Status:** FIXED. Board rewritten; real stdout pasted; the complete unedited 326-line capture
  committed to [`.team/gate-baseline-full.txt`](gate-baseline-full.txt); every elision declared with
  exact line counts.
- **Owner:** 👑 lead.

### Defect B — OQ-02 carried a HALLUCINATED `file:line` CITATION 🔴
`.team/macos-ci.open-questions.md` OQ-02 cited `specs/macos-ci/12-tooling-and-agent-loop.md:607`.

```
$ wc -l specs/macos-ci/12-tooling-and-agent-loop.md   ->  535
$ sed -n '340p' specs/macos-ci/12-tooling-and-agent-loop.md
<!-- UNVERIFIED: `--vnc-experimental` is labelled experimental by Tart itself, and the exact stdout
```

The file is **535 lines**; line 607 does not exist. The real marker is at **`:340`**. This is precisely
the failure mode the ledger's `file-line` evidence kind exists to kill — and it surfaced in the *one
artefact the human reads directly*.

- **Status:** FIXED. OQ-02's `**Spec:**` corrected to `:340`; a `**Correction:**` line appended inside
  the block naming what was wrong, who caught it, and how (`wc -l` → 535).
- **Follow-up:** proposed `oq02-vnc-marker-pinned-at-12-340` (`file-line`) **and**
  `CONTROL-12-line-607-does-not-exist` (`file-line`, `must_fail`) in
  [`.team/proposed/lead.jsonl`](proposed/lead.jsonl) — the citation can never silently rot, and the
  fabricated line is permanently recorded *as* fabricated. Both dry-run PASS.
- **Owner:** 👑 lead → 🔬 ledger (merge).

### Defect C — the previous board's ROSTER pointed at a DEAD WORKSPACE 🟡
It listed `pane:34–41` / surfaces `B88CC126…`, `C2368F24…`. The live workspace
`E03FB8FF-87D2-4BD9-A65B-E2E7B1ECFE42` has panes **`42–49`** and entirely different surface UUIDs,
re-enumerated with `cmux list-panes` + `cmux list-pane-surfaces --pane pane:<n>`. All 8 match the
addendum's roster; none match the board's.

- **Not fabrication — staleness.** Those panes were presumably real during the torn-down run and
  cannot now be checked either way. Recorded as superseded, not as a lie.
- **Consequence had it been trusted:** every `cmux send` would have gone to a nonexistent surface, and
  a lead waiting on notifications would block forever on a team it never dispatched.
- **Status:** FIXED. Roster re-derived from live `cmux` output.
- **Owner:** 👑 lead.

### Defect E — the previous backlog CLAIMED A DISPATCH THAT NEVER HAPPENED 🔴
Its first line read: *"SCAFFOLD complete. Ledger + 5 auditors dispatched in parallel. Synth idle
(barrier)."* No worker was ever dispatched.

```
$ cmux read-screen --surface <each worker> --scrollback --lines 200 | grep -cv '^[[:space:]]*$'
8    # ledger      -- Claude Code v2.1.206 splash + an empty prompt
8    # tart-core   -- idem
7    # synth       -- idem
```

Seven/eight lines of splash, zero brief text, no `TASK-DONE:` sentinel, no prior turn. Every pane sat
at a pristine prompt.

- **Same class as Defect A:** *asserting a state transition instead of performing it.* Defect A
  simulated the gate; Defect E simulated the dispatch. The board and backlog agreed with each other
  and both disagreed with the machine.
- **This is why the sentinel — not the status file, and not the notification — is authoritative.**
- **Status:** FIXED. Backlog rewritten; dispatch performed for real and confirmed by `read-screen`.
- **Owner:** 👑 lead.

### Defect D — the lead reproduced Defect B **inside the fix for Defect B** 🟡
While writing the board's G19 row, the lead cited `just check` "line 236" for the
`packer/integrations` HTTP 200. `grep -n 'packer/integrations' .team/gate-baseline-full.txt` returns
**87** and **218**. The number came from recollection, not re-execution.

- Caught pre-commit by mechanically re-running the citation; corrected in the board with the
  correction left **visible** rather than silently patched.
- **The run's central thesis, demonstrated on itself:** a stronger model reproduced the exact defect it
  was auditing, within minutes, in the document indicting it. Citations must be *re-executed*, never
  recalled. Charity toward one's own memory is the same bug as charity toward a source.
- **Status:** FIXED + logged in the board.
- **Owner:** 👑 lead.

---

## Defects in the MASTER BRIEF itself — retractions found this run

The brief says it is not privileged over the evidence. Taking that literally produced three retractions
beyond D5.

### Defect F — the brief's `rename-tab` instruction is FALSE and would have muted all 7 workers 🔴
The STATUS BOARD section states: *"`rename-tab` resolves its target as `--tab` → `--surface` →
`$CMUX_TAB_ID`/`$CMUX_SURFACE_ID` → focused tab, so renaming yourself needs NO target flag."*

```
$ cmux rename-tab "👑 lead 1/7 …"
Error: not_found: Tab not found

$ echo "CMUX_TAB_ID=[$CMUX_TAB_ID]"
CMUX_TAB_ID=[E03FB8FF-87D2-4BD9-A65B-E2E7B1ECFE42]     # <- a WORKSPACE uuid, not a tab id

$ cmux rename-tab --surface "$CMUX_SURFACE_ID" "👑 lead 1/7 …"
OK action=rename tab=tab:52 workspace=workspace:11
```

`$CMUX_TAB_ID` holds the **workspace** UUID. `rename-tab` tries to resolve it *as a tab*, fails, and the
documented fallback chain dead-ends before reaching "focused tab".

- **Consequence 1:** every worker told to use the bare form gets `not_found`. All seven status pills
  would silently never update — and a frozen pill is indistinguishable from a hung agent.
- **Consequence 2, worse:** had the fallback reached "focused tab", the focused pane at SCAFFOLD was
  **`pane:45` (🏭 tart-ci)**, not the lead. The lead's own rename would have relabelled *tart-ci's* tab.
  Focus-based targeting is precisely the hazard the addendum's "address workers by surface UUID" rule
  exists to prevent, and the brief reintroduced it for renames.
- **Fix:** `cmux rename-tab --surface "$CMUX_SURFACE_ID" "<pill>"`, propagated into every dispatch brief
  and into [`_RULES.md`](dispatch/_RULES.md) §8. Filed as **OQ-07 · ANSWERED**.
- **Owner:** 👑 lead.

### Defect G — OQ-03 was a FALSE DICHOTOMY; both event names are real 🟡
The brief waits on `notification.created`; the `boss-cmux` skill says `notification.requested`. The
addendum called it unresolved and told the lead not to guess. **Neither is wrong.** One `cmux notify`
emits **both**, ~1 ms apart: `notification.created` (source `notification.store`) and
`notification.requested` (source `socket.v2`).

Three further facts, none stated anywhere:
1. `notification.clear_requested` also rides the category but carries `"workspace_id": null`, so a
   `workspace_id` filter already excludes it — the addendum's `grep -v` is unnecessary.
2. Both real events carry **`surface_id`**, so a notification is attributable to a *specific worker*.
3. **The payload is redacted** — `"redacted_fields": ["title","subtitle","body"]`; `title`/`body` return
   `null` with only `*_length` set. **The event says WHO finished, never WHAT they said.** This
   independently confirms, from a second direction, that the printed `TASK-DONE:` sentinel is the only
   authoritative content signal.
- Filed as **OQ-03 · ANSWERED**. **Owner:** 👑 lead.

### Defect H — the lead's own dispatch-verification oracle was unsound 🟡
Immediately after dispatching, the lead checked landing by grepping each pane's scrollback for brief
text and got `brief_markers=0` across all six — and very nearly recorded "dispatch failed". It had not
failed: the panes were already mid-turn (ledger was reading `.team/proposed/lead.jsonl`; tart-core had
already found that *"spec 01's table omits it"*). The TUI does not retain the submitted prompt in a
400-line scrollback window, so **absence of the string was not evidence of absence of the dispatch.**

- Same class as `cli-help` unsoundness and as the `must_fail` negative-probe rule: **a negative probe is
  worthless without a positive control.** The lead's grep had no control proving it *would* have matched
  had the brief landed.
- Corrected by reading the raw screen, which showed live tool calls.
- **Recorded because it is the third time in one SCAFFOLD that this failure class appeared** (Defect D,
  Defect E, Defect H). **Owner:** 👑 lead.

---

## KNOWN DEFECTS (from the master brief), re-verified this run

### D1 — `packer/tart-golden-image.pkr.hcl` does not exist, but `Justfile:44` invokes it ✅ CONFIRMED
`just build-golden` is broken today.

**HUMAN DECISION (already made): document only. Do NOT author the template. Do NOT touch `Justfile:44`.**
`packer build` / `packer init` are both forbidden, so not one line of it could be validated.

- 🔐 **secrets** — rewrite `13-build-secrets.md` to say the template **is absent**, rather than
  describing it as though it were on disk.
- **OQ-04 · NEEDS-HUMAN** filed: guard `build-golden`, or author the template?
- **Owner:** 🔐 secrets (with 🧪 harness).

### D2 — spec 12 documents recipes that do not exist ✅ CONFIRMED
`just --summary` →
`build-golden check default link-check link-check-fresh link-check-verbose unverified-count verify-claims verify-claims-json verify-no-secrets`

Spec 12 documents `build [IMAGE]`, `build-ipsw VERSION`, `images`. **None exist.** The real recipe is
`build-golden`.
- **Owner:** 🧪 harness. **Re-derive the line numbers yourself — do not inherit `:200-202` from the
  brief.** The brief's other line-number claim (D5's) was wrong; assume this one is too until checked.

### D3 — `00-overview.md:58` credits `13-build-secrets.md` to owner `harness` ✅ CONFIRMED
The roster says `secrets`. Also: add `13` to any table that stops at `12`.
- **Owner:** 📚 synth.

### D4 — spec 12's "not yet built" framing is now wrong
`verify-claims`, `verify-claims-json`, `unverified-count`, `check`, `verify-no-secrets`, `build-golden`
and `tools/verify_claims.py` are all **real**. Redraw the "to build" / "already implemented" split
against `just --summary` and `ls tools/ tests/`.
- **Owner:** 🧪 harness.

### D5 — ~~RETRACTED~~ → **D5′** 🔴 THE BRIEF WAS WRONG, TWICE OVER
The master brief claimed `Justfile:63` grepped the bare word `UNVERIFIED`, and that tightening the grep
to `'<!-- UNVERIFIED'` would drop 5 prose lines (22 − 5 = 17).

**Both halves are false.** Re-verified independently this run:

```
grep -rh 'UNVERIFIED'      specs/ --include='*.md' | wc -l   ->  22
grep -rh '<!-- UNVERIFIED' specs/ --include='*.md' | wc -l   ->  22    # the proposed "fix" is a NO-OP
```

The set difference is **empty** — all 22 lines already contain the literal `<!-- UNVERIFIED`. The real
discriminator is the **backtick**: prose mentions wrap the marker in a code span.

```
grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -v '`<!-- UNVERIFIED'   ->  16   real markers
grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep    '`<!-- UNVERIFIED'   ->   6   prose mentions
```

And D5's enumeration was **short by one**: it named 5 (`specs/macos-ci.md:505`, `00-overview.md:68`,
`01-tart-core.md:191`, `12:7`, `12:459`). There are **6** — the missed line is **`specs/macos-ci.md:517`**,
confirmed present in the excluded set. D5's arithmetic (22 − 5 = 17) would have enshrined a **wrong
baseline** as the number every later diff is measured against.

- **Resolution:** adopt **16**. `Justfile:63` now reads
  ``@grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -v '`<!-- UNVERIFIED' || echo "  none"``
- **Soundness re-checked, not inherited.** Zero false positives (all 16 kept lines carry a real marker)
  and zero false negatives (no excluded line carries a bare marker). **Sound today.**
- **But fragile** → **OQ-05**: a line carrying a real marker *and* a backticked mention would be
  silently dropped. *A budget you can pay down by editing punctuation is not a budget.*
- 📚 **synth must record the D5 retraction in `11-sources.md`**, next to G10 and G14.
- **Owner:** 👑 lead (Justfile) + 🧪 harness (12's two prose lines) + 📚 synth (the retraction).

---

## Ground truths — status

| GT | Status | Note |
|---|---|---|
| G10 | 🔴 **RETRACTED** (pre-existing) | fabricated URL; guarded by a `must_fail` control. NEVER restore. |
| G14 | 🔴 **RETRACTED** (pre-existing) | `packer` **is** installed (1.15.4); no `just doctor` recipe. |
| D5 | 🔴 **RETRACTED → D5′** | this run. Both halves false; enumeration short by one. |
| G14′ | 🟢 upheld | `tart 2.32.1 · packer 1.15.4 · lychee 0.22.0 · cirrus · utmctl · just · uv · gh` all present. |
| G19 | 🟢 upheld | `/packer/integrations/**` absent from sitemap, returns **200** (capture lines 87, 218). Never refute a page you have not fetched. |
| G1–G9, G11–G13, G15–G18 | ⚪ **to be attacked** | assigned below. Default to refuted. |

**Assignments.** G1/G2/G3 → 🍎 tart-core + 🏭 tart-ci · G4 (dollar figures — **highest-risk numbers in
the repo**; a human signs off) → 🏭 tart-ci · G5/G6/G7/G18 → 🖥 utm · G8 → 🍎 tart-core · G9/G11/G12 →
🧪 harness · G13 → 🧪 harness (**must stay `<!-- UNVERIFIED -->`**, OQ-02) · G15/G16/G17 → 🔐 secrets ·
G19 → 🍎 tart-core (**carve-out: do not refute by grepping the sitemap**).

---

## Per-file coverage — 00 through 13

| File | Owner | Cross-auditor | State |
|---|---|---|---|
| `00-overview.md` | 📚 synth | 🔬 ledger | barrier |
| `01-tart-core.md` | 🍎 tart-core | 🔐 secrets | dispatched |
| `02-packer-tart-builder.md` | 🍎 tart-core | 🔐 secrets | dispatched |
| `03-tart-ci-and-orchard.md` | 🏭 tart-ci | 🧪 harness | dispatched |
| `04-tart-licensing-risk.md` | 🏭 tart-ci | 🧪 harness | dispatched |
| `05-utm-automation.md` | 🖥 utm | 🍎 tart-core | dispatched |
| `06-utm-macos-guest.md` | 🖥 utm | 🍎 tart-core | dispatched |
| `07-utm-settings-appendix.md` | 🖥 utm | 🍎 tart-core | dispatched |
| `08-dotfiles-test-harness.md` | 🧪 harness | 🖥 utm | dispatched |
| `09-dotfiles-under-test.md` | 🧪 harness | 🖥 utm | dispatched |
| `10-tart-vs-utm-adr.md` | 📚 synth | 🔬 ledger | barrier |
| `11-sources.md` | 📚 synth | 🔬 ledger | barrier |
| `12-tooling-and-agent-loop.md` | 🧪 harness | 🖥 utm | dispatched |
| `13-build-secrets.md` | 🔐 secrets | 🏭 tart-ci | dispatched |
| `specs/macos-ci.md` | 📚 synth | 🔬 ledger | barrier — **PLAN-FORMAT CONTRACT; conforms today, do not regress** |
| `.team/claims.jsonl` | 🔬 ledger | 📚 synth | dispatched |

---

## CONFLICTS (agents append below their own role heading)

### 🔬 ledger

**Ledger delta: 50 → 63 claims, `just verify-claims` exit 0, `just check` exit 0. Markers unchanged at 16.**
Merged `.team/proposed/lead.jsonl` (4/4 dry-run green) and `.team/proposed/ledger.jsonl` (9/9 dry-run
green). Zero duplicate `id`s, zero records missing `file`. **Nothing rejected, nothing refuted on merge.**

#### The two invariants — enforced and re-checked

**(a) All six `must_fail` controls intact and still failing their evidence** (i.e. passing inverted).
Verified mechanically from `verify_claims.py --json`, not by eye:
`CONTROL-utm-settings-apple-devices-is-fabricated` · `CONTROL-disposable-is-not-apple-backend` ·
`CONTROL-tart-doc-index-oracle` · `CONTROL-tart-cirrus-page-has-no-sshpass` ·
`packer-sensitive-hides-secret` · `packer-sensitive-hides-secret-under-debug-log`.
(`grep -c must_fail` returns **7**; the 7th hit is the *prose* of
`CONTROL-packer-debug-log-prints-plain-literals`. There are exactly **6** `"must_fail": true` records.)

**(b) No control is vacuous.** I ran each probe's argv+env myself rather than trusting the pairing:

```
$ packer inspect tests/fixtures/packer-sensitive          -> 136 bytes; var.pub: "plain_FIXTURE_CONTROL"; var.sec: "<sensitive>"
$ PACKER_LOG=1 packer inspect tests/fixtures/packer-sensitive -> 981 bytes; 2x plain_FIXTURE_CONTROL; 2x <sensitive>; 0x ghp_FIXTURE_SENTINEL
```

Both controls assert a literal the **same** argv+env genuinely prints, and both commands produce
non-empty output. The negative probes are therefore falsifiable. **Neither pair is vacuous.**

#### 🔴 SOUNDNESS BUG IN `tools/verify_claims.py` — found, reproduced, FIXED

`CONTROL-12-line-607-does-not-exist` is sound **as written**: `check_line` returns a *plain* `False`
(`"line 607 out of range (file has 535)"`) for an out-of-range line, with no `UNREACHABLE:`/`STRUCTURE:`
prefix, so `must_fail` correctly inverts it. I confirmed that in the source before accepting the lead's
claim, as instructed.

**But the control had a second, unguarded failure path.** `_read()` raising `FileNotFoundError` returned
`f"missing: {e}"` — also a *plain* failure. `must_fail` inverted that too. So **deleting a control's
target file turned the control green.** Reproduced against a scratch ledger:

```
{"id":"HAZARD-missing-file","kind":"file-line","must_fail":true,"target":"specs/does-not-exist.md","line":607,...}
   before:  [PASS] HAZARD-missing-file   1/1 claims verified   EXIT=0     <-- green, for the wrong reason
   after:   [FAIL] HAZARD-missing-file   UNREACHABLE: missing file: ...   EXIT=3
```

An absent target is not evidence about the claim — exactly the reason `UNREACHABLE:` and `STRUCTURE:`
exist. Fixed by prefixing that path `UNREACHABLE:`, so `must_fail` can never invert it. This is a
*bug fix to prefix semantics*, **not a new evidence kind**; no claim's verdict changed (63/63 before and
after), `uvx ruff check` clean. Pinned by the new claim `verify-claims-missing-file-is-unreachable`.

The pairing already mitigated it — `oq02-vnc-marker-pinned-at-12-340` targets the same file and would
have failed loudly. The *pair* was sound; the *control alone* was not. That is the vacuous-control
pattern wearing a different hat.

#### ⚠️ A SECOND G19-CLASS SCOPE EXCEPTION — the tart index does not cover `/blog/<post>`

My own sweep script flagged two URLs in `11-sources.md` as `ABSENT -> FABRICATED`:

```
https://tart.run/blog/2023/02/11/changing-tart-license/                                       -> HTTP 200
https://tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/  -> HTTP 200
```

**Both are real.** The tart search index contains `/blog/`, `/blog/archive/{2023,2024,2025}/` and
`/blog/category/{announcement,orchard}/` — and **zero** `/blog/YYYY/MM/DD/` posts. The index does not
cover that prefix, so absence there is evidence of nothing. I fetched before refuting; the verdict is
**retracted**.

This is G19 with a different URL, and it is **more dangerous than G19**, because the 2025-10-27 press
release is the *sole source* for G4's "enforcement is not theoretical" claim — the highest-risk,
human-sign-off item in the repo. A future agent applying "absence from the tart index proves fabrication"
would retract the licensing enforcement evidence with total confidence.

**Rule for the ledger, now binding: `doc-index`/`doc-contains` with `site: "tart"` are valid ONLY for the
20 documentation pages. Never for `/blog/<post>`.** All three existing tart `doc-index` claims
(`/integrations/cirrus-cli`, `/faq/`, and the `/integrations/sshpass` control) sit inside the covered
prefixes, so **no current claim is wrong**. → 👑 lead: this belongs in `CLAUDE.md` next to the G19
writeup. → 📚 synth: and in `11-sources.md`. See **OQ-26** for the missing evidence kind.

#### 🟡 THE BRIEF'S THIRD FALSE LINE NUMBER (after D5 and `rename-tab`)

D2 says spec 12 documents the phantom recipes at `12-tooling-and-agent-loop.md:200-202`. Re-derived:

```
$ sed -n '200,203p' specs/macos-ci/12-tooling-and-agent-loop.md
200: |---|---|                                                     <- the table rule
201: | `build [IMAGE]` | Packer build the golden image via the OCI lane. |
202: | `build-ipsw VERSION` | Packer build from a pinned IPSW. Verifies `sha256` first. |
203: | `images` | Print `macos-versions.toml` alongside `tart list`. |
```

The rows are **201-203**, not 200-202: line 200 is the table rule and `images` at 203 falls outside the
brief's range entirely. The backlog already told 🧪 harness to re-derive rather than inherit — **it was
right to.** Pinned by `d2-spec12-201-documents-nonexistent-build-recipe` and
`d2-justfile-has-no-build-ipsw-recipe`. → 🧪 harness.

#### 🟡 OQ-06's stated derivation of the baseline "16" actually yields 17

OQ-06 says *"`wc -l` on the captured output is how this run derived '16'."* It does not:

```
$ just unverified-count | wc -l                 -> 17
$ just unverified-count | grep -c 'UNVERIFIED'  -> 17
$ just unverified-count | head -1               -> 🕵️  <!-- UNVERIFIED --> markers by file:
```

The recipe's **own header line contains the literal `UNVERIFIED`**, so any naive `wc -l` or
`grep -c UNVERIFIED` over its output over-counts by exactly one. The number **16 is correct**
(`grep -rn 'UNVERIFIED' specs/ --include='*.md' | grep -vc '`<!-- UNVERIFIED'` → 16); only the described
method is off by one. I hit this myself and briefly believed the budget had drifted. It sharpens OQ-06:
a budget whose own header pollutes its own count is a budget measured by attention. → 👑 lead.

#### 🟡 The G10 gloss is imprecise: the path was TRUNCATED, not conjured

The brief and `CLAUDE.md` say `settings-apple/devices/` *"does not exist and never did. It was
fabricated."* Evidence:

```
https://docs.getutm.app/settings-apple/devices/         -> 404, ABSENT from the 78-page index
https://docs.getutm.app/settings-apple/devices/devices/ -> 200, IN the index   (title: "Devices")
https://docs.getutm.app/settings-apple/devices/{display,network,serial}/ -> in the index
```

`/settings-apple/devices/` is a real **section** whose index page sits one segment deeper — the
Just-the-Docs pattern also seen at `/settings-apple/settings-apple/` and `/settings-qemu/drive/drive/`.
The bare path 404s and is absent from the index, so **`CONTROL-utm-settings-apple-devices-is-fabricated`
is untouched, unweakened, and still correct**: its *evidence* (absence from the index) holds. Only the
provenance gloss ("never existed", "fabricated") overstates — a truncated URL is the more parsimonious
account, and `11-sources.md:171-176` already gets this exactly right ("a **malformed path**").
**No claim changed.** Reported because the brief, not the spec, is the thing that is wrong. → 👑 lead.

---

### 🔬 ledger — CROSS-AUDIT of 📚 synth (`00`, `10`, `11`, `specs/macos-ci.md`)

Red-team posture, default-to-refuted, G19 carve-out honoured (nothing refuted unfetched).

**What survived a genuine refutation attempt — synth's numbers are unusually good:**

| Claim | Where | Verdict |
|---|---|---|
| `203` pages under `/packer/docs`, `337` total `/packer/*`, `0` under `/packer/integrations` | `11:51-54` | ✅ exact, re-run today |
| tart-builder integrations page returns 200 despite sitemap absence (**G19**) | `11:32` | ✅ `curl` → `200`; `.web-docs/components/builder/tart/README.md` present in the clone |
| `docs.getutm.app` publishes **78 pages**; **39 of 78** cited | `11:223,230` | ✅ its own embedded script reproduces `39 of 78` verbatim |
| three local clones pinned at `c10d611` / `cd2d1c6` / `270dc24` | `11:202-204` | ✅ all three match `HEAD` exactly |
| Settings(Apple) quote: *"…less mature than QEMU. It is the only way to run macOS virtualized on Apple Silicon."* | `11:122` | ✅ both sentences found verbatim in the index |
| tart FAQ: *"Local images that you can run are stored in `~/.tart/vms/`"* | `11:155` | ✅ found |
| **G4 licensing figures** (Free 100 cores / 4 Orchard Workers; Gold $12,000/yr; Platinum $36,000/yr) | `10:74-75` | ✅ **upheld**, exact against `tart.run/licensing` |
| `skip_clean` defaults to `false` | `11:150` | ✅ page states *"This defaults to false"* |

**CONFLICT L1 — `00-overview.md:52` restates RETRACTED G10 as fact.** 🔴
> `| 07 | 07-utm-settings-appendix.md | utm | Thin settings-page index; 4 pruned dead URLs (G10) |`

There are no dead URLs. `07-utm-settings-appendix.md:36` is literally headed **"## Dead links — none"**,
and `11-sources.md:158-194` carries the full G10 retraction. **Every downstream file is fixed; the one
file a newcomer reads first is not.** The G10 residue survives in the orientation doc. → 📚 synth.

**CONFLICT L2 — `00-overview.md:56` invents a `[404]` grade that `11-sources.md` explicitly does not have.** 🔴
> `| 11 | 11-sources.md | synth | Every source URL, grouped, graded meaty/thin/404/cited-as-exclusion. |`

`11-sources.md:6-14` defines exactly three grades — `[meaty]`, `[thin]`, `[cited-as-exclusion]` — and
states *"There is no `[404]` grade because nothing is dead."* A direct cross-file contradiction between
two files **synth owns**. → 📚 synth.

**CONFLICT L3 — `11-sources.md:150` attributes to Packer's docs a default the page never states.** 🟡
The row claims the shell-provisioner page gave us *"the two defaults the whole design rests on:
`use_env_var_file` (false …) and `skip_clean` (false …)"*. Fetched and searched the page:

- `skip_clean` — *"This defaults to false (clean scripts from the system)."* ✅ stated.
- `expect_disconnect` — *"Defaults to false."* ✅ stated (shows the page **does** state defaults when it means to).
- `use_env_var_file` — **no default is ever stated.** The page says only *"If true, Packer will write your
  environment variables to a tempfile…"* and *"unless the user has set `use_env_var_file: true`"*.

The default is a **strong inference** from the `execute_command` branch, not a documented fact. The design
is safe regardless — `13-build-secrets.md` sets the field *explicitly* — but 11 presents inference as
citation, which is the precise sin this run exists to catch. Cannot be settled as a ledger claim: there is
no HashiCorp doc oracle (see **OQ-24**, **OQ-26**). → 📚 synth: reword, or mark `<!-- UNVERIFIED -->` citing OQ-24.

**CONFLICT L4 — `11-sources.md:13` and `:178`: the "47/47 URLs return 200" count is stale and unverifiable.** 🟡
The file cites **70 distinct markdown-link URLs** today (`grep -ohE '\]\(https?://[^)]+\)' | sort -u | wc -l`).
"47" refers to the URLs *supplied by the original research brief* — a list that is not on disk, so the
number can be neither verified nor disproved from this repo. Meanwhile `just link-check` (lychee, fragments
included) already proves the stronger, live property over **all** of them, and is green. → 📚 synth:
replace the frozen count with a pointer to `just link-check`, or mark it. See **OQ-25**.

**CONFLICT L5 — `10-tart-vs-utm-adr.md:75` "Diamond custom" is incomplete, not wrong.** 🟢 minor
`tart.run/licensing` states: *"a custom Diamond Tier License is required, which costs **$12 per CPU core
per year** and gives the ability to run unlimited Orchard Workers."* The ADR's parenthetical
`(Gold $12K/yr, Platinum $36K/yr, Diamond custom)` drops the per-core rate that the brief's G4 carries.
Also worth noting: the licensing page is **internally inconsistent**, saying *"4 hosts for Orchard"* in one
sentence and *"4 Orchard Workers"* in another. → 📚 synth (and 🏭 tart-ci owns G4).

**Note — `00-overview.md:67` calls this a "docs-only" pass and never mentions the ledger.** 🟢 minor
The overview points a newcomer only at *"inline citations and `<!-- UNVERIFIED -->` markers"*. The
repo's actual epistemics now run through `.team/claims.jsonl` + `just check`, which execute `packer
inspect`, `git config`, `gh auth token` and `tart --help`. The orientation file is one release behind its
own truth gate. → 📚 synth.

**D3 re-confirmed independently** (`sed -n '58p' specs/macos-ci/00-overview.md` → owner `harness`; roster
says `secrets`). → 📚 synth.


---

### 🔬 ledger — LEDGER-MERGE RESULT + invariant (b) enforcement

**Merged all five auditors. `just check` → EXIT 0, `237/237 claims verified`, 0 FAIL lines.**

| source | claims | dry-run |
|---|---|---|
| baseline `claims.jsonl` | 50 | — |
| `lead.jsonl` | 4 | 4/4 |
| `ledger.jsonl` (mine) | 9 | 9/9 |
| `tart-core.jsonl` | 44 | 44/44 |
| `tart-ci.jsonl` | 34 | 34/34 |
| `utm.jsonl` | 35 | 35/35 |
| `harness.jsonl` | 43 | 43/43 |
| `secrets.jsonl` | 15 | 15/15 |
| ledger repairs + hardening | +4 −1 | — |
| **total** | **237** | **237/237** |

**Nothing rejected. One id deduped:** 🧪 harness and I independently proposed
`oq02-vnc-marker-pinned-at-12-359` with **byte-identical** evidence (same kind/target/line/expect).
Convergent derivation, not a conflict. Kept one.

#### 🔴 CONFLICT L6 — `CONTROL-git-grep-c-emits-colon-when-present` is VACUOUS. Proven, not argued. → 🧪 harness

Invariant (b) says every negative `must_fail` `cli-help` probe ships a positive control on the **same
argv+env**. Three of harness's probes cannot: `git grep -c <absent-term>` emits **zero bytes** on a true
negative, so no same-argv command can ever print anything. Their substitute — same repo, a pattern that
*is* present — is the right shape. **The chosen literal is not.** Both probe and control use `expect: ":"`,
and git's own diagnostic contains a colon:

```
$ git -C /nonexistent-repo grep -c stdinIsATTY
fatal: cannot change to '/nonexistent-repo': No such file or directory
```

Executed against a scratch ledger, not reasoned about:

```
[PASS] VACUITY-control-against-broken-repo     expect=":"                      <-- PASSES on a repo that does not exist
[FAIL] VACUITY-probe-against-broken-repo       expect=":" must_fail            <-- probe fails loudly (good)
[FAIL] VACUITY-strengthened-control            expect=".chezmoi.yaml.tmpl:"    <-- correctly refuses
```

**The control does not prove what it claims** ("`git grep -c` in this tree DOES emit `path:count`"). It
proves only that *some* output containing a colon appeared — which a `fatal:` line satisfies.

**The pair is safe today, and safe by accident.** A broken repo path turns the gate red only because the
*probe* also keys on `":"` and inverts on it. Strengthen the probe's literal (the obvious "improvement")
and the control goes green on a nonexistent repo while the probe does too — a silent false green on
`no-xcode-select-in-zsh-dotfiles-tracked`, `no-ansible-in-zsh-dotfiles-tracked`, and
`prep-repo-has-no-ansible-playbook`, three of G9/G12's load-bearing negatives.

**Fixed additively, without touching harness's records:** two new controls assert a real `path:count`
token that no `fatal:` line can contain —
`CONTROL-git-grep-emits-real-path-count-token` (`home/.chezmoi.yaml.tmpl:`) and
`CONTROL-prep-git-grep-emits-real-path-count-token` (`.github/dependabot.yml:`). Both PASS.
→ 🧪 harness: retire the `":"` controls, or adopt the discriminating literals.

**And a defect in the brief's own rule.** Invariant (b) is written for the `packer inspect` shape, where
the same command prints a variable table regardless of the claim. It **does not generalize** to a
`grep -c`-shaped probe, where a true negative implies empty output and a same-argv control is a logical
impossibility. The rule needs a second clause: *when a true negative implies no output, the control must
run the same command **shape** against the same substrate with a pattern known to match, and must assert a
literal that the command's **error** paths cannot produce.* → 👑 lead / the next brief.

#### Honesty budget: 16 → 15, and the drop is LEGITIMATE

🍎 tart-core deleted the sole real marker in `01-tart-core.md:68` (exact ghcr.io image path/tag syntax).
Per `_RULES.md`, a marker may only leave the budget against a **passing** claim. It did:
`tart-quickstart-lists-sequoia-xcode-image` (`doc-contains`) explicitly says *"RETIRES the
`<!-- UNVERIFIED -->` marker formerly at 01:68"*, and it passes.

**One gap, closed.** The replacement prose asserts `ghcr.io/cirruslabs/macos-monterey-xcode:15`, but their
claim pins `macos-sequoia-xcode:latest` — a different image and a *numeric* tag. I verified the new string
independently against tart's quick-start index (it is listed verbatim) and added
`tart-quickstart-lists-monterey-xcode-15` so the retired marker's replacement sentence is itself backed.
**Verdict: not a silent paydown.** The one remaining `UNVERIFIED` string in `01` is the backticked prose
mention at `:222`, correctly excluded by D5's discriminator.

#### 🟡 `CONTROL-12-line-607-does-not-exist` is drifting toward accidental validity

`12-tooling-and-agent-loop.md` grew **535 → 577 lines** during this run. The control asserts line 607 does
not exist. It is now **30 lines** from passing — at which point the gate goes red and the message reads
*"CONTROL PASSED — the oracle is broken"*, which would be **wrong**: nothing broke, the file merely grew.
The tripwire is correct but its failure mode is no longer theoretical. Its `claim` prose now records the
current length and says so. → 👑 lead: worth deciding whether a length-pinned control is the right shape.

### 🍎 tart-core

**Proposals:** `.team/proposed/tart-core.jsonl` — **44 claims, dry-run 44/44 PASS, exit 0.**
The negative probes were **falsification-tested** (mutants asserting a present string, and a missing
binary, all correctly FAIL; `UNREACHABLE` is not inverted). Marker budget in my files **3 → 2**: two
retired against passing claims, one added citing OQ-15. Repo total **16 → 15**.

#### 🟢 GATE — was RED at 21:39 (61/63), now **GREEN**. Resolved by 🔬 ledger, exactly as recommended.
Both failures are `file-line` claims pinned into `12-tooling-and-agent-loop.md`, which 🧪 harness has
legitimately edited (535 → **577** lines) while fixing D2. Re-derived with `sed -n`:
- `oq02-vnc-marker-pinned-at-12-340` → the marker moved to **`12:359`**.
- `d2-spec12-201-documents-nonexistent-build-recipe` → `build [IMAGE]` now lives at **`12:209`**, inside a
  ⚠️ note *recording that the bogus recipes were removed*. **The claim now asserts a defect that has been
  fixed; keeping it green would require harness to re-break the spec.** It must be re-formulated (e.g.
  `absent` over the recipe table), not merely re-pinned.

This is the predicted failure mode of pinning `file-line` claims into a file another agent owns. I touched
neither `12` nor `claims.jsonl`. — **Owner:** 🔬 ledger (re-formulate) + 👑 lead (gate).

**RESOLVED (re-verified by me at the end of my turn, not assumed).** `just check` → **exit 0, 235/235**.
🔬 ledger retired the two brittle pins and replaced them with line-independent evidence:
`oq02-vnc-marker-pinned-at-12-359` **plus** `oq02-vnc-marker-exists-regardless-of-line`, and
`d2-spec12-no-longer-documents-build-recipe` **plus** `d2-spec12-carries-the-phantom-recipe-retraction`.
All **44** of my proposed claims are merged. The lesson survives the fix: *a `file-line` claim is a
citation, and a citation into someone else's live file is a citation into a moving target.*

#### 🎁 Note to 🧪 harness — two of `08`'s markers are now retirable against **passing** claims
`08:107` (*"exact headless-run flag spelling — cross-check against 01-tart-core.md"*) and `08:114`
(*"exact `--dir` mount syntax — cross-check against 01-tart-core.md"*) both defer to `01`. Both are now
settled from `tart run --help` (tart 2.32.1) and backed by merged ledger claims: `tart-has-no-graphics`
(pre-existing) and **`tart-run-has-dir-flag`** (mine, `expect: "--dir <[name:]path[:options]>"`). The
grammar is `[name:]path[:options]`, options are comma-separated, `ro` and `tag=<TAG>` are the documented
ones, and macOS guests auto-mount under `/Volumes/My Shared Files`. Retiring those two markers would drop
the honesty budget **15 → 13** for the right reason: the claims got verified.

#### 🔴 G13 — PARTIALLY RETRACTED. `vnc_port_min` / `vnc_port_max` **do not exist.**
The brief's G13: *"Packer's tart builder drives `boot_command` over this same channel (`disable_vnc`,
`vnc_port_min/max`)."* `disable_vnc` is real. **The two port fields are not.** Zero hits in the upstream
field reference, in `.web-docs/`, and in `builder/tart/builder.hcl2spec.go` — the **generated spec that
enumerates every field the builder accepts**. The builder's whole VNC surface is `disable_vnc` +
`boot_key_interval`.

**`12-tooling-and-agent-loop.md:330` repeats the error and cites `02` as its authority — but `02` never
claimed those fields.** A circular citation to a field that does not exist. (Re-derived with `sed -n '330p'`.)

Four claims proposed, each with a positive control so `absent` cannot pass on an emptied or renamed file:
`g13-packer-tart-webdocs-has-no-vnc-port-fields`, `g13-packer-tart-hcl2spec-has-no-vnc-port-fields`, and
their two `CONTROL-…-documents-disable-vnc` partners.
— **Owner:** 🧪 harness (fix `12:330`) · 📚 synth (record the retraction in `11-sources.md`).

#### 🟡 `01:156` was WRONG — the prune sentence inverted its source. FIXED.
Spec said *"Default cap: **100 GB**, adjustable with `--prune-limit`."* The FAQ says `tart clone` *"limits
this automatic pruning to 100 GB by default **to avoid removing too many cached items**"* — the 100 GB
bounds **how much a prune reclaims**, not how large the cache may grow. `tart clone --help` agrees. The flag
exists **only on `tart clone`** (absent from `tart pull --help` and `tart run --help`).
`tart prune --space-budget` *is* a size budget. Paired: `tart-clone-has-prune-limit-flag` (cli-help, naming
its own refutation) ↔ `tart-faq-prune-limit-bounds-what-is-reclaimed` (doc-contains).

#### 🟡 `01`'s keychain workaround was TRUNCATED — following it verbatim still fails to boot. FIXED.
`01` published one command (`security create-keychain`). The FAQ publishes **three** (`create-keychain`,
`unlock-keychain`, `login-keychain -s`). **Creating a keychain neither unlocks it nor makes it the login
keychain**, so `01`'s documented mitigation for the macOS 15+ boot failure did not mitigate it.

#### 🟡 `01`'s core-CLI table omitted **`tart exec`**. FIXED.
`tart exec` exists in 2.32.1 and *"Requires Tart Guest Agent running in a guest VM."* It is the direct
counterpart to `utmctl exec`, which Apple-backend UTM macOS guests structurally cannot provide (G18) — the
sharpest instance of the asymmetry `01` argues for, and it was missing. `tart exec --help` also states *"all
non-vanilla Cirrus Labs VM images already have the Tart Guest Agent installed,"* independently confirming
`01`'s vanilla-vs-base claim.

#### 🟢 `02:73` `pull_concurrency` SETTLED from source — marker retired, not deleted.
Upstream really does annotate it `(boolean)` **and** say *"Default is 4"* in the same sentence. The plugin's
source settles it: `PullConcurrency uint16` (`builder.go:36`), `Type: cty.Number` (`builder.hcl2spec.go:190`),
forwarded to `tart clone --concurrency %d` (`step_clone_vm.go:24`) — all three re-derived with `sed -n`. It
is a **count**; the `(boolean)` is a live upstream docs bug, now recorded rather than silently "corrected".

#### 🟡 `02:88` omitted a constraint that **scopes OQ-01**.
The field reference: *"`disk_format` … **Only applies when using `from_ipsw` and `from_iso`.**"* `02`'s
golden-image sketch builds from `vm_base_name`, where `disk_format` is **inert**. So OQ-01's question — does
`asif` preserve deleted-secret residue? — **cannot arise on the clone-from-`ghcr.io` path this harness
actually takes.** 🔐 secrets should know this before spending a VM boot on it.

#### 🔴 NEW HAZARD — `headless = false` may not work at all. → **OQ-15**, marker added.
`packer-plugin-tart` v1.21.0 emits `--graphics` when `headless = false` (`step_run.go:43`). **`tart run
--help` (2.32.1) advertises no `--graphics` option.** Settling it needs `tart run`, which scope forbids. The
docs advise disabling `headless` *to debug `boot_command`* — so the build may break precisely when someone is
already debugging.

#### ⚪ G19 upheld; the brief's number has drifted **337 → 365**.
`0` of **365** `/packer/*` sitemap entries sit under `/packer/integrations` (the brief says 337), and the Tart
builder page returns **200** (fetched, per the carve-out — never refuted by grepping the sitemap). Encoded as
a `must_fail` negative probe **plus** a positive control on the same `argv`
(`g19-packer-integrations-absent-from-hashicorp-sitemap` ↔ `CONTROL-hashicorp-sitemap-lists-packer-docs`),
because *"no `/packer/integrations` in the sitemap"* is equally satisfied by **curl returning nothing**.

#### 🟢 Ground truths I attacked and could **not** break
- **G8 — upheld in all four parts** from `tart.run/faq/` + `quick-start/`: the macOS 15+ unlocked-
  `login.keychain` requirement (the FAQ calls it *"undocumented"*); nested virt = **M3/M4 + macOS 15+ + Linux
  guests only**; prebuilt images span macOS 12–26; creds `admin`/`admin` are **public and documented** →
  **never mark them `sensitive`** (G16: masking is value-based, so it would rewrite every `admin` in every log).
- **G3 — upheld.** `packer-plugin-tart` ships exactly one builder (`builder/tart`, `RegisterBuilder("cli")` →
  the `tart-cli` source type) and the string `utm` appears nowhere in the repo.
- **`01`'s two `file:line` citations survived re-derivation exactly** — `vanilla-tahoe.pkr.hcl:20-21`
  (`ssh_password`/`ssh_username = "admin"`) and `base.pkr.hcl:167`
  (`brew install cirruslabs/cli/tart-guest-agent`). The brief said to treat every line number as a hostile
  witness; these two are honest.
- **`01`'s repo-move claim is true**: `cirruslabs/tart` → `openai/tart` and `cirruslabs/tart-guest-agent` →
  `openai/tart-guest-agent`, both HTTP **301**, while `tart run --help` still prints the `cirruslabs` URL.
  **`04-tart-licensing-risk.md` still does not account for the ownership move.** → 🏭 tart-ci.
- **G1 NOT verified by me.** I never queried a Terraform registry; I confirmed only the *Packer* half (G3).
  **Do not read my G3 result as evidence for G1.** → 🏭 tart-ci.

---

### 🍎 tart-core — CROSS-AUDIT of 🖥 utm (`05`, `06`, `07`)

I tried to refute these files and **mostly failed**, which I report as a result rather than pad with
manufactured findings. All **33** distinct `docs.getutm.app` paths cited across `05`/`06`/`07` are in the
78-page index *and* **all 33 return HTTP 200** — fetched individually, not assumed. All 12 of `05`'s quoted
sentences reproduce against the index. `05`'s negative claim that `/advanced/remote-control` *"names no
backend at all"* is **true**: `qemu`, `apple` and `backend` are each absent from its 3,758 characters.
`settings-apple/devices/` **really does 404** (fetched) while `settings-apple/devices/devices/` returns 200 —
the G10 control is sound and the two are genuinely different pages. Both "plausible Apple-side"
port-forwarding URLs 404, so `07`'s upstream-nav-bug analysis holds. Four defects follow.

#### 🔴 C1 — `06:201`: the **Clipboard Sharing** gate is `macOS 13+`, not `—`.
`06` §9 opens by declaring *"the label in the source page is the minimum guest release."* The live page
(fetched with `curl`; `docs.getutm.app` 403s WebFetch) reads:
> `macOS 13+ Clipboard Sharing — On Linux guests booting from UEFI, install spice-vdagent…`

Every other row's badge matches (Sound/Keyboard/Pointer `macOS 12+`; Trackpad/Rosetta `macOS 13+`; Balloon and
Entropy genuinely unbadged). Only Clipboard Sharing is recorded `—`. **The table contradicts the convention
the section states one paragraph earlier.** — **Owner:** 🖥 utm.

#### 🟡 C2 — `06:199`: the Trackpad cell is **not a quote**, in a column headed *"What the source says."*
Spec: *"requires **a** Ventura or higher guest"*. Page: **`Requires Ventura or higher guest.`** (no article).
Demonstrated, not asserted: a `doc-contains` probe for the spec's phrasing **FAILS**; for the page's exact
string it passes. Any ledger claim written from `06`'s wording is dead on arrival. — **Owner:** 🖥 utm — use
the exact upstream string.

#### 🟡 C3 — `07:38-39`: the arithmetic is wrong (the substance is right).
> *"Every UTM docs URL used by `05`, `06` and `07` returns HTTP 200 — **all 32 of them** … and all **20
> distinct page paths** are present in UTM's own 78-page search index."*

Measured: **55** URL occurrences and **33** distinct page paths (05→10, 06→12, 07→18). Neither 32 nor 20 is
any of these. The *claim* is true — I fetched all 33 and every one returned 200 — but the file whose job is to
be the audit trail should not carry a count nobody can reproduce. — **Owner:** 🖥 utm.

#### 🟡 C4 — `05:277` is broader than its own evidence, and collides with the verifier's side-effect promise.
`05` asserts *"**Invoking `utmctl`** launches UTM.app if it is not already running,"* but the evidence it cites
used **`utmctl list`** — a VM-acting subcommand. That does **not** establish that `utmctl start --help` (pure
argument-parser output) launches anything. This matters: `.team/claims.jsonl` runs `utmctl exec --help` and
`utmctl start --help` on **every `just check`**, while `tools/verify_claims.py`'s docstring promises the
verifier is *"deliberately side-effect-free"* — a promise `05:280` repeats. Both cannot hold if `--help`
dispatches an Apple Event.

I could not settle it read-only: UTM.app has been up since **19:22:06** (`ps -eo lstart`, PID 366), over two
hours before my `just check` at 21:39:43 — so its being up proves nothing — and quitting it is host mutation.
Suggested fix, costing nothing: narrow the sentence to *"invoking a `utmctl` subcommand that acts on a VM."*
— **Owner:** 🖥 utm + 🔬 ledger.

#### ⚪ C5 — informational, not a defect: `05`/`07` cite four claim ids that are **only proposed**.
`utm-app-version-is-4-7-5`, `utmctl-usb-group-has-no-debug-flag`, `utmctl-usb-leaf-does-have-debug-flag` and
`utm-no-tso-toggle-on-apple-virtualization` live in `.team/proposed/utm.jsonl`, not in `.team/claims.jsonl`.
Legitimate in-flight state — **but if 🔬 ledger rejects any, a spec is left citing a ledger claim that does not
exist**: the decorated-citation failure mode, one level up. (I independently confirmed UTM.app **4.7.5** from
`Info.plist`'s `CFBundleShortVersionString` — no Apple Event required.) — **Owner:** 🔬 ledger, at merge.

> **Method note for 🔬 ledger.** `grep '"id":"x"' claims.jsonl` is an **unreliable** membership test: the
> ledger's JSON writes `"id": "x"` *with a space*, so that grep silently returns nothing and reads as
> "fabricated". I nearly filed four false fabrication reports on the strength of it, and caught it only because
> one of the four was a claim I had already seen with my own eyes. **Parse the JSON.** A tool that answers
> "absent" when it means "my pattern did not match" is the G10 failure wearing a different mask.

### 🏭 tart-ci

**Summary: `04` — the file a human signs off on — shipped with ZERO backing claims and one fabricated
quotation. G4's numbers are all CORRECT and now carry 10 claims. 34 proposed, 34 dry-run PASS (exit 0).**

#### 🔴 RETRACTION 1 — `04:36-37` attributed an INVENTED SENTENCE to `tart.run/licensing/`
`04` read: *The current summary page states this as: **"commercial use free up to 100 CPU cores (tart)."***
That sentence **has never appeared on that page, under any casing.**
```
curl -fsSL https://tart.run/licensing/   (tags stripped, casefolded)
  "commercial use free up to 100" -> ABSENT    "commercial use free" -> ABSENT
  "free up to 100"                -> ABSENT    "(tart)"              -> ABSENT
  real sentence: "organizations that exceed a certain number of server installations
                  (100 CPU cores for Tart and/or 4 hosts for Orchard) will be required to obtain a paid license."
```
The quoted string is lifted **verbatim from the master brief's own G4** (*"commercial free <=100 CPU cores
(tart)"*) and dressed as an upstream citation. **This is G10's failure mode with the polarity flipped: not
a fabricated URL, but a real URL with a fabricated sentence — precisely what `doc-contains` exists to kill,
on a page that had no `doc-contains` claim.**
- **FIXED** in `04`, retraction left visible. Guarded by `CONTROL-licensing-page-never-says-commercial-use-free`
  (`must_fail`), paired with `tart-licensing-page-exists` so a failure means *the sentence is absent*, not
  *the page is gone*.

#### 🔴 RETRACTION 2 — the `tart` doc-index oracle DOES NOT COVER `tart.run/blog/**` (OQ-08)
An unnamed **second G19-class carve-out**, aimed at `04`'s most load-bearing citations.
```
curl -sS -o /dev/null -w '%{http_code}' https://tart.run/blog/2025/10/27/press-release-...     -> 200
curl -sS -o /dev/null -w '%{http_code}' https://tart.run/blog/2023/02/11/changing-tart-license/ -> 200
tart search index: 20 pages, ZERO blog posts.  "heather meeker" / "successfully enforces" -> ABSENT

uv run tools/verify_claims.py <probe>
  [FAIL] doc-index    '/blog/2025/.../press-release-...' is not in the tart search index — fabricated or moved
  [FAIL] doc-contains STRUCTURE: page ... is not in the tart index — fabricated or moved
```
**`doc-index` calls a live HTTP-200 page "fabricated or moved."** An agent obeying *default to refuted*
would delete `04` §3's entire enforcement precedent and record a fabrication that never happened —
**G10 running backwards, on the highest-risk file in the repo.**
- **My own worker brief is unexecutable as written.** It orders *"Use `doc-contains`, not just `doc-index`"*
  for the press release. `doc-contains` reads the **search index**, never the live page
  (`tools/verify_claims.py:240-247`), so it **cannot reach any tart blog post at all**.
- **Worked around, dry-run passing:** a `cli-help` claim whose `argv` is `curl -fsSL <url>` reaches the live
  page. Five proposed. Two sharp edges found **by dry-running, not by reasoning**: (1) it greps **raw
  HTML**, so a literal split by an inline tag fails; (2) `check_contains` is a bare `in` with **no
  whitespace normalization** (unlike `doc-contains`'s `norm_text`), so a literal spanning an HTML
  **line-wrap** also fails — that is what broke `tart-2023-post-defines-server-installation` on the first
  pass. Keep curl expects short.
- **For 🔬 ledger:** `cli-help` **ignores curl's exit code**, so a network outage yields a **FAIL, not
  `UNREACHABLE:`** — a false refutation. A `url-contains` kind fixes this *and* `doc-contains`'s blind spot.
  Overlaps 🔬 ledger's OQ-11 (`http-status` kind). **Recommend one kind, not two.**
- Pinned forever by `CONTROL-tart-blog-is-outside-doc-index-domain` (`must_fail` `doc-index`).

#### 🟡 `03:97` cited a LEDGER CLAIM ID THAT DOES NOT EXIST
`03` credited the sshpass guard to `control-tart-doc-contains-oracle`.
`grep -c 'control-tart-doc-contains-oracle' .team/claims.jsonl` → **0**. The real id is
**`CONTROL-tart-cirrus-page-has-no-sshpass`**. A spec citing a nonexistent ledger id is the ledger's own
failure mode one level up: the citation *looks* re-executable and never was. **FIXED in `03`.**

#### 🟡 `03:128-130` invoked `just doctor` — the fiction G14 was retracted for
`03` said sshpass is *"deliberately not a `just doctor` requirement"* and named a *"doctor requirement
table"*. `just --summary` → `build-golden check default link-check link-check-fresh link-check-verbose
unverified-count verify-claims verify-claims-json verify-no-secrets`; `grep -in doctor Justfile` → nothing.
**G14's retracted claim survived inside a spec nobody re-checked.** FIXED. (`cirrus 1.0.0-1769788`, and
`sshpass` absent — those parts *were* true.)

#### 🟡 `03:144`'s `<!-- UNVERIFIED -->` marker gave a FALSE REASON
Marker read: *"no source page describes self-hosted Cirrus CI runner registration."* **False.**
`cirrus worker --help` → *"Persistent worker mode"*; `cirrus worker run --help` → `--token` *"pool
registration token"*, `--name` *"worker name to use when registering in the pool"*. The CLI is a source, it
is installed, and it describes registration precisely. The *conclusion* stays unverified for a **narrower,
correct** reason (**OQ-22**): whether a persistent worker may run a *custom* image under hosted Cirrus CI.
**A marker whose reason is wrong is worse than no marker — it tells the next reader the question was already
looked into.** Marker retained, reason rewritten, ledgered as `cirrus-worker-run-has-pool-registration-token`.

#### 🟢 G4 — UPHELD. Every tier number re-verified; NONE moved.
Free 100/4 · Gold $12,000 500/20 · Platinum $36,000 3,000/200 · Diamond $12/core/yr. The worker column is
independently corroborated from a **second page** (`/orchard/quick-start/`, `ORCHARD_LICENSE_TIER`).
Ten claims proposed, one per threshold. **Two precision defects fixed:**
- Diamond's Tart-core cell said **"Unlimited"**. The page grants only *"unlimited Orchard **Workers**"* and
  says nothing about a core ceiling. An **inference from per-core pricing, presented as fact**. Now *not stated*.
- Diamond's price was hedged **"~$12/core/yr"**. The page states it exactly: *"$12 per CPU core per year."*
  The tilde hedged a number that needed none.
- `04` §2's NOTE about the 2023 post's *superseded* table (Gold 100+/$12K, Platinum 500+/$36K, Diamond
  3000+) is **CONFIRMED verbatim**. It was right.
- `04` §1 quoted *"usage on personal computers … is royalty-free"*; the ellipsis silently swallowed **"and
  before reaching the 100 CPU cores limit"** — the qualifier the whole document tracks. Restored.
- `04` §1's "dummy plug" quote: substance **fully supported** (*"a Mac Mini with a HDMI Dummy Plug is
  considered a server"*) but written as a **paraphrase inside quotation marks**. My own first probe called
  it fabricated; **that probe was case-sensitive and I was wrong.** Corrected before reporting — the
  evidence beat my first read, which is the only reason this line is not itself a false retraction.

#### 🟢 G4′ — NEW, and the reason a human must look: **the counterparty changed** → **OQ-20 NEEDS-HUMAN**
`cirruslabs/tart` → **`openai/tart`**; `cirruslabs/tart-guest-agent` → `openai/tart-guest-agent`. LICENSE is
**`FSL-1.1-ALv2`**, *"Copyright 2022-2026 OpenAI"*, Apache-2.0 *"effective on the second anniversary of"*
each release. The FSL text mentions **CPU cores zero times** (`grep -ic 'cpu\|core'` → `0`), so the 100-core
Free Tier is a **tart.run tier grant, not a licence clause** — which is why nothing contradicts. Meanwhile
`tart.run/licensing/` still says Fair Source and still bills `licensing@cirruslabs.org`.
**No number moved, so this is not a cost retraction — but §3's enforcement precedent is a *Cirrus Labs*
action and the copyright is now *OpenAI*'s. Who enforces is the human's call, not an agent's.** 4 claims.

#### 🟢 G1 — UPHELD, with two corrections to how it is cited
- The maintainer's sentence is **real and verbatim**. `osy` (authorAssociation `CONTRIBUTOR`), discussion
  3618: **"There are plans for this in #3718 but that's still a long way off."** Verified via GraphQL over
  the body, all 3 comments, and their replies.
- **`utmapp/UTM#3618` is a DISCUSSION, not an issue.** `gh api repos/utmapp/UTM/issues/3618` → **404**
  (authenticated; unauth rate limit 58/60, so not throttling). `github.com/utmapp/UTM/issues/3618` returns
  200 **only because GitHub redirects** it to `/discussions/3618` (`url_effective` confirms). **The baseline
  `link-check` 200 proved the redirect, not the resource.** `05:8` and `11:100` already say "discussion" and
  link `/discussions/3618` — **correct**. The *master brief* says "issue". → 🖥 utm / 📚 synth, FYI only.
- **Do not cite the Terraform Registry search API.** `/v1/providers?q=tart`, `?q=utm`, `?q=orchard` all
  return the **identical** `hashicorp/*` top-100 — **the `q=` parameter is ignored.** I nearly filed that as
  evidence. What *is* evidence: `registry.terraform.io/v1/providers/cirruslabs/{tart,orchard}` → **404**,
  refuting the **canonical addresses only**, not all namespaces. Both ledgered with that scope named in the
  claim prose; `03` now states the limit rather than implying an exhaustive negative.

#### 🟢 G2 — UPHELD
The tonyyo11 post's only Terraform *providers* are **Jamf's** (`#terraform-provider-jamfpro`, "the new Jamf
Platform API provider"). Tart appears solely as the **VM builder** (*"With Tart, I can create disposable,
repeatable macOS VMs that enroll automatically into my Jamf environment"*). **No `tart_*`/`utm_*` resource
type appears anywhere.** The aspirational line G2 warns of is literally present: *"Tart fits perfectly into
my long-term Terraform plans."*
- **Unresolvable as stated:** the brief says *"The repo README's 'Terraform' line is aspirational"* without
  saying **which repo**. `macos-ci/README.md:12` states the **negative** (*"There is no Terraform provider
  for tart or for UTM"*) — correct, not aspirational. Neither dotfiles README mentions Terraform. Flagged,
  not guessed.

#### 🟢 Honesty budget: 16 → 15. **NOT a silent drop. Verified.**
The vanished marker is `01-tart-core.md:68` (ghcr.io image path/tag syntax) — **not my file**. 🍎 tart-core
retired it and proposed `tart-quickstart-lists-sequoia-xcode-image` (`doc-contains`, expect
`ghcr.io/cirruslabs/macos-sequoia-xcode:latest`), whose `claim` prose *names the marker it retires*.
**The budget working exactly as designed.** My two files: 2 markers before, 2 after (net 0); both now cite
an OQ (OQ-21, OQ-22).

#### 🟡 OQ NUMBER COLLISIONS — for 👑 lead to adjudicate
Concurrent appends collided: **OQ-08 ×2** (tart-ci @144, ledger @290), **OQ-09/10/11 ×3 each** (utm, ledger,
tart-ci). I renumbered mine to **OQ-20/21/22** per `_RULES.md` §6 and kept **OQ-08**, the earliest in this
append-only file. `_RULES.md`'s *"if you race, renumber yours upward"* has **no tiebreak** when three agents
race the same number at once — worth a rule fix.

#### 🟢 OQ-19 (🧪 harness's cross-audit of me) — CONFIRMED, and my controls are LIVE
Harness found a third `doc-contains` state nobody modelled: a page **in** the index with **empty** text makes
a `must_fail` control pass silently. Real. **I did not take "your pages are text-rich" on trust — I
mutation-tested both of my `must_fail` controls:** swapping each `expect` for a string the target *does*
contain flips both to `[FAIL] CONTROL PASSED — the oracle is broken`. Neither is vacuous. A third probe
confirms `/licensing/` carries real body text. And `CONTROL-tart-blog-is-outside-doc-index-domain` is
`doc-index`, which tests **path membership** and never reads body text, so the hole cannot reach it.
**Partial resolution appended inside OQ-19's block; status stays NEEDS-HUMAN — only 🔬 ledger can add the guard.**

---

### 🏭 tart-ci — CROSS-AUDIT of 🔐 secrets (`13-build-secrets.md`)

**The question I was told to ask — "is each control vacuous?" — answered by EXECUTION, not reading.**

#### 🟢 The two `must_fail`/CONTROL pairs are SOUND. Neither control is vacuous.
```
$ packer inspect tests/fixtures/packer-sensitive
  var.pub: "plain_FIXTURE_CONTROL"      <- the control literal genuinely prints
  var.sec: "<sensitive>"                <- masking is on
  exit=0 ;  ghp_FIXTURE_SENTINEL occurrences: 0
$ PACKER_LOG=1 packer inspect tests/fixtures/packer-sensitive
  980 bytes of output;  plain_FIXTURE_CONTROL x2;  ghp_FIXTURE_SENTINEL x0
```
The **deeper** vacuity test — the one the control does *not* cover — is whether the sentinel would print at
all if unmasked. It would: `fixture.pkr.hcl:18` sets `default = "ghp_FIXTURE_SENTINEL"` on the
`sensitive = true` variable, so the negative probe genuinely exercises masking rather than asserting the
absence of a string that was never there. **Both pairs are honest: same `argv`, same `env`, non-empty
output, control literal present.**

#### 🟢 G16 — UPHELD, and `13:161-163` UNDERSTATES it
Scratch fixture where a **non-sensitive** variable holds the **same value** as a sensitive one:
```
var.common_word:                "<sensitive>"                        # sensitive, value "admin"
var.twin_not_sensitive:         "<sensitive>"                        # NOT sensitive, same value -> still masked
var.unrelated_<sensitive>_user: "the <sensitive> user is <sensitive>"
```
Masking is **value-based and global**, exactly as `13` says — **and it redacts the VARIABLE NAME too**
(`unrelated_admin_user` → `unrelated_<sensitive>_user`). `13:163`'s predicted `the <sensitive> user is
<sensitive>` is reproduced verbatim. **Do not mark `ssh_password = "admin"` sensitive.** Confirms
`vanilla-tahoe.pkr.hcl:20-21` must stay plain (re-derived with `sed -n`; the `:20-21` citation is correct).

#### 🔴 CONFLICT for 🔐 secrets — D1 is STILL NOT ADDRESSED in `13`
`ls -d packer` → *No such file or directory*. `Justfile:44` invokes `packer/tart-golden-image.pkr.hcl`.
`grep -in 'absent\|does not exist\|missing\|not on disk' 13-build-secrets.md` → **no hit says the template is
absent**; `13:141-145` still presents `build-golden` as though the template were on disk. The backlog's D1
entry assigns exactly this to 🔐 secrets. **Not done.**

#### 🟡 CONFLICT for 🔐 secrets — `13:143` MISQUOTES `Justfile:43`, dropping `|| true`
```
13:143       $(gh auth token 2>/dev/null)
Justfile:43  "${HOMEBREW_GITHUB_API_TOKEN:-$(gh auth token 2>/dev/null || true)}"
```
`13:22` itself argues *"the `|| true` is load-bearing"* about the Dockerfile — then drops it from its own
quotation of this repo's Justfile. Also fenced as `make` when it is a `just` recipe.

#### 🟡 CONFLICT for 🔐 secrets — `13:15-22`'s Dockerfile block SPLICES TWO DIFFERENT `RUN` STANZAS
Cited as `zsh-dotfiles/Dockerfile:127`. Lines 127-130 are the `--mount` header, the
`HOMEBREW_GITHUB_API_TOKEN=` line, `brew --version`, and `brew install chezmoi neovim mise go`. The quoted
`brew install python@3.12 pre-commit actionlint` is at **`:137`**, inside the **second** `--mount` stanza
beginning at `:135`. The `--mount` line at `:127` is real (`grep -n` → `127`, `135`); the block as printed
exists nowhere. A composite presented as a citation.

#### 🟡 CONFLICT for 🔐 secrets — `13:3` credits the file to the WRONG OWNER
`sed -n '3p'` → `Owner: 🧪 harness.` The roster and this backlog's coverage table both say **🔐 secrets**.
Same class as **D3** (`00-overview.md:58`), which 📚 synth owns — a second instance nobody listed.

#### 🟢 Verified for 🔐 secrets (no action)
`13:66` `grep -rI HOMEBREW_GITHUB_PACKAGES_TOKEN` across both clones → **no matches**. `13:76` `Brewfile:4`
= `tap "bossjones/tap", "git@github.com:bossjones/homebrew-tap.git"` → **exact**. `13:194`
`tart.run/faq/#vm-location-on-disk` → anchor present in the index, page 200. `13:189`
`packer/docs/provisioners/shell` → 200. The two `<!-- UNVERIFIED -->` markers at `13:51`/`13:54` **must
stay** (OQ-01); nothing I ran touches a tart disk image.

### 🖥 utm

**AUDIT-OWN result: no fabricated URL survives in `05`/`06`/`07`.** All **20** distinct
`docs.getutm.app` page paths cited by my three files are present in UTM's own 78-page search index, and all
**32** distinct URLs (anchors included) return HTTP 200. **G5, G6, G7 and G18 all survived a genuine
refutation attempt** and are now backed by `doc-contains` claims quoting the pages verbatim, not by the
previous run's summary. `.team/proposed/utm.jsonl` — **35/35 dry-run PASS, exit 0**.

#### CONFLICT U-1 — `08` invokes `tart --dir`, which does not exist 🔴
`08-dotfiles-test-harness.md` writes `tart --dir` **twice** (`:74`, `:110`; re-derived with `grep -n`).

```
$ tart --help          # global options are exactly two
  --version               Show the version.
  -h, --help              Show help information.
$ tart --dir '~/x'
Error: Unknown option '--dir'
```

`--dir` is an option of the **`run` subcommand**: `tart run <vm> --dir=<[name:]path[:options]>`.
Proposed: `xaudit-08-tart-dir-is-not-a-global-flag` (`must_fail`) + `CONTROL-xaudit-08-tart-help-prints-globals`.
- **Owner:** 🧪 harness.

#### CONFLICT U-2 — `08`'s three markers cite a SIBLING SPEC as their authority 🟡
The markers at `08:72`, `08:107`, `08:114` all read *"cross-check against `01-tart-core.md`"*. **A spec is
not a source.** `tart` 2.32.1 is installed and all three are settleable from the binary:

| marker | verdict | claim |
|---|---|---|
| `:72` `tart clone` syntax | ✅ correct — `USAGE: tart clone <source-name> <new-name>` | `xaudit-08-tart-clone-syntax` |
| `:107` headless flag | ✅ correct — `--no-graphics  Don't open a UI window.` | `xaudit-08-tart-run-no-graphics` |
| `:114` `--dir` syntax | 🔴 **spec is wrong** — see U-1 | `xaudit-08-tart-dir-is-not-a-global-flag` |

`:72` and `:107` are **retirable** once ledger merges. `:114` must be **corrected**, not retired.
> The brief's line numbers for these (`:62/:97/:104/:174`) are **stale** — harness is editing live.
- **Owner:** 🧪 harness.

#### CONFLICT U-3 — `08` never names the guest-side mount path, and silently drops macOS 12 guests 🟡
`tart run --dir` defaults to the `com.apple.virtio-fs.automount` tag, which on a macOS guest auto-mounts at
**`/Volumes/My Shared Files/<name>`**. `08` says the dotfiles tree is "mounted via `tart --dir`" and never
says where the guest reads it from. The same help text adds: *"Requires host to be macOS 13.0 (Ventura) or
newer. macOS guests must be running macOS 13.0 (Ventura) or newer too."* — so the harness's mount step
**requires a Ventura+ guest**, which `08` does not state. Corroborated independently by
[tart quick-start](https://tart.run/quick-start/). Claims: `xaudit-08-tart-dir-automounts-to-shared-files`,
`xaudit-08-tart-dir-requires-ventura-guest`, `xaudit-08-tart-dir-automount-documented`.
- **Owner:** 🧪 harness.

#### CONFLICT U-4 — 👑 lead's own proposed claim ALREADY FAILS 🔴
`oq02-vnc-marker-pinned-at-12-340` does not verify against the current tree:

```
$ uv run tools/verify_claims.py .team/proposed/lead.jsonl        # TRUE EXIT = 2
[FAIL] oq02-vnc-marker-pinned-at-12-340  (file-line)
         line 340 is '`_gui_core.parse_vnc_url()` turns that line into a `VncTarget`; `gui.p',
         expected to contain '<!-- UNVERIFIED: `--vnc-experimental`'
$ grep -n 'UNVERIFIED: `--vnc-experimental`' specs/macos-ci/12-tooling-and-agent-loop.md   ->  359
$ wc -l specs/macos-ci/12-tooling-and-agent-loop.md   ->  577      (HEAD: 535)
```

harness's concurrent edits grew `12` by 42 lines and pushed the marker from `:340` to `:359` — it was at
`:349` when I first grepped, minutes earlier. **OQ-02's `**Spec:** …:340` citation is stale**, which is
Defect B's class reintroduced by ordinary editing rather than by hallucination. This will fail LEDGER-MERGE.
**A `file-line` claim that pins a marker tracks the citation, not the truth**, and rots whenever anyone
inserts a line above it. Suggest re-pinning after `12` settles, or using `file-contains` on the marker text.
- **Owner:** 👑 lead → 🔬 ledger.

#### CONFLICT U-5 — `CONTROL-12-line-607-does-not-exist` is UNSOUND, and its prose has the polarity backwards 🔴
The control claims: *"If this ever starts PASSING, the file grew past 607 lines."* **It is passing right
now**, and growth past 607 would **not** change that. `file-line` returns `ok=False` both when line 607 is
out of range *and* when line 607 exists but lacks `UNVERIFIED`; `must_fail` inverts both to PASS. Proven
with two fixtures rather than argued:

```
[PASS] SHAPE-A-577-lines-out-of-range          # today: line 607 does not exist
[PASS] SHAPE-B-700-lines-line-607-EXISTS       # the condition it says it detects -> still PASS
```

It only goes red if line 607 *exists AND contains* `UNVERIFIED`. **The sound form is `"expect": ""`** — the
empty string matches any existing line, so the evidence verifies iff line 607 exists, and `must_fail` then
means exactly *"line 607 does not exist"*. Verified:

```
[PASS] FIX-A-577-lines-line-607-absent
[FAIL] FIX-B-700-lines-line-607-EXISTS
         CONTROL PASSED — the oracle is broken; every other claim of this kind is now unreliable
```

Also: every other CONTROL in the ledger says *"its **evidence** must not verify"*. This one says
*"if this ever starts **PASSING**"*, conflating the tool's post-inversion verdict with pre-inversion
evidence. **A verifier nobody verifies is just a second thing to trust** — and this is the control written
to enforce that lesson. I did not edit `claims.jsonl` or `lead.jsonl`; the one-word fix is ledger's call.
- **Owner:** 🔬 ledger (with 👑 lead).

#### CONFLICT U-6 — `OQ-08` is claimed by two blocks and cited ambiguously by four specs 🟡
`.team/macos-ci.open-questions.md` now carries **two `## OQ-08` headings** (🏭 tart-ci at `:144`, 🔬 ledger
at `:290`). Four specs cite "OQ-08": `02:135`, `04:98`, `08:189`, `13:294`. Only `13:294` disambiguates
("🔬 ledger's OQ-08"). 🧪 harness has already renumbered its own to OQ-17/18 and flagged this. I renumbered
mine upward to **OQ-09 … OQ-12** per `_RULES.md` §6.
- **Owner:** 👑 lead (adjudicate).

#### A REFUTATION I ATTEMPTED AND FAILED — recorded because the failure is the point ⚪
`02-packer-tart-builder.md:135` marks *"whether `tart run --graphics` parses on tart 2.32.1"* unverified,
reasoning that settling it "requires invoking `tart run`, which scope forbids". `tart run --help` lists only
`--no-graphics`, and `tart run --graphics` (no VM name) returns `Missing expected argument '<name>'` rather
than `Unknown option`, which *looked* like proof the flag parses. **The control disproved me:**

```
$ tart run --zzzz-not-a-flag              -> Error: Missing expected argument '<name>'
$ tart run --graphics                     -> Error: Missing expected argument '<name>'      # identical
$ tart run --zzzz-not-a-flag no-such-vm   -> Error: the specified VM "no-such-vm" does not exist
$ tart run --graphics       no-such-vm    -> Error: the specified VM "no-such-vm" does not exist   # identical
```

`tart run` does **not** surface unknown options before the missing-argument and VM-existence checks, so its
error text carries **no information** about whether a flag parses. (The *top-level* parser does reject them:
`tart --dir` → `Unknown option`. That asymmetry is why U-1 is sound and this is not.)
**🍎 tart-core's marker at `02:135` is CORRECT and survives.** I nearly shipped a confident refutation of a
true statement — G10 running backwards — and only the control caught it. I propose **no** claim here; a
`cli-help` probe of the form `tart run <flag> <vm>` could boot a VM if the name ever existed, and the
ledger's verifier must stay side-effect-free.
- **Owner:** none. Informational, for 🍎 tart-core and 📚 synth.

#### Self-correction in a file I own ⚪
`05:263` asserted *"Every subcommand accepts the global `--debug` and `--hide`."* **False.** The two
**group** commands `usb` and `file` accept only `-h`; the globals live on the **leaf** subcommands.
Fixed in `05`, with `utmctl-usb-group-has-no-debug-flag` (`must_fail`) +
`CONTROL-utmctl-usb-help-prints-subcommands` + `utmctl-usb-leaf-does-have-debug-flag`. Also `05:14` called
[issue #3718](https://github.com/utmapp/UTM/issues/3718) "the tracked IaC-support request"; it is titled
**"Vagrant support for macOS"** (`gh issue view 3718 --repo utmapp/UTM` → `OPEN`). Corrected.
And `05:263`'s `utmctl version → 4.7.5` is now ledger-backed **without a side effect**: `utmctl version`
dispatches an Apple Event and *launches UTM.app*, so `utm-app-version-is-4-7-5` reads
`/Applications/UTM.app/Contents/Info.plist` instead.

#### Observation for the lead — the honesty budget moved, but not by me ⚪
Repo-wide markers are **16 → 14**. My three files still carry exactly **4** (`05:115`, `05:415`, `06:78`,
`07:25` — all four retained; three now cite an OQ). The drop is entirely in 🍎 tart-core's files
(`01`: 1→0, `02`: 2→1, measured against `HEAD`). Not adjudicated by me — flagging so the GATE diff is not
misread as mine.

### 🧪 harness

All 36 proposed claims dry-run **`36/36`, exit 0** (`uv run tools/verify_claims.py .team/proposed/harness.jsonl`).
Every refutation below is backed by one. Nothing here is inference.

#### C-H1 — 🔴 `08:28` FABRICATED A PACKAGE. `trash` is not in the brew prereq list.
08 says the golden image installs *"the brew prereq list from `smoke-test-docker.sh:142-157`
(`wget curl retry go trash openssl@3 readline libyaml gmp autoconf tmux`)"*.

```
$ grep -n 'trash' zsh-dotfiles/scripts/smoke-test-docker.sh
(no output — the word does not occur in the file)
$ sed -n '142,143p' zsh-dotfiles/scripts/smoke-test-docker.sh
    brew install wget curl kadwanev/brew/retry go || true
    brew install openssl@3 readline libyaml gmp autoconf tmux || true
```

Two errors in one sentence. **`trash` was invented** — it appears nowhere in the cited file (it *does*
exist in `install.sh` and `aliases.zsh`, presumably where the association came from). And the range
**`:142-157` is wrong**: the quoted ten formulae are `:142-143`; `:144-157` installs ~50 more, which the
golden image is explicitly *not* supposed to carry. `retry` is really `kadwanev/brew/retry`.
Claims: `smoke-test-never-mentions-trash`, `smoke-brew-prereq-list-line-142`, `…-line-143`.
**Status:** FIXED in 08. **Owner:** 🧪 harness.

#### C-H2 — 🔴 `09:23` and `08:221`: *"`ansible` appears exactly once"* is FALSE. It appears twice.
```
$ grep -n -i ansible zsh-dotfiles-prep/Brewfile
57:brew "ansible"
602:vscode "redhat.ansible"
```
The *conclusion* (G9 — neither repo is provisioned by Ansible) survives; the *count* does not. Both specs
state it as a load-bearing fact (*"appears exactly once … it's an installable tool"*). Fixed to `:57` **and**
`:602`. Claims: `ansible-in-prep-brewfile-line-57`, `ansible-in-prep-brewfile-line-602`.
**Status:** FIXED in 08 + 09. **Owner:** 🧪 harness.

#### C-H3 — 🟡 **G9's stated method is unusable.** *"Prove it with an `absent` claim"* would FAIL.
The harness brief (and the master brief's G9) instructs: *"NEITHER dotfiles repo uses Ansible … Prove it
with an `absent` claim."* `absent` takes **one file** and asserts a string is not in it. The string
`ansible` **is** in `zsh-dotfiles-prep/Brewfile`. A literal `absent` claim over that repo fails; narrowed
to a file that happens not to mention it, it proves nothing.

G9 is true only under the reading *"neither repo is **provisioned by** Ansible"* — a claim about
**playbooks**, not about the word. Expressed correctly it needs a `must_fail` `cli-help` over `git grep`
**plus a positive control**, exactly as `packer-sensitive-hides-secret` does, because *"no `hosts:` key in
any YAML"* is equally satisfied by *"the pathspec matched no files."* Proposed:
`prep-repo-has-no-ansible-playbook` (`must_fail`) ↔ `CONTROL-prep-grep-c-emits-colon-when-present` (same
argv **and same `*.yml`/`*.yaml` pathspec**, pattern `name:`, proving 9 tracked files match); and
`no-ansible-in-zsh-dotfiles-tracked` (`must_fail`) ↔ `CONTROL-git-grep-c-emits-colon-when-present`.
Falsifiability of the negatives was mutation-tested: swapping the pattern to one known present flips them
to `FAIL` with `CONTROL PASSED — the oracle is broken`.
**Not a spec defect — a defect in the brief's instruction.** **Owner:** 🧪 harness → 🔬 ledger.

#### C-H4 — 🔴 `08:174` cites a flag that does not exist: `sheldon lock --check`.
`sheldon` **is installed on this host, at exactly the pinned `0.6.6`**, so this was checkable all along.
```
$ sheldon --version
sheldon 0.6.6 (31c6df8f7 2022-01-29)
$ sheldon lock --help
Install the plugins sources and generate the lock file
OPTIONS:  --update  --reinstall  -h, --help
```
No `--check`. No `verify` subcommand anywhere in `sheldon --help`. And `lock`'s own one-line description
says it **installs** — the opposite of a non-mutating verify. The line already carried an
`<!-- UNVERIFIED -->` marker asking someone to *"confirm exact non-mutating flag against sheldon 0.6.6's
`--help`"*. Nobody ran the command. It takes one second.
**This is the run's thesis in miniature: the marker was honest, and still nobody checked.**
Claims: `sheldon-installed-is-the-pinned-0-6-6`, `sheldon-lock-has-no-check-flag` (`must_fail`) ↔
`CONTROL-sheldon-lock-help-prints-reinstall`, `sheldon-lock-is-mutating`. → **OQ-08 (NEEDS-HUMAN)**.
**Status:** marker RETAINED and rewritten to cite OQ-08. **Owner:** 🧪 harness.

#### C-H5 — 🔴 `09:29-41` — the bootstrap section misattributes **two** commands.
1. `09:32` — *"(`zsh-dotfiles-prep/README.md:12`, matches `docs/quickstart.md:10`)"*. It does not match.
   `README.md:12` curls `bin/zsh-dotfiles-prereq-installer`; `quickstart.md:10` curls a **different
   script**, `install.sh`, with no `-s -- --debug`. The string `prereq-installer` does not occur in
   `quickstart.md` at all.
2. `09:34-38` — the block `sh -c "$(curl -fsLS chezmoi.io/get)" -- init -R --debug -v --apply …` is
   attributed to *"what the prereq installer prints as next steps, `:1135`"*. Line 1135 actually reads
   `logn 'You are ready to run zsh-dotfiles. Run: chezmoi init -R --debug -v --apply https://github.com/bossjones/zsh-dotfiles.git"'`
   — a bare `chezmoi init`, no `curl`. The `curl … get.chezmoi.io` form is at `:1132` and it **installs**
   the chezmoi binary (`-t v2.31.1`); it does not init anything. Two different lines were welded together.

Claims: `quickstart-does-not-cite-prereq-installer`, `quickstart-line-10-curls-install-sh`,
`prereq-installer-next-steps-line-1135`, `prereq-installer-pins-chezmoi-2-31-1-line-1132`.
**Status:** FIXED in 09. **Owner:** 🧪 harness.

#### C-H6 — 🔴 `09:183` cites `smoke*` Makefile targets that do not exist.
*"`zsh-dotfiles-prep/Makefile:35-67` `smoke*` targets"*. The word `smoke` occurs **nowhere** in that
136-line Makefile. Its targets are `style`, `style-fix`, `lint-gh-actions`, `install-hooks`,
`docker-buildx`, `docker-run-test{,-debug,-bash}`, `ghcr-login`, `docker-buildx-push`,
`docker-full-pipeline`, `debian-fix-broken`, `fix`. Lines 35-67 straddle `docker-buildx` and
`docker-run-test`. The three Dockerfiles named on `09:181` **do** exist.
Claim: `prep-makefile-has-no-smoke-target`. **Status:** FIXED in 09. **Owner:** 🧪 harness.

#### C-H7 — 🟡 `09:204-208` — the tmux test cited as a model **cannot see the dotfiles' prompt**.
09 calls `test_dotfiles.py:239-270` a *"tmux-based prompt-loaded check"* and then reassures that *"most of
its **alias-content** tests"* are skipped. The cited test is not an alias test, and it is skipped too
(`:245`). Worse, `:254` spawns `env zsh -f` — **`-f` means no rcfiles** — and `:265` then sets `PS1='> '`
**by hand** before `:270` asserts `">" in pane_contents`. It asserts that tmux can echo a prompt string it
just typed. It exercises zero lines of `zsh-dotfiles`.
Claims: `test-dotfiles-tmux-prompt-test-is-skipped`, `test-dotfiles-tmux-spawns-zsh-f`.
**Status:** FIXED in 09. **Owner:** 🧪 harness.

#### C-H8 — 🟡 **G11's verbatim apply invocation is CONDITIONAL**; both specs quote it as unconditional.
```
360:    if command -v retry &> /dev/null; then
361:        retry -t 4 -- "$chezmoi_bin" init -R --debug -v --apply --force \
362:            --promptString version_manager="$VERSION_MANAGER" --source=. || chezmoi_exit_code=$?
363:    else
364:        "$chezmoi_bin" init -R --debug -v --apply --force \
365:            --promptString version_manager="$VERSION_MANAGER" --source=. || chezmoi_exit_code=$?
```
The brief's `:361-365` range is **correct** — but it spans an `if/else`, and the quoted line is only the
`if` arm. Upstream degrades gracefully when `retry` is absent; the harness must not, because `08:29` makes
`retry` load-bearing. That is precisely why the golden image must **install** `retry` rather than inherit
it. Confirmed present in the prep installer at `:589` (`brew install kadwanev/brew/retry`) and in
`smoke-test-docker.sh:142`.
Claims: `smoke-retry-wrapper-is-conditional-line-360`, `smoke-retry-apply-line-361`,
`smoke-promptstring-line-362`, `prereq-installer-installs-retry-line-589`.
**Status:** FIXED in 08. **Owner:** 🧪 harness.

#### C-H9 — 🔴 **D2's line numbers are WRONG. The brief has now been caught a THIRD time.**
`_RULES.md` warns: *"the master brief has been caught with a false line-number claim (D5) and a false CLI
claim (rename-tab). Treat every line number in it as a hostile witness."* Duly.

The brief and this backlog both put the phantom recipes at **`12:200-202`**.
```
$ grep -n '`build \[IMAGE\]`\|`build-ipsw VERSION`\|`images`\|`pull IMAGE`' specs/macos-ci/12-tooling-and-agent-loop.md
201:| `build [IMAGE]` | …
202:| `build-ipsw VERSION` | …
203:| `images` | …
204:| `pull IMAGE` | …
$ sed -n '200p' specs/macos-ci/12-tooling-and-agent-loop.md
|---|---|
```
`:200` is the table's **separator row**. `:203` (`images`) falls **outside** the brief's range. And D2
**undercounts**: a fourth phantom, **`pull IMAGE` (`:204`)**, sits in the same table and is equally absent
from `just --summary`. Correct citation: **`12:201-204`, four recipes, not three.**
Claims: `justfile-has-no-build-ipsw-recipe`, `justfile-has-no-images-recipe`, `justfile-has-build-golden`.
**Status:** FIXED in 12. **Owner:** 🧪 harness. 👑 **lead: D2's text needs the same correction.**

#### C-H10 — 🟢 G12's approximate line numbers, re-derived. One is off by one.
| Brief | Actual | |
|---|---|---|
| prereq-installer `~:578` | **`:578`** `brew install bossjones/asdf-versions/asdf@0.11.2` | ✅ exact |
| prereq-installer `~:752` | **`:753`** `git clone … asdf.git ~/.asdf --branch v0.11.2` | ⚠️ `:752` is the preceding `log` line |
| `.chezmoiignore.tmpl:5` | **`:5`** `{{ if eq .version_manager "mise" -}}` | ✅ (and `:11` is the `else` — both directions) |
| `install.sh:206` "hard-errors" | **`:206`** opens the guard; **`:209`** is the `exit 1` | ⚠️ imprecise, not false |
| `.chezmoi.yaml.tmpl:102-107` | ✅ exact | |
| `.chezmoi.yaml.tmpl:20` = `asdf` | ✅ exact | |
| `12:340` VNC marker | ✅ exact (file is 535 lines; the prior pass's `:607` remains fiction) | |

Also: **`zsh-dotfiles` DOES ship a macOS asdf script** — `run_onchange_after_50-macos-install-asdf-plugins.sh.tmpl`.
G12's wording (*"no `02-macos-install-asdf`, only `-centos-`/`-ubuntu-`"*) is true **only of the `02-*`
installer family**. The `50-*-install-asdf-plugins` family *does* have a macOS member, which exits 0 when
the binary is missing (`:32`). The existing `no-macos-asdf-installer` claim targets the right thing; the
prose around it needed the qualifier. **G12 upheld, with that caveat.** **Owner:** 🧪 harness.

#### C-H11 — 🟢 D4 confirmed, and it is broader than stated.
`just --summary` → `build-golden check default link-check link-check-fresh link-check-verbose
unverified-count verify-claims verify-claims-json verify-no-secrets`. `tools/verify_claims.py` and
`tests/fixtures/packer-sensitive/fixture.pkr.hcl` exist; **`src/` and `packer/` do not** (D1 confirmed
independently: `ls -d packer` → `No such file or directory`, while `Justfile:44` invokes
`packer/tart-golden-image.pkr.hcl`).

So spec 12's opening sentence — *"Everything here is a design specification, not yet built"* (`12:5`) — is
now **false for six recipes and one tool, and still true for the entire `src/macos_ci/` package.** Redrawn
in 12 as an explicit three-way split (built / phantom-in-this-spec / not-yet-built) rather than a blanket
disclaimer. **Owner:** 🧪 harness.

#### C-H12 — 🟢 G13 upheld; `12:340` marker RETAINED, unchanged.
`tart run --help` (2.32.1) does expose `--vnc-experimental` (ledger: `tart-has-vnc-experimental`, passing).
The **stdout format** at `12:318` remains unbooted and unverifiable. Marker untouched; OQ-02 stands; the
lead's `oq02-vnc-marker-pinned-at-12-340` pins it. **No line of 12's VNC section was edited.**

#### C-H13 — 🔴 **I BROKE TWO LIVE LEDGER CLAIMS BY FIXING D2 AND D4. `just verify-claims` is RED (61/63).**
Reporting rather than silencing. **🔬 ledger must merge the replacements; I may not touch `claims.jsonl`.**

```
$ just verify-claims
[FAIL] oq02-vnc-marker-pinned-at-12-340  (file-line)
         line 340 is '`_gui_core.parse_vnc_url()` turns that line into a `VncTarget`; `gui.p',
         expected to contain '<!-- UNVERIFIED: `--vnc-experimental`'
[FAIL] d2-spec12-201-documents-nonexistent-build-recipe  (file-line)
         line 201 is '| `destroy` | `tart delete` the clone. |', expected to contain '`build [IMAGE]`'
61/63 claims verified
```

Neither is a regression. **Both are the ledger doing exactly its job**, and they fail for two *different*
reasons that are worth separating:

1. **`d2-spec12-201-…` pinned the PRESENCE of a defect.** I was told to fix D2. The moment I did, the claim
   asserting *"line 201 documents `build [IMAGE]`"* had to fail. **A `file-line` claim that pins a defect
   is a claim that must fail the day the defect is fixed.** It should be *inverted*, never deleted —
   proposed as `d2-spec12-no-longer-documents-build-recipe` (`absent`, dry-run PASS).

2. **`oq02-vnc-marker-pinned-at-12-340` pinned a MARKER that I never touched.** The D4 rewrite added 19
   lines above it; `git diff` shows **zero** changes to the marker's own text. `:340` → **`:359`**. The
   marker is byte-identical and still there. G13 is upheld and OQ-02 stands.

   **This is the `file-line` trade-off, discovered the hard way.** The lead created that claim to kill the
   hallucinated `:607` citation — and it works. But a line pin is *brittle against any edit above it*, so
   it conflates *"the citation rotted"* with *"the marker vanished"*, which are opposite findings. A marker
   that was **deleted** and a marker that **moved down 19 lines** produce the same red. So I propose
   **both**: `oq02-vnc-marker-pinned-at-12-359` (`file-line` — catches a wrong citation) **and**
   `oq02-vnc-marker-exists-regardless-of-line` (`file-contains` — survives edits, catches deletion). One
   alone cannot distinguish the two failure modes. Both dry-run PASS.

**Honesty budget, checked, not asserted.** My three files carried **5** real markers before my edits
(`08:62,97,104,174` · `12:340`) and carry **5** after (`08:72,107,114,189` · `12:359`). One marker was
*rewritten* (the sheldon line, now citing OQ-17); none was deleted; none was added. Net **0**.
`just link-check` → **exit 0**. `just unverified-count` → 15 globally, and **none of the delta is mine**.

**Owner:** 🔬 ledger (merge the three replacements, retire the two stale pins) + 👑 lead (the gate is red
until then).

#### C-H14 — 🔴 CROSS-AUDIT of 🏭 tart-ci — G4 survives; the oracle beneath it does not.
Full block under **RETRACTION CANDIDATES** below. Headline: **every licence figure is correct to the
dollar**, and I found instead that a `must_fail` `doc-contains` aimed at a *zero-text indexed page* passes
silently — the `STRUCTURE:` guard does not cover it. **OQ-19 (NEEDS-HUMAN)** → 🔬 ledger.

### 🔐 secrets

**AUDIT-OWN + CROSS-AUDIT complete.** 15 proposed claims in
[`.team/proposed/secrets.jsonl`](proposed/secrets.jsonl), **15/15 dry-run PASS**, and all 5 deliberately
broken mutants of my own negative probes correctly **FAIL** (see S-2). G15/G16/G17 all **upheld**; G16 is
upheld *and strengthened*. Nothing in my brief was refuted. Ten findings, all in artefacts, none in the
ground truths.

#### S-1 CONFLICT · 13 attributed to the fixture an execution the fixture cannot perform 🔴
`13`'s masking section said *"Executed against `tests/fixtures/packer-sensitive/`, three things are true"*
and listed (2) *"a non-sensitive variable holding the **same string** also prints `<sensitive>`"* and
(3) value-based masking. **The fixture's `pub` defaults to `plain_FIXTURE_CONTROL` — a different string
from the sensitive `sec`.** No execution against that fixture, and no ledger claim, ever assigned a
non-sensitive variable the secret's value. The conclusion is *true*; the cited execution never
demonstrated it. **This is lesson 2 of the master brief — "an assertion with a citation is decorated, not
verified" — occurring inside the spec that teaches lesson 2.**

Fixed without touching the fixture (which I do not own): `packer inspect -var 'pub=<secret>' <fixture>`
asks the question the fixture could always have answered.

```
$ packer inspect -var 'pub=ghp_FIXTURE_SENTINEL'        tests/fixtures/packer-sensitive
var.pub: "<sensitive>"                   # non-sensitive var, redacted anyway
$ packer inspect -var 'pub=notthesecret_CONTROL'        tests/fixtures/packer-sensitive
var.pub: "notthesecret_CONTROL"          # control: -var really assigns
$ packer inspect -var 'pub=prefix-ghp_FIXTURE_SENTINEL-suffix' tests/fixtures/packer-sensitive
var.pub: "prefix-<sensitive>-suffix"     # redaction is SUBSTRING-level
```

→ claims `packer-sensitive-masks-by-value-not-variable`,
`packer-sensitive-masks-substring-inside-larger-value`,
`CONTROL-packer-inspect-var-flag-assigns-plain-value`. **G16 upheld and strengthened**: masking is not
merely value-based, it is *substring*-based — a scratch fixture marking `admin` sensitive rendered
`/admin/home` as `/<sensitive>/home`. The G8 `admin/admin` creds must stay plain, emphatically.

#### S-2 CONFLICT · the `PACKER_LOG=1` pair does not test what its name says 🟡
**Not vacuous — under-powered, which is worse, because it reads as covered.** Both pairs share `argv`
and `env` with their controls, and `plain_FIXTURE_CONTROL` really is printed. But:

| | pair 1 | pair 2 (`-under-debug-log`) |
|---|---|---|
| control asserts a literal the same argv+env prints | yes | yes |
| control can detect the debug log ran **at all** | n/a | **no** |

Measured with separate pipes (as `subprocess.run(capture_output=True)` captures):
`plain_FIXTURE_CONTROL` lives on **stdout**, and stdout is **byte-identical** with and without the
overlay — 136 B either way, `diff` clean. `PACKER_LOG=1` adds 845 B on **stderr**, which the verifier
concatenates before matching. So `CONTROL-packer-debug-log-prints-plain-literals` would pass unchanged
against a Packer that ignored `PACKER_LOG` entirely, and `packer-sensitive-hides-secret-under-debug-log`
would then assert *"the secret is absent from a debug log that was never produced."*

→ proposed the missing discriminator: `CONTROL-packer-log-env-overlay-is-effective` (expects
`[INFO] Packer version:`, which appears **only** under the overlay) and
`packer-debug-log-silent-when-overlay-disabled` (`must_fail`, `env: {"PACKER_LOG": "0"}`) with its
positive control `CONTROL-packer-log-disabled-still-prints-plain-literals`.
**I did not delete or weaken either existing pair.** 🔬 ledger's call.

#### S-3 CONFLICT · `verify_claims.py`'s `env` overlay can SET but never UNSET → OQ-14 🟡
`tools/verify_claims.py:211` — `env = {**os.environ, **claim.get("env", {})}`. An operator with
`PACKER_LOG=1` exported silently promotes **every** "no-env" claim to a debug-log run. Both still pass, so
the failure is invisible: pair 1 stops testing the no-debug-log case, and pair 2 degenerates into a
duplicate of it. Measured: `PACKER_LOG` unset / `""` / `0` all disable; **any** other non-empty value —
including `off` — enables. Workaround used (pin `"0"`), not a fix. `unset: [...]` is ~4 lines but the file
is 🔬 ledger's. → **OQ-14**.

#### S-4 CONFLICT · 13 misquotes the `Justfile` — twice, dropping a load-bearing idiom 🟡
Both fenced recipes in 13 were transcriptions, not quotes, and both were labelled as `make` for a
`justfile`.

```
Justfile:43  @HOMEBREW_GITHUB_API_TOKEN="${…:-$(gh auth token 2>/dev/null || true)}" \
13 (was)     @HOMEBREW_GITHUB_API_TOKEN="${…:-$(gh auth token 2>/dev/null)}" \
```

The dropped `|| true` is **the same idiom 13 itself calls "load-bearing"** eleven lines earlier, about
the Dockerfile. `verify-no-secrets` was likewise missing `|| true`, its `[ ! -d ~/.tart/vms/{{vm}} ]`
guard (`exit 4`) and its real echo strings. **Fixed in 13; both now quoted verbatim with line refs.**

#### S-5 CONFLICT (→ 🍎 tart-core, file `02`) · `disk_format` is inert on the clone lane 🔴
13:44-46 justified "raw disk image" by citing `disk_format = "raw"` from `02`. From the local
`packer-plugin-tart` clone:

```
builder/tart/builder.go:93-94      if b.config.DiskFormat == "" { b.config.DiskFormat = "raw" }   # raw IS the default
builder/tart/step_create_vm.go:33  if config.DiskFormat != "" && config.DiskFormat != "raw" { … "--disk-format" }
builder/tart/step_clone_vm.go      (no reference to DiskFormat at all)
```

and the plugin's own field reference says *"Only applies when using `from_ipsw` and `from_iso`."*
**The golden image is cloned, so `--disk-format` is never passed and `disk_format = "asif"` would be a
silent no-op on our lane.** Two consequences: 13's residue argument does not rest on `disk_format` (it
rests on the *source image's* format, which this run has **not** established); and **OQ-01 is narrower
than it reads** — asif can only arise on a `from_ipsw`/`from_iso` build. **OQ-01 is NOT closed and the
markers at `13:51`/`13:54` STAY** (both re-verified with `sed -n`; the lead's pins
`g15-hdiutil-caveat-marker-pinned-at-13-51` / `oq01-asif-marker-pinned-at-13-54` still PASS against my
edited file — I kept every edit at line ≥56 or line-count-neutral, precisely so they could not rot).
→ 🍎 **tart-core should reconcile `02`'s `disk_format` prose.** Claims proposed:
`tart-builder-disk-format-defaults-to-raw`, `tart-builder-passes-disk-format-only-on-create-path`,
`CONTROL-tart-builder-clone-step-ignores-disk-format`.

#### S-6 · D1 CONFIRMED, documented, template NOT authored ✅
`packer/` does not exist; `Justfile:44` invokes `packer/tart-golden-image.pkr.hcl`. Both pinned:
`justfile-build-golden-invokes-missing-template` (`file-line`) + `golden-template-does-not-exist`
(`cli-help`). `13`'s design section now opens with a callout stating the template **is absent** and that
**not one line of it has been validated**, separating the *verified mechanisms* from the *unwritten
template that would compose them*. Justfile untouched (👑 lead owns it). OQ-04 remains NEEDS-HUMAN.

#### S-7 · G17 upheld, every clause re-executed (one of my own probes was unsound first) ✅
`60` = live `api.github.com/rate_limit` unauthenticated core limit. All three repos return `200` from
`info/refs?service=git-upload-pack`. `HOMEBREW_GITHUB_PACKAGES_TOKEN` absent from both trees (267 + 43
tracked files) — **first measured with `grep … | head`, whose exit code is `head`'s, not `grep`'s;
re-run with `grep -q`.** And `git ls-remote git@github.com:…` succeeding proves *nothing* on a host with
an SSH agent, so the rewrite is now demonstrated against a **disabled** SSH transport with a negative
control: `GIT_SSH_COMMAND=false` alone → `exit 128`; plus `GIT_CONFIG_*` → `exit 0`. Only HTTPS explains it.

#### S-8 · budget 16 → 15 is HONEST. I certify it, having tried to break it 🟢
`just unverified-count` now lists **15**. The lost marker is `01-tart-core.md:68` (the `ghcr.io` image-ref
caveat), deleted by 🍎 tart-core and replaced with a citation to
`tart-quickstart-lists-sequoia-xcode-image`. Per `_RULES.md` §6 that is legal **only** if the claim
passes. It does (`doc-contains`, dry-run PASS), and I confirmed the page independently rather than
trusting the tool: `ghcr.io/cirruslabs/macos-sequoia-xcode:latest` is one of 20 refs listed verbatim
under `quick-start/`. **This is a marker retired by verification, not by deletion — the budget fell for
the right reason.** 13 still carries exactly its 2 markers; I added none and removed none.

#### S-9 · G19 re-checked, not inherited 🟢
`curl -sS -o /dev/null -w '%{http_code}'` on the Tart builder field reference → **200**, while the sitemap
still yields **0** `/packer/integrations/` entries. I fetched the page before forming any view of it. The
carve-out holds. Separately: **HashiCorp doc prose cannot be substring-grepped from raw HTML** — `Default:
false` and `This defaults to false` are both absent from the bytes `curl` returns, because tags split the
sentences. Any future `cli-help`+`curl` claim against `developer.hashicorp.com` HTML is unsound. Packer's
**pinned source** (`raw.githubusercontent.com/…/v1.15.4/…`) is plain text and is sound → **OQ-13**
(NEEDS-HUMAN: may `just check` depend on GitHub egress?).

#### S-10 · note for 👑 lead · OQ numbering collided three ways 🟡
`OQ-08` was taken concurrently by 🏭 tart-ci, 🔬 ledger **and** 🧪 harness; `OQ-09` by 🖥 utm and 🧪 harness.
Per `_RULES.md` §6 I renumbered upward: mine are **OQ-13** and **OQ-14**. The duplicate numbers are still
live in the file and `02:135` cites *"See OQ-08"* ambiguously. Someone with authority over the shared file
should disambiguate; I did not edit another agent's block.

#### Ledger note — the `must_fail` count is 6, not 7
`grep -c must_fail .team/claims.jsonl` returns **7**. Parsing the JSON returns **6**: the seventh hit is
the *word* `must_fail` inside `CONTROL-packer-debug-log-prints-plain-literals`'s `claim` prose. The brief
says six; **the brief is right and the grep is wrong.** Worth knowing before anyone "reconciles" the count.

### 📚 synth
_(none yet)_

---

## RETRACTION CANDIDATES (agents append; lead adjudicates)

### 🧪 harness — CROSS-AUDIT of 🏭 tart-ci (`03-tart-ci-and-orchard.md`, `04-tart-licensing-risk.md`)

**Posture: default to refuted. I tried to break every number and could not break one.**

#### X-1 — 🟢 **G4 UPHELD.** Every licence figure re-derived independently, from the search index, not from 04.
I did not read tart-ci's citations and agree with them; I pulled `tart.run/search/search_index.json`
myself and read the `licensing/**` entries cold.

| 04 says | `tart.run/licensing/` says, verbatim | |
|---|---|---|
| Free: 100 cores / 4 Orchard workers | *"Free Tier license has a 100 CPU core limit for Tart and 4 Orchard Workers limit for Orchard."* | ✅ |
| Gold: $12,000/yr, 500 cores, 20 workers | *"…costs $12,000 per year." / "500 CPU core limit … 20 Orchard Workers limit"* | ✅ |
| Platinum: $36,000/yr, 3,000 cores, 200 workers | *"…costs $36,000 per year." / "3,000 CPU core limit … 200 Orchard Workers limit"* | ✅ |
| Diamond: $12/core/yr, cores *not stated*, workers Unlimited | *"…costs $12 per CPU core per year and gives the ability to run unlimited Orchard Workers."* | ✅ **and tart-ci's two corrections are right** |
| every P+E core counts | *"all performance and energy-efficient cores of the host CPU are always counted towards the license usage"* | ✅ |

**No number has moved.** tart-ci's two "precision corrections" (`04:74-80`) are both correct: the page
does *not* state a Diamond core ceiling, and the price is exactly `$12`, not `~$12`.

**One free strengthening, offered not demanded.** The licensing page settles the *"combined, not per-host"*
reading at `04:43` with a worked example 04 does not quote: *"Using Tart on 12 Mac Minis with 8 CPUs each"*
(= 96) **fits** the free tier; *"Using Tart on 13 Mac Minis with 8 CPUs each"* (= 104) **does not**. That is
upstream doing the arithmetic for us. Worth a `doc-contains` claim. 🏭 tart-ci's call, not mine.

#### X-2 — 🟢 All twelve blog quotations in 04 verified **verbatim against the fetched pages**.
Per G19 I did not grep the index for these; I `curl`'d them. All four cited URLs return `200`.
`Fair Source 100` · `unlimited installations on personal computers` · `royalty-free and does not have the
viral properties of AGPL` · `before reaching the 100 CPU cores limit` · `installation of Tart on a physical
device without a physical display connected` · `HDMI Dummy Plug is considered a server` · `Successfully
Enforces Its Fair Source License` · `in order to create a competing product` · `Jordan Raphael` ·
`Heather Meeker` · `This was an exceptional case` · `Most of our users have no trouble complying with our
license` — **12 / 12 found.**

#### X-3 — 🟢 §4b's OpenAI-org claim **CONFIRMED**, and it is the biggest live fact in the repo.
```
$ curl -fsSL https://api.github.com/repos/cirruslabs/tart | …
full_name: openai/tart      license: NOASSERTION      stars: 6061
created: 2022-02-01         pushed: 2026-07-07
$ curl -fsSL https://raw.githubusercontent.com/openai/tart/main/LICENSE | head -1
# Functional Source License, Version 1.1, ALv2 Future License
$ curl -fsSL https://api.github.com/repos/cirruslabs/tart-guest-agent | …
full_name: openai/tart-guest-agent
```
`cirruslabs/tart` **is** `openai/tart`; the guest agent moved too; the licence **is** `FSL-1.1-ALv2`.
Meanwhile `tart.run/licensing/` still says "Fair Source License" and still routes to
`licensing@cirruslabs.org`. 04's three open sub-questions (who enforces, is the tier table stale, the
ALv2 conversion term) are **live and correctly flagged**. This is the item the human should read first.

#### X-4 — 🔴 **THE ONE REAL DEFECT I FOUND, and it is not in 04 — it is in the oracle 04 relies on.**
`04:94-99` warns not to refute the blog posts via the index, and pins that with
`CONTROL-tart-blog-is-outside-doc-index-domain`. **Correct, and incomplete.** Its supporting sentence —
*"that index … covers 20 documentation pages and zero blog posts"* — is literally true and materially
misleading. **Six of those 20 pages are under `blog/`**: `/blog`, `/blog/archive/{2023,2024,2025}`,
`/blog/category/{announcement,orchard}`. The blog is not absent from the index. It is **half-present** —
the pages are indexed and their body text is **empty**.

That matters because `tools/verify_claims.py` has no guard for it:

```
$ uv run tools/verify_claims.py <scratch>/mf.jsonl
[PASS] MUTANT-CONTROL-on-empty-page    (doc-contains)   # page=/blog/ expect="literally anything at all"
[FAIL] MUTANT-CONTROL-on-missing-page  (doc-contains)
         STRUCTURE: page '/no/such/page' is not in the tart index — fabricated or moved
```

**A `must_fail` `doc-contains` aimed at a zero-text indexed page goes green.** It would go green for any
string ever written. `STRUCTURE:` catches a *missing* page; nothing catches a *textless* one, so the check
falls through to the ordinary "sentence not found" branch and `must_fail` inverts it. And the non-inverted
diagnostic actively lies: `page /blog exists but does not contain 'Fair Source 100' — upstream may have
reworded; re-read it`. It never had text to reword.

**Blast radius, measured rather than assumed:** the four live `doc-contains` controls are **safe today** —
`/integrations/cirrus-cli` (2378 chars), `/licensing` (5225), `/quick-start` (10863). Nothing is currently
green for the wrong reason. But *"a verifier nobody verifies is just a second thing to trust"* is this
run's own rule, and here the verifier's guard has a hole the guard was written to close.

→ **OQ-19 (NEEDS-HUMAN).** Fix is one branch in `evaluate()`; `tools/verify_claims.py` is 🔬 **ledger**'s
file alone. **Not tart-ci's defect. Routing it to 🔬 ledger and 👑 lead.**

#### X-5 — 🟡 `03:112` names *"four controls"*. There are now **nine** `must_fail` claims in the live ledger.
`CONTROL-utm-settings-apple-devices-is-fabricated`, `CONTROL-disposable-is-not-apple-backend`,
`CONTROL-tart-doc-index-oracle`, `CONTROL-tart-cirrus-page-has-no-sshpass`, `packer-sensitive-hides-secret`,
`packer-sensitive-hides-secret-under-debug-log`, `CONTROL-12-line-607-does-not-exist`,
`g16-injected-secret-never-prints-in-unrelated-variable`, `CONTROL-d1-packer-dir-does-not-exist`.
A hard-coded count in prose rots on every merge. Suggest *"the `must_fail` controls"* with no number, or a
ledger claim that pins it. **Owner:** 🏭 tart-ci. Low severity; the four it names are all still real.

#### X-6 — 🟢 `03`'s CLI claims hold. `cirrus run --help` really documents
`--artifacts-dir string   directory in which to save the artifacts`, and `cirrus version 1.0.0-1769788` is
installed. `03`'s two `<!-- UNVERIFIED -->` markers (`:53`, `:144`) are honest and should stay.

**Summary of the cross-audit: 04 survives a hostile read intact. The number I set out to break — G4 — is
correct to the dollar. The defect is one layer beneath it, in the tool that proves things.**

---

## 👑 LEAD ADJUDICATION — BLOCKING. The gate may NOT go green until these are closed.

### 🔴 GATE-BLOCKER 1 — a vacuous control is currently PASSING inside a 237/237 green gate

Verified by the lead directly against the merged `.team/claims.jsonl`:

```
no-xcode-select-in-zsh-dotfiles-tracked        cli-help  must_fail=True   expect=':'
no-ansible-in-zsh-dotfiles-tracked             cli-help  must_fail=True   expect=':'
prep-repo-has-no-ansible-playbook              cli-help  must_fail=True   expect=':'
CONTROL-git-grep-c-emits-colon-when-present    cli-help  must_fail=False  expect=':'   <-- VACUOUS
```

`git`'s own failure diagnostic contains a colon:
`fatal: cannot change to '/nonexistent-repo': No such file or directory`.
So the control passes against **a repo that does not exist**. It proves *"some output containing a colon
appeared"* — **not** its stated claim, *"`git grep -c` in this tree emits `path:count`"*.

**Why the pill says "6 controls intact" AND ledger proved a control vacuous, with no contradiction.**
The six are the *original* `must_fail` oracles — all six confirmed `PRESENT must_fail=True` by the lead,
none deleted or weakened. The vacuous one is a **seventh, newly-added positive control**
(`must_fail=False`). Both statements are true. This is precisely why the brief distinguishes the two jobs
of `must_fail`, and precisely why "controls intact" is not the same question as "controls meaningful".

**The pair is safe today, and safe *by accident*.** A broken repo turns the gate red only because the
*probe* also keys on `":"` and inverts on it. Strengthen the probe's literal — the obvious, well-intentioned
"improvement" — and the control goes green on a nonexistent repo while the probe does too: a **silent false
green** on `no-xcode-select-in-zsh-dotfiles-tracked`, `no-ansible-in-zsh-dotfiles-tracked`, and
`prep-repo-has-no-ansible-playbook`, three of G9/G12's load-bearing negatives.

🔬 ledger fixed this **additively** (correctly, without rewriting harness's records) by adding
`CONTROL-git-grep-emits-real-path-count-token` (`home/.chezmoi.yaml.tmpl:`) and
`CONTROL-prep-git-grep-emits-real-path-count-token` (`.github/dependabot.yml:`) — literals no `fatal:`
line can produce. **Both PASS.** But the `":"` control was left in place, and the gate is green with it.

**LEAD RULING:** a control that would pass no matter what is a green check that means nothing, and the
brief says such a thing must **fail loudly**, not be quietly noted. → 🔬 **ledger** (sole owner of
`claims.jsonl`): **retire the three `":"` literals**, repointing the probes and the control at the
discriminating tokens. **This blocks GATE.** Do not close it by deleting the probes.

### 🔴 GATE-BLOCKER 2 — invariant (b) does not generalize, and the master brief is wrong about it
Invariant (b) is written for the `packer inspect` shape, where the same command prints a variable table
regardless of the claim. It **cannot** hold for a `grep -c`-shaped probe, where a true negative implies
**empty output**, making a same-`argv` positive control a *logical impossibility*.

**The rule needs a second clause:** *when a true negative implies no output, the control must run the same
command **shape** against the same substrate with a pattern known to match, and must assert a literal that
the command's **error** paths cannot produce.* → 👑 lead / the next brief.
**This is a retraction of the master brief's `must_fail` JOB 2 as written.**

### 🟡 GATE-BLOCKER 3 — `CONTROL-12-line-607-does-not-exist` is drifting toward accidental validity
`12-tooling-and-agent-loop.md` grew **535 → 577** lines during this run. The lead's control asserts line
607 does not exist. It is now **30 lines** from passing — at which point the gate goes red with the message
*"CONTROL PASSED — the oracle is broken"*, which would be **wrong**: nothing broke, the file merely grew.
The tripwire fires on the right event for the wrong reason. → 👑 lead decision.

**And it already bit.** The same growth moved the `--vnc-experimental` marker `:340 → :359`, invalidating
the lead's *own* Correction #1 in OQ-02 **within this same run**. 🔬 ledger caught it by execution and
re-pinned it, adding the line-agnostic `oq02-vnc-marker-exists-regardless-of-line`.
**Nobody caught it by reading.** A `file:line` citation in prose is a fact with a half-life; only the
re-executable claim survived both the hallucination and the drift.

---

## 🖥 utm — CROSS-AUDIT of harness (08, 09, 12)

### utm - CROSS-AUDIT of harness (08, 09, 12)

Posture: default to refuted. Every line number below re-derived with `grep -n` / `sed -n` at audit time.
`.team/proposed/utm.jsonl` — **44/44 dry-run PASS, exit 0** (27 from AUDIT-OWN, 17 from cross-audit).

#### ✅ (2) G13 HELD — the VNC stdout format was NOT upgraded to fact
The marker survives, guarding the §`gui` prose:
```
$ grep -n 'UNVERIFIED: `--vnc-experimental`' specs/macos-ci/12-tooling-and-agent-loop.md   -> 359
```
Pinned by **`xaudit-12-vnc-stdout-stays-unverified`** (`file-contains`, deliberately **not** `file-line` —
the same assertion as a `file-line` claim already rotted twice this run: `:340` → `:349` → `:359`).
**But see CONFLICT X-3 and OQ-28:** the string's *first* appearance is a pytest `assert` at `12:79`,
280 lines before its caveat.

#### ✅ (3) D2 and D4 CONFIRMED by execution
```
$ just --summary
build-golden check default link-check link-check-fresh link-check-verbose unverified-count
verify-claims verify-claims-json verify-no-secrets
$ ls tools/   -> verify_claims.py
$ ls tests/   -> fixtures/packer-sensitive/{fixture.pkr.hcl}
$ ls -d packer/  -> No such file or directory      # D1 stands; Justfile:44 invokes it
```
`12` now handles both correctly: `:11` splits *Built and passing today* from `:12` *Built but broken*, and
the recipe table at `:216-218` marks `build-ipsw VERSION` and `images` as **`Proposed.`**, with an explicit
retraction note at `:209-211`. **D2 and D4 are FIXED, not merely acknowledged.** Claims:
`xaudit-12-no-build-ipsw-recipe`, `xaudit-12-no-images-recipe`, `CONTROL-xaudit-just-summary-lists-build-golden`.
- 🟡 **Nit:** `12:11`'s "Built and passing today" list omits `default`, which `just --summary` prints. Nine
  of ten. Cosmetic; no claim proposed.

#### ✅ (4) LEDGER'S CONFLICT L6 — CONFIRMED BY EXECUTION, and refined
I did not take L6 on trust. Executed:
```
$ git -C /Users/.../zsh-dotfiles      grep -c stdinIsATTY
home/.chezmoi.yaml.tmpl:1
specs/fix-smoke-mise-version-manager.md:2
$ git -C /Users/.../NO-SUCH-REPO      grep -c stdinIsATTY
fatal: cannot change to '/Users/.../NO-SUCH-REPO': No such file or directory    # <- contains ':'
```
`CONTROL-git-grep-c-emits-colon-when-present` expects only `":"`. **It PASSES against a repo that does not
exist.** Ledger is right, and `CONTROL-git-grep-emits-real-path-count-token` is the correct fix. Confirmed
through the verifier itself, not by inspection:
```
[PASS] WEAK-CONTROL-vs-broken-path
[FAIL] STRONG-CONTROL-vs-broken-path
[FAIL] NEGATIVE-xcode-vs-broken-path      CONTROL PASSED — the oracle is broken
[FAIL] NEGATIVE-ansible-vs-broken-path    CONTROL PASSED — the oracle is broken
```
**REFINEMENT ledger should hear — L6's severity is overstated.** In the very world where the weak control
goes vacuous, git's `fatal:` line *also* contains `":"`, so **both `must_fail` negatives fail loudly** and
the suite goes red anyway. I could construct no world where the control passes vacuously *and* the negatives
pass. **The weak control degrades DIAGNOSIS, not DETECTION.** That does not make it acceptable — a control
that cannot distinguish `path:count` from `fatal:` is not testing its own sentence — but the ledger was
never at risk of going silently green. Claim: `xaudit-09-git-grep-fatal-line-contains-a-colon`.

#### 🔴 CONFLICT X-1 — `no-macos-asdf-installer` is `absent` over the WRONG FILE, and its `02-` prefix is silently load-bearing
`claims.jsonl:8` asserts `absent("02-macos-install-asdf")` in **`.chezmoiignore.tmpl`**, with the prose
*"there is no macOS asdf installer script to ignore, **because none exists**."* Two defects:

1. **Wrong target.** "None exists" is a fact about `.chezmoiscripts/`, not about the ignore list. The claim
   passes unchanged if someone **adds** `02-macos-install-asdf.sh` and forgets to ignore it.
2. **The `02-` prefix is doing undocumented work.** `.chezmoiignore.tmpl:5-10` *does* enumerate asdf scripts,
   and line 8 is `.chezmoiscripts/run_onchange_after_50-macos-install-asdf-plugins.sh` — which **contains the
   substring `macos-install-asdf`**. Drop the prefix and the claim inverts:
```
[PASS] AS-MERGED-02-prefix      # absent("02-macos-install-asdf")
[FAIL] WITHOUT-02-PREFIX        # absent("macos-install-asdf") -> .chezmoiignore.tmpl unexpectedly contains it
```
**Proposed replacement, dry-run PASS**, probing the directory the claim is actually about, with **two**
positive controls so the absence is provably *macOS-specific* rather than *ls printed nothing*:
`xaudit-09-no-macos-asdf-installer-script-on-disk` (`must_fail` over `ls .chezmoiscripts/`) +
`CONTROL-xaudit-scripts-dir-lists-macos-mise-installer` + `CONTROL-xaudit-scripts-dir-lists-ubuntu-asdf-installer`.
Plus `xaudit-09-ignore-file-does-contain-macos-install-asdf`, which documents the trap so nobody
"simplifies" the prefix away. **Do not delete the merged claim — strengthen it.** → **OQ-27**.
- **Owner:** 🔬 ledger (evidence) + 🧪 harness (prose at `09:120`).

#### 🔴 CONFLICT X-2 — `absent` claims have no control requirement at all
`_RULES.md` §5 mandates a positive control for a negative `must_fail` **`cli-help`** probe, on the grounds
that *"no secret in the output" is equally satisfied by no output.* **`absent` has the identical hazard and
no guard.** X-1 is the worked example. → **OQ-27**.
- **Owner:** 👑 lead (`_RULES.md`) + 🔬 ledger (`verify_claims.py`).

#### 🟡 CONFLICT X-3 — `12:79` encodes the UNVERIFIED VNC string as a test assertion
```
$ sed -n '79p' specs/macos-ci/12-tooling-and-agent-loop.md
    line = "Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415..."
```
Presented as *"an obvious first failing test, before a line of implementation exists"* — i.e. the seed test
someone pastes into `tests/unit/test_gui_core.py`. Its marker is at `:359`. The danger is not the failing
test; it is the "fix": adjusting the regex to match whatever a VM prints launders the unverified format into
a green assertion. Suggest repeating the marker at `:79`, or `pytest.mark.xfail(reason=…OQ-02)`. → **OQ-28**.
- **Owner:** 🧪 harness.

#### 🟡 (1) 08's markers cite a SIBLING SPEC — restated, line numbers re-derived
Full detail under `### 🖥 utm` above (**U-1/U-2/U-3**). The brief's `:62/:97/:104/:174` are **stale**;
current: `:72`, `:107`, `:114`, `:189`. Verdicts from `tart` 2.32.1 itself, not from `01`:

| marker | verdict |
|---|---|
| `:72` `tart clone` | ✅ correct — `USAGE: tart clone <source-name> <new-name>` |
| `:107` `--no-graphics` | ✅ correct — `Don't open a UI window.` |
| `:114` `--dir` | 🔴 **`tart --dir` DOES NOT EXIST**; `tart --help` has exactly two globals. `--dir` is a `tart run` option |
| `:189` `sheldon` | ⚪ genuinely blocked — needs a booted guest (harness's OQ-17) |

`:189`'s marker now cites **OQ-17**, correctly renumbered after the OQ-08 collision. Two of the four markers
are **retirable** on merge; `:114` needs a **correction**, not a retirement.

#### ✅ 09 verified line-by-line against the LOCAL clones (never WebFetched)
Every G11/G12 citation in `09` re-derived with `sed -n`; all correct:
`.chezmoiroot:1` → `home` · `.chezmoiversion:1` → `2.20.0` · `.chezmoi.yaml.tmpl:2` →
`{{- $interactive := stdinIsATTY -}}` · `:20` → `{{- $version_manager := "asdf" -}}` · `:102-107` →
`version_manager` genuinely **outside** the `$interactive` guard, with an upstream comment saying exactly
why · `install.sh:206-209` → hard-errors when `brew` is missing · `.chezmoiignore.tmpl:5` → the
`eq .version_manager "mise"` branch · `git grep -c xcode-select` → **no tracked hit** (exit 1).
- ⚪ **Note on the master brief, not on `09`:** the brief quotes `smoke-test-docker.sh:361-365` as the
  non-TTY invocation **"verbatim"**. It is not verbatim — line 362 ends `|| chezmoi_exit_code=$?`, and
  `:361-365` straddles an `if`/`else` whose *else* branch runs the same command **without** `retry`. `09`
  itself does not repeat the error. Informational for 📚 synth.

### 🔴 GATE-BLOCKER 4 — the `absent` evidence kind has NO control requirement (OQ-27, utm) — GROUND-TRUTH CLASS

**Two distinct defects, one closed, one open.**

**(i) CLOSED THIS RUN — `must_fail` controls went GREEN on DELETED FILES.** At `HEAD`, `evaluate()` caught
`FileNotFoundError` and returned `f"missing: {e}"` — **without** the `UNREACHABLE:` prefix — so `must_fail`
**inverted it into a pass**. Proven by running the original verifier out of `git show HEAD:`:

```
$ uv run tools/verify_claims.py <must_fail file-line claim, target file does not exist>
[PASS] PROBE-mustfail-fileline-on-deleted-file  (file-line)
1/1 claims verified   EXIT=0
```

**Deleting a control's target file turned the control green.** A 404 wearing a green check. 🔬 ledger fixed
it (`+9/-2`): the handler now returns `UNREACHABLE: missing file: …`, exit **3**, never inverted. Re-verified
post-fix: `[FAIL] … UNREACHABLE: missing file`, exit 3. **This was a live hole in the verifier that guards
every other claim in the repo.**

**(ii) STILL OPEN — `absent` passes vacuously against an EMPTY or GUTTED file.**
`check_absent` is `return expect not in haystack`. Executed:

```
[PASS] PROBE-absent-on-EMPTY-file     (zero-byte target)
[PASS] PROBE-absent-on-GUTTED-file    (content replaced)
2/2 claims verified   EXIT=0
```

The brief mandates a positive control for a negative `must_fail` `cli-help` probe — *"no secret in the
output" is equally satisfied by no output at all* — but **never extends the rule to `absent`, and the tool
enforces neither.** An `absent` claim over an emptied file is a permanently green check that asserts nothing.
**Same disease, one evidence-kind over.**

**Empirical coverage — the lead audited all 13 `absent` claims.** Twelve are guarded *by accident or
diligence*: each has a sibling `file-contains`/`file-line` claim over the **same `target`**, pinning the
file's identity. **Exactly one is unguarded:**

| `absent` claim | target | positive control on same target |
|---|---|---|
| `prep-makefile-has-no-smoke-target` | `Makefile` | ***NONE*** |

**LEAD RULING → 🔬 ledger:** (1) add a positive control asserting a real `Makefile` token; (2) merge utm's
`xaudit-09-no-macos-asdf-installer-script-on-disk` (`must_fail` `cli-help` over `ls .chezmoiscripts/` with
**two** positive controls) — its shape is correct and it replaces a claim that survives only by a `02-`
prefix accident; (3) **enforce the pairing structurally** — require every `absent` record to name a
`control` id and exit `USAGE` if it does not, exactly as a bare negative `cli-help` probe is rejected as
unfalsifiable. **A rule the tool does not enforce is a rule that will be forgotten.**

**And a retraction of the master brief.** The brief's `must_fail` JOB 2 discipline is stated only for
`cli-help`. It must be restated as a property of **negative evidence in general**: *any claim that asserts
the absence of something must ship a positive control proving the probe would have detected its presence.*
That covers `absent`, negative `cli-help`, and `doc-contains` alike. → 👑 lead / the next brief.

---

### 🔬 ledger — GATE-BLOCKER 1 remediation

**Lead ruling accepted in full.** I had proven `CONTROL-git-grep-c-emits-colon-when-present` vacuous,
fixed it *additively*, and left the vacuous control in the ledger with the gate green. That was wrong:
per the brief a vacuous control must **fail loudly**, not be noted in prose. A green check next to a
control that cannot fail is exactly the "second thing to trust" the ledger exists to prevent.

**The three `":"` literals are retired.** Not deleted — *repointed*. All three probes survive.

| id | must_fail | old `expect` | new `expect` |
|---|---|---|---|
| `no-xcode-select-in-zsh-dotfiles-tracked` | ✔ | `":"` | `"xcode-select"` |
| `no-ansible-in-zsh-dotfiles-tracked` | ✔ | `":"` | `"nsible"` |
| `prep-repo-has-no-ansible-playbook` | ✔ | `":"` | `"osts:"` |
| `CONTROL-git-grep-c-emits-colon-when-present` | — | `":"` | → **`CONTROL-git-grep-o-emits-matched-text`**, `"stdinIsATTY"` |
| `CONTROL-prep-grep-c-emits-colon-when-present` | — | `":"` | → **`CONTROL-prep-grep-o-i-emits-matched-text`**, `"ame:"` |

The probes now run `git grep -h -o <pattern>`, which echoes **the matched text itself**. A match is
therefore proved by a token that `fatal: cannot change to '<path>': No such file or directory` cannot
contain. A true negative still emits **zero bytes** (verified: `wc -c` → 0), so `must_fail` inverts on
genuine absence and on nothing else.

**Proof the vacuity is gone — executed, not argued:**

```
[PASS] OLD-colon-control-against-broken-repo     expect=":"            <-- the retired control: PASSES on /nonexistent-repo
[FAIL] NEW-control-against-broken-repo           expect="stdinIsATTY"  <-- git -C /nonexistent-repo ... did not emit 'stdinIsATTY'
[FAIL] NEW-prep-control-against-broken-repo      expect="ame:"         <-- did not emit 'ame:'
```

If either repo path ever breaks, the control now fails loudly and *"xcode-select was absent"* stops
meaning anything — which is the whole point of a control.

#### Two holes found while remediating, both closed

1. **`grep -o` preserves case.** `"nsible"` catches `ansible` and `Ansible` but **not** `ANSIBLE`. No
   single lowercase literal can cover every casing under `-o`. Added `no-ansible-uppercase-in-zsh-dotfiles-tracked`
   (`expect: "NSIBLE"`). The two probes together cover all three realistic spellings.
2. **One `expect` cannot cover two alternated patterns.** `prep-repo-has-no-ansible-playbook` searched
   `-e hosts: -e become:` but could only assert one matched token. Split: `become:` now has its own probe,
   `prep-repo-has-no-become-key` (`expect: "ecome:"`). Both share the same positive control.

Two controls I had added additively last turn — `CONTROL-git-grep-emits-real-path-count-token` and
`CONTROL-prep-git-grep-emits-real-path-count-token` — guarded the now-retired `-c` probe shape. With no
probe left to guard they were **orphan controls**, so they are removed rather than left as decoration.

#### Invariant (b), second clause — now recorded in the claim prose, not just the backlog

Every remediated record's `claim` field carries this verbatim, so it re-executes with the evidence:

> **INVARIANT (b), SECOND CLAUSE:** when a true negative implies **NO OUTPUT**, a same-argv positive
> control is a **logical impossibility** — the same command can never print anything when the claim
> holds. The control must therefore run the same command **SHAPE** against the same **substrate** with a
> pattern **KNOWN to match**, and must assert a literal that the command's **ERROR paths cannot
> produce**. A bare `":"` fails this: `fatal: cannot change to '<path>': No such file or directory`
> contains one, so a `":"`-keyed control PASSES against a repo that does not exist.

Note this means the strict same-argv audit will still report these three probes as "unpaired". That is
**correct and expected** — the pairing is by command shape and substrate, not by argv. A tool that
enforces the literal same-argv rule would demand something that cannot exist.

#### Gate

```
$ just check
🚀 Checking all links in markdown files using lychee
...
238/238 claims verified
$ echo $?
0
```

`0` FAIL lines. **All six original `must_fail` controls verified PRESENT with `must_fail: true` and still
failing their evidence** — none weakened, none deleted:
`CONTROL-utm-settings-apple-devices-is-fabricated`, `CONTROL-disposable-is-not-apple-backend`,
`CONTROL-tart-doc-index-oracle`, `CONTROL-tart-cirrus-page-has-no-sshpass`,
`packer-sensitive-hides-secret`, `packer-sensitive-hides-secret-under-debug-log`.

Ledger **237 → 238** (+2 probes, −2 orphan controls, +1 control, 5 repointed). Markers unchanged at **15**.
`00-overview.md` **not touched** — CONFLICT L1 remains correctly routed to 📚 synth.

---

## 🏭 tart-ci — CROSS-AUDIT of 🔐 secrets (13-build-secrets.md)

**Verdict: 🔐 secrets' self-reported defect is CONFIRMED BY EXECUTION, and it is worse than an under-power —
the old pair goes GREEN against a Packer that never emitted a debug log at all. Everything else in `13`
that I could attack, I failed to break. 10 successor claims proposed; whole file dry-runs 44/44, exit 0.**

### 🔴 CONFIRMED (not merely repeated): the `PACKER_LOG=1` pair is causally blind

Run on **separate pipes**, as instructed — not read:

```
$ packer inspect tests/fixtures/packer-sensitive              > out 2> err   # stdout 136B  stderr   0B  exit 0
$ PACKER_LOG=1 packer inspect tests/fixtures/packer-sensitive > out 2> err   # stdout 136B  stderr 845B  exit 0
$ cmp out_plain out_log   ->  byte-identical.  The overlay adds NOTHING to stdout.
```

`tools/verify_claims.py:225` matches `proc.stdout + proc.stderr`, so `plain_FIXTURE_CONTROL` on stdout
satisfies `CONTROL-packer-debug-log-prints-plain-literals` **whether or not the debug log ran.** I proved
that rather than asserting it, by simulating *"a Packer that ignores `PACKER_LOG`"* with `env PACKER_LOG=0`
and re-running the real evidence:

```
[PASS] SIM-old-control-under-PACKER_LOG-0        expect=plain_FIXTURE_CONTROL   <- the control is BLIND
[PASS] SIM-old-negative-under-PACKER_LOG-0       expect=ghp_FIXTURE_SENTINEL    <- the must_fail probe is BLIND
[FAIL] SIM-new-discriminator-under-PACKER_LOG-0  expect=[INFO] Packer version:  <- the successor SEES it
[FAIL] SIM-new-control-under-PACKER_LOG-0        expect=plain_FIXTURE_CONTROL   <- the successor SEES it
[FAIL] MUT-new-negative-is-live                  "CONTROL PASSED — the oracle is broken"   <- successor is live
```

**Both halves of the shipped pair pass with logging switched off.** They are not vacuous in the
*empty-output* sense secrets' §"needs a control" paragraph guards against — stdout is non-empty and really
does print the control literal. They are vacuous in the **causal** sense: no part of the evidence depends
on `PACKER_LOG` having done anything. `packer-sensitive-hides-secret-under-debug-log` therefore asserts a
secret is absent from a debug log it never checked was produced — exactly as `13:299-302` says.

**One refinement to `13:297`, which I could only find by isolating the streams.** It reads
*"`plain_FIXTURE_CONTROL` appears on **stdout**"*, which invites the reading that stderr lacks it. It does
not: under the overlay, the isolated stderr contains `plain_FIXTURE_CONTROL` **and** `<sensitive>` and
**not** the sentinel. That strengthens secrets' argument rather than weakening it — the control literal is
on *both* streams, so matching it can never tell you which one you were reading. The sentence should say
"appears on stdout *as well*", not "appears on stdout".

**The fix, proposed and dry-run green.** `cli-help` spawns `argv` directly, so `["sh","-c","… 2>&1 1>/dev/null"]`
isolates stderr — the first evidence in this repo that can:
`CONTROL-packer-debug-log-stderr-emits-info-banner` (proves the log ran) ·
`CONTROL-packer-debug-log-stderr-prints-plain-literal` (proves the stream is non-empty) ·
`packer-sensitive-hides-secret-in-isolated-debug-log` (`must_fail`; the properly-powered negative) ·
`packer-no-debug-log-on-stderr-when-overlay-disabled` (proves the overlay is the **cause**, written as a
positive echo of a token rather than a bare `must_fail`, because "no `[INFO]` line" is also satisfied by no
output).
→ **`_RULES.md` §5 forbids weakening the old pair, and the old pair is misleading. That collision is
[OQ-29 · NEEDS-HUMAN](macos-ci.open-questions.md).** Whether `sh -c` belongs in `argv` at all is
[OQ-30](macos-ci.open-questions.md).

### 🟢 REFUTATION ATTEMPTED AND FAILED — secrets' *other* new negative probe is sound
I expected to find that secrets had not applied its own lesson to
`g16-injected-secret-never-prints-in-unrelated-variable` (`must_fail`, `env PKR_VAR_pub=ghp_FIXTURE_SENTINEL_AND_MORE`).
The vacuity is real in principle — without the overlay the sentinel is absent anyway (0 occurrences), so
the probe would pass for the wrong reason. **But the discriminator exists:**
`g16-sensitive-masks-value-inside-unrelated-variable`, same `argv`+`env`, `expect="<sensitive>_AND_MORE"` —
a literal that appears **only** under the overlay (`with=1, without=0`). Executed:
```
$ PKR_VAR_pub=ghp_FIXTURE_SENTINEL_AND_MORE packer inspect tests/fixtures/packer-sensitive
  var.pub: "<sensitive>_AND_MORE"     var.sec: "<sensitive>"
```
Same for `packer-debug-log-silent-when-overlay-disabled`, which **does** ship its same-`argv`+`env` positive
control (`CONTROL-packer-log-disabled-still-prints-plain-literals`, `env PACKER_LOG=0`). **No finding.**

### 🟢 Invariant check: all six original `must_fail` claims present and unweakened
21 `must_fail` claims now; the original six are all there
(`CONTROL-utm-settings-apple-devices-is-fabricated`, `CONTROL-disposable-is-not-apple-backend`,
`CONTROL-tart-doc-index-oracle`, `CONTROL-tart-cirrus-page-has-no-sshpass`, `packer-sensitive-hides-secret`,
`packer-sensitive-hides-secret-under-debug-log`), with `expect` and `env` unchanged.
*(My first `grep` said all four masking claims were **missing** — the ledger now pretty-prints `"id": "…"`
with a space. That was my pattern's fault, not a deletion. Re-checked with a JSON parse before reporting.
Reporting a phantom deletion would have been the exact defect this run exists to catch.)*

### 🟢 `PACKER_LOG` value semantics (`13:316`) — CONFIRMED, and it is a trap worth keeping
```
PACKER_LOG=[UNSET]   0B disabled      PACKER_LOG=[off]    845B ENABLED
PACKER_LOG=[]        0B disabled      PACKER_LOG=[false]  845B ENABLED
PACKER_LOG=[0]       0B disabled      PACKER_LOG=[no]     845B ENABLED
                                      PACKER_LOG=[00]     845B ENABLED
                                      PACKER_LOG=[ ]      845B ENABLED
```
Exactly as `13` states. `00` and `off` both **enable** logging: the value is compared against `""`/`"0"`,
not parsed as a boolean. Ledgered as `packer-log-value-off-still-enables-logging`.

### 🟢 D1 — DISCHARGED. `13` now says the template is ABSENT
`ls -d packer` → *No such file or directory*. `13:151` reads **"This template does not exist yet.
`packer/tart-golden-image.pkr.hcl` is **absent from the repo**"**, backed by
`justfile-build-golden-invokes-missing-template` (`file-line` on `Justfile`) and `golden-template-does-not-exist`.
My earlier CONFLICT is closed. Two smaller notes, neither blocking:
- `CONTROL-d1-packer-dir-does-not-exist` greps `ls -1` for the substring `packer`, so it cannot distinguish
  a `packer/` **directory** from a future file named `packer-notes.md` — it would fire on either. The precise
  claim is `golden-template-does-not-exist`. It ships its same-`argv` positive control
  (`CONTROL-ls-prints-repo-root-entries`, expect `Justfile`), so it is sound, merely over-broad.
- `golden-template-does-not-exist` expects the string `No such file or directory`. I checked this is not
  locale-fragile here (`LC_ALL=C` and `LC_ALL=de_DE.UTF-8` both emit it), but it is an **error message**, and
  error messages are not a stable API.

### 🟢 The two `<!-- UNVERIFIED -->` markers at `13:51` and `13:54` — STILL PRESENT, not retired
Re-derived with `sed -n`, not inherited:
```
sed -n '51p'  ->  <!-- UNVERIFIED: reproduced on the host against a UDIF/APFS image via hdiutil, not inside a tart VM
sed -n '54p'  ->  <!-- UNVERIFIED: whether the same holds for `disk_format = "asif"` (macOS 26+), a sparse format
```
Both pinned by new `file-line` claims (`secrets-13-marker-51-still-present`, `secrets-13-marker-54-still-present`)
so neither can be silently deleted to pay down the honesty budget (OQ-01).

### 🟢 G15 — UPHELD, every source citation re-derived against pinned `provisioner.go` (v1.15.4)
| `13` says | I found |
|---|---|
| `:89` uploads via `comm.Upload(remoteVFName, …)` as `varfile_<rand>.sh` | `:272` `fmt.Sprintf("varfile_%d.sh", rand.Intn(9999))`, `:273` `comm.Upload(remoteVFName, r, nil)` ✅ |
| `:90` `chmod 0600` | `:279` `Command: fmt.Sprintf("chmod 0600 %s", remoteVFName)` ✅ |
| `:91` cleanup is an unlink | `:401` `cleanupRemoteFile` issues an unlink, not a shred ✅ |
| `:94` "a successful, non-`skip_clean` build" still leaks | `:383` `if !p.config.SkipClean { cleanupRemoteFile(p.config.envVarFile…) }` ✅ gated exactly as claimed |

### 🟢 SETTLES 🔬 ledger's OQ-09 — `use_env_var_file`'s default is sourced now, not inferred
The **docs page does not state it.** `developer.hashicorp.com/packer/docs/provisioners/shell` says
*"`skip_clean` … **This defaults to false**"* but for `use_env_var_file` says only *"If true, Packer will
write your environment variables to a tempfile…"* — **no default given.** So `13:174`'s `# default` was an
inference from the docs. The **source settles it**:
```
:46   UseEnvVarFile bool `mapstructure:"use_env_var_file"`     <- declared
:103  if p.config.UseEnvVarFile == true {                       <- read
:110  if p.config.UseEnvVarFile == true {                       <- read
:241  if p.config.UseEnvVarFile == true {                       <- read
      (no assignment anywhere)                                  <- so the default is Go's zero value: false
```
Ledgered as `packer-shell-use-env-var-file-has-no-default-assignment`, with a **FETCH_FAILED guard** so an
empty download cannot masquerade as a pass — `cli-help` ignores `curl`'s exit code (OQ-08).

### 🟢 G16 — UPHELD (re-confirmed from my own-file pass): masking is value-based, global, and eats identifiers
`var.unrelated_admin_user` renders as `var.unrelated_<sensitive>_user`. `13:161-163` is correct and
understates it. `ssh_password = "admin"` must stay plain.

### 🟢 G17 — UPHELD, line by line
- `HOMEBREW_GITHUB_PACKAGES_TOKEN`: `grep -rI` across **both** clones → **no matches**.
- `zsh-dotfiles-prep/Brewfile:4` re-derived → `tap "bossjones/tap", "git@github.com:bossjones/homebrew-tap.git"` ✅
- All three repos clone anonymously: `info/refs?service=git-upload-pack` → **200 / 200 / 200**.
- Env-only git rewrite really overrides on-disk config, nothing written:
  `GIT_CONFIG_COUNT=1 … git config --get url.https://github.com/.insteadOf` → `git@github.com:`;
  the same command **without** the env vars returns nothing.
- Homebrew `Manpage.md` really contains *"doesn't require permissions for any of the scopes"* ✅
- `13:8`'s rate limits measured live: unauthenticated core **60**, authenticated core **5000** ✅

### 🟢 `13` cites `Justfile:52-58` for `verify-no-secrets` — re-derived, CORRECT
`sed -n '52p'` → `verify-no-secrets vm:`; `sed -n '58p'` → the `✅ clean:` else-branch. The fenced block
matches the recipe verbatim, including the `|| true` that my earlier cross-audit found missing. All four of
my previous CONFLICTs against `13` are **closed**: owner line now reads `Owner: 🔐 secrets`, `13:217` carries
`|| true`, the Dockerfile splice is gone, and D1 is documented.

---

### secrets - CROSS-AUDIT of tart-core (01, 02)

Posture: try to refute, default to refuted. **I did not edit either file.** 11 new claims proposed
(`.team/proposed/secrets.jsonl`, **26/26 dry-run PASS** for the whole file), 4 mutants run against the two
new negative probes — 3 correctly FAIL, and **the 4th exposed a real defect in `verify_claims.py`** (X-6).

**Verdict: 01 and 02 are the strongest specs I have read in this repo.** Every `file:line` citation into
the local clones is *exact* — `vanilla-tahoe.pkr.hcl:20-21`, `base.pkr.hcl:167`, `builder.go:36`,
`builder.hcl2spec.go:190`, `step_clone_vm.go:24`, `step_run.go:43` — all re-derived with `sed -n` and all
correct. Every quoted FAQ/quick-start sentence is verbatim. 02 already absorbed my `disk_format` CONFLICT
from AUDIT-OWN. Four defects, three of them small, one of them mine to own.

#### X-1 REFUTED · 01:38-39 — the omitted-verb list is wrong, and double-counts `create` 🔴
> *"`tart --help` lists **nine further verbs this table omits** as out of scope: `create`, `get`, `logout`,
> `import`, `export`, `prune`, `rename`, `stop`, `suspend`."*

`create` is **in the table**, at 01:25 (`| \`tart create <name>\` | Build a new VM from scratch |`).
Mechanically:
```
tart --help subcommands (19): clone create delete exec export get import ip list login
                              logout prune pull push rename run set stop suspend
01's table (11):              clone create delete exec ip list login pull push run set
actually omitted (8):         export get import logout prune rename stop suspend
```
**Eight, not nine** — and the ninth slot is filled by a verb the table documents. Off-by-one caused by
listing `create` twice. → claims `tart-help-lists-create-subcommand`, `xaudit-01-table-lists-create-verb`.

#### X-2 REFUTED · 01:63-65 — the guest's auto-login cannot satisfy a **host**-side requirement 🔴
01 says the prebuilt images' `autoLoginUser` is *"directly relevant to the macOS 15+ keychain requirement
(**G8**) below: the prebuilt images boot into a real GUI login session, which is the condition under which
`login.keychain` is unlocked."*

The FAQ attaches that requirement to the process **using** Virtualization.Framework:
> *"there's an undocumented requirement from Virtualization.Framework **(which Tart uses)** to have an
> unlocked `login.keychain` available at the times when running a VM"*

and its auto-login workaround is *"configure automatic log in to **a Mac user account** … this will
maintain a running user session (GUI)"* — the **host's** account. Two independent reasons the inference
fails: (a) a guest cannot unlock the *host's* `login.keychain`; (b) the requirement fires **when starting
the VM**, i.e. strictly *before* the guest's auto-login could run — a precondition of the guest's own boot
cannot be satisfied by that boot. 01:185-189 gets this right ("the **host** running macOS 15"); 01:63-65
contradicts it 120 lines earlier. **The FACT at 01:63 is true** (`autoLoginUser admin` + `/etc/kcpassword`
are in all five `vanilla-*` templates); only the *"directly relevant"* inference is wrong.
→ claims `tart-faq-keychain-requirement-attaches-to-the-tart-process`,
`tart-faq-autologin-mitigation-is-a-host-mac-user-account`, `vanilla-tahoe-presets-autologin-user`,
`vanilla-tahoe-has-passwordless-sudo`.

#### X-3 REFUTED · 02:177 cites `12-tooling-and-agent-loop.md:330`. That line is **blank**. 🟡
The `vnc_port_min`/`vnc_port_max` assertion 02 files a CONFLICT against now sits at **12:349** (spec 12
grew to **577** lines under 🧪 harness's edits). 02's CONFLICT is *substantively right* — 12 does still
assert those fields — but its citation rotted mid-run.
→ `spec12-mentions-vnc-port-min` (stable), `spec12-vnc-port-mention-is-at-349` (`file-line`),
`CONTROL-spec12-line-330-is-not-the-vnc-port-mention` (`file-line`, `must_fail`).
**⚠ ledger: merge the two `file-line` claims only once 12 is frozen**, or a further edit flips them.

#### X-4 · 02:172-177 UPHELD — and I nearly refuted it with poisoned evidence 🟢
*"No `vnc_port*` key appears … anywhere in the plugin's source — including `builder.hcl2spec.go`."*
My first grep returned **two hits** and I was one keystroke from filing a refutation. Both were in
`packer-plugin-tart/logs/{pre,post}_tool_use.json` — **the `pre_tool_use` hook's recordings of the very
grep commands this audit typed.**
```
grep -rIn 'vnc_port' <clone> --exclude-dir=.git                     -> 2 hits, both in logs/
grep -rIn 'vnc_port|VNCPortMin|VNCPortMax' <clone> --exclude-dir=.git --exclude-dir=logs
                                                                    -> ZERO hits.   02 UPHELD
grep -c 'vnc_port' <clone>/builder/tart/builder.hcl2spec.go         -> 0
grep -c 'disable_vnc' <clone>/builder/tart/builder.hcl2spec.go      -> 2
```
`logs/` is **untracked** (`?? logs/`, 0 tracked files), created today at 21:24, and now also contains the
ledger's `ghp_FIXTURE_SENTINEL`. **The instrument that records the search has contaminated the corpus
being searched.** No *live* claim is affected — `_read()` resolves `target` to a single file, never a
directory walk — but any human or agent reproducing a spec's "grep the source" argument by hand will hit
it. → **OQ-32 (NEEDS-HUMAN)**. This is G10's failure mode with a new cause: not a fabricated citation, but
a **fabricated corroboration**.

#### X-5 · the `--graphics` pair was missing its negative half 🟡
`tart-has-no-graphics` proves `--no-graphics` **is present**. Nothing in the ledger proved `--graphics`
**is absent** — which is the entire basis of 02:130-136 and OQ-15. Added
`tart-run-help-has-no-graphics-flag` (`must_fail`, same `argv`), with `tart-has-no-graphics` as its
positive control so "no `--graphics`" cannot be satisfied by empty output. (`--graphics` is **not** a
substring of `--no-graphics`; verified before proposing.) Mutation test: pointing the probe at
`--no-graphics` correctly FAILS.

#### X-6 CONFLICT (→ 🔬 ledger) · `file-line` + `must_fail` inverts an **out-of-range line** into a PASS 🔴
The inversion guard at `tools/verify_claims.py:289` exempts `UNREACHABLE:` and `STRUCTURE:`. `check_line`
returns a bare `line N out of range (file has M)` (**:126**) with **no prefix**, so `must_fail` flips it green.
```
{"kind":"file-line","must_fail":true,"target":"specs/.../12-...md","line":99999,"expect":"vnc_port"}
  -> [PASS]                                   # the line does not exist. The "control" passed.
{"kind":"cli-help","must_fail":true,"argv":["tart-nonexistent",...]}
  -> [FAIL] UNREACHABLE: not on PATH          # correctly NOT inverted
```
`cli-help` is guarded against a missing binary and `doc-contains` against a missing page. **`file-line` is
not guarded against a missing line.** This touches a live claim: **`CONTROL-12-line-607-does-not-exist`
passes today via exactly this path** (12 is 577 lines). Its purpose is served, but its green means
"607 ≥ len(file)", not "607 was fabricated" — and it would keep passing if 12 were truncated to three
lines. My own `CONTROL-spec12-line-330-…` is guarded only by the coincidence that its partner pins line
**349 > 330**. → **OQ-31**. Suggested fix (ledger's call, ~2 lines): a `RANGE:` prefix added to the tuple
at :289. **I did not touch the file.**

#### Corroboration
🏭 tart-ci's **OQ-29**, cross-auditing *my* files, independently reached my AUDIT-OWN finding S-2 — that
`packer-sensitive-hides-secret-under-debug-log` is blind. Two agents, opposite directions, same defect.
That is the rotation working.

#### Scope
Files 01 and 02 **not edited** (`git status` shows tart-core's own modifications only). No `<!-- UNVERIFIED -->`
marker added or removed in either: 01 carries **0** real markers (line 222 is a backticked prose mention,
correctly excluded by the D5′ grep); 02 carries **2**, both of which I re-derived and which must **stay**
(`:135` → OQ-15 `--graphics`; `:207` → the composed example). `.team/claims.jsonl`, `Justfile` and
`tools/verify_claims.py` untouched by me.

### 👑 lead — GB3 characterised by EXECUTION. Ledger's diagnosis was directionally right, numerically wrong.

🔬 ledger warned that `CONTROL-12-line-607-does-not-exist` sits **30 lines from passing** (577 → 607) and
would then emit *"CONTROL PASSED — the oracle is broken"*. I did not take that on trust. Synthetic targets,
run through the real verifier:

```
target = 12-tooling-and-agent-loop.md (577 lines)          -> [PASS]   out of range, correct
target = 700-line file, line 607 = ordinary prose          -> [PASS]   correct — it does NOT fire at 607
target = 700-line file, line 607 = an UNRELATED marker     -> [FAIL]   "CONTROL PASSED — the oracle is broken"
target = same file, expect the SPECIFIC marker literal     -> [PASS]   correct
```

**The control does not fire when the file reaches 607 lines.** `expect` is the bare substring `UNVERIFIED`,
so it fires when line 607 happens to contain **any** `UNVERIFIED` marker — related or not. The failure mode is
not *"the file grew"*; it is **a false alarm on an unrelated marker landing at an arbitrary line number**, which
would scream that the `file-line` oracle is broken when nothing is broken. That is worse than ledger described:
a tripwire that cries wolf teaches its readers to disarm it.

**Fix, dispatched to 🔬 ledger:** keep `must_fail` + `line: 607`, change `expect` from `"UNVERIFIED"` to the
specific literal ``<!-- UNVERIFIED: `--vnc-experimental` ``. Then: out-of-range passes, ordinary line 607
passes, and it fires **only if the prior lead's fabricated citation ever becomes genuinely valid** — precisely
the event worth screaming about. The claim prose must also stop asserting *"line 607 does not exist"* and start
asserting *"the vnc marker is not at line 607"*, which is what it actually tests.

**Meta-lesson.** Both the original control and ledger's critique of it were reasoned about rather than executed.
Running it against three synthetic files took ninety seconds and produced a different answer than either.
**This is the third time in this run that execution beat reading** (Defect D, the `:340 → :359` drift, and now
this). The `file-line` kind exists because prose citations rot; it turns out `file-line` *claims themselves*
rot the same way, and only a fixture can tell you.

---

### 🔬 ledger — GB3 + GB4 remediation

#### GB3 — `CONTROL-12-line-607-does-not-exist` reshaped. **My "30 lines from passing" was WRONG.**

I claimed the control was approaching accidental validity as `12-tooling-and-agent-loop.md` grew toward
607 lines. That is not how it fires. The lead characterised it by execution; I reproduced it against
synthetic 700-line files before touching anything:

```
[PASS] OLD-expect-UNVERIFIED-plain-line-607                  700-line file, ordinary prose at 607  -> does NOT fire
[FAIL] OLD-expect-UNVERIFIED-unrelated-marker-at-607         700-line file, UNRELATED marker at 607
         CONTROL PASSED — the oracle is broken                 <-- FALSE ALARM
[PASS] NEW-expect-specific-literal-unrelated-marker-at-607   same file, specific literal            -> correct
[FAIL] NEW-expect-specific-literal-genuine-marker-at-607     vnc marker genuinely at 607
         CONTROL PASSED — the oracle is broken                 <-- correct: scream
```

Because `expect` was the bare substring `UNVERIFIED`, the control fired on **any** unrelated marker
landing at line 607. File *length* was never the trigger — an out-of-range line yields a plain `False`,
which `must_fail` inverts, so growth alone can never fire it. **A tripwire that cries wolf teaches its
reader to disarm it.**

Fixed: `kind=file-line`, `must_fail=true`, `line=607` all retained; `expect` is now the specific literal
``<!-- UNVERIFIED: `--vnc-experimental` ``. The claim prose now says what is actually asserted — *the vnc
marker is NOT at line 607*, the exact citation the prior (Haiku) lead pass fabricated — not "line 607 does
not exist", and records that the file is **577 lines** today (535 when written).

#### GB4a — the one uncontrolled `absent` claim, and the xaudit-09 merge

`prep-makefile-has-no-smoke-target` was the only `absent` record with no positive control on its target.
Added `CONTROL-prep-makefile-has-a-style-target` (`file-contains`, `expect: "contrib/style.sh"`, a recipe
body the prep Makefile genuinely contains at line 12).

Merged from `.team/proposed/utm.jsonl`: `xaudit-09-no-macos-asdf-installer-script-on-disk` (`must_fail`
`cli-help` over `ls .chezmoiscripts/`) with **both** its positive controls
(`CONTROL-xaudit-scripts-dir-lists-macos-mise-installer`, `CONTROL-xaudit-scripts-dir-lists-ubuntu-asdf-installer`),
plus the trap claim `xaudit-09-ignore-file-does-contain-macos-install-asdf`. Verified by `ls`: the two
control literals are present, `02-macos-install-asdf` is not. The two controls make the absence
**macOS-specific** and prove the listing is non-empty — falsifiable in both directions.

`no-macos-asdf-installer` is **kept**, not deleted: it now carries the trap claim as its control, which
documents that its `02-` prefix is load-bearing (`.chezmoiignore.tmpl` contains the substring
`macos-install-asdf` via `run_onchange_after_50-macos-install-asdf-plugins.sh`). Drop the prefix and it
fails. The direct probe supersedes it as *evidence*; the pair now records *why* the indirect one survives.

**I did NOT merge utm's `xaudit-09-git-grep-fatal-line-contains-a-colon`** — it is correct and its finding
is already landed, but its `expect` is a bare `":"`, and the lead verified that zero claims retain that
literal. Reintroducing it would contradict a property the lead checked. → 🖥 utm / 👑 lead to adjudicate.

#### GB4b — enforced in the tool, not in prose

**Brief retraction, recorded in the ledger prose and in `verify_claims.py`'s docstring:** `must_fail`
JOB 2 stated the positive-control requirement for `cli-help` only. **It is a property of ALL negative
evidence, `absent` included.** An `absent` claim over an empty file verifies happily — reproduced:

```
$ uv run tools/verify_claims.py <scratch>   # absent over a 0-byte file, expect=HOMEBREW_GITHUB_PACKAGES_TOKEN
2/2 claims verified
```

`tools/verify_claims.py` now rejects structurally, **before any evidence runs**. Every `kind=absent`
record and every `must_fail` `cli-help` probe must carry a `control` naming a positive claim id in the
same ledger. `doc-index` / `doc-contains` are exempt: those four `CONTROL-*` records *are* the oracle
guards and have no partner by construction.

Enforcement verified against four scratch ledgers, not assumed:

```
(1) absent, no `control`          -> STRUCTURAL REJECTION ... carries NEGATIVE evidence but no `control` field   EXIT=4
(2) `control` names unknown id    -> DANGLING: `control` names 'does-not-exist', which is not a claim id ...     EXIT=4
(3) `control` names a must_fail   -> BAD: `control` names 'NEG', which is itself a must_fail claim ...           EXIT=4
(4) doc-index oracle, no partner  -> 1/1 claims verified                                                          EXIT=0
```

Check (3) is mine, beyond the ruling: a control that is itself a negative proves nothing. Backfilled
`control` on **28** records (13 `absent`, 15 negative `cli-help`); `xaudit-09-...` carries a **list** of two.
Before backfill the tool rejected the live ledger with **27** offenders — that rejection is the proof the
rule is real rather than aspirational.

`uvx ruff check tools/verify_claims.py` → `All checks passed!`

#### Gate

```
$ just check
🚀 Checking all links in markdown files using lychee
[200] file:///Users/bossjones/dev/bossjones/macos-ci/specs/macos-ci.md
[200] file:///Users/bossjones/dev/bossjones/macos-ci/specs/macos-ci/11-sources.md
   [... 567 lines elided: lychee [200] lines + PASS lines + marker list ...]
243/243 claims verified
$ echo $?
0
```

`0` FAIL lines. All six original `must_fail` controls PRESENT with `must_fail: true` and still failing
their evidence — none weakened, none deleted. Ledger **238 → 243**. Markers unchanged at **15**.
`00-overview.md` untouched; CONFLICT L1 remains 📚 synth's.

**One consequence the lead should know.** The structural check resolves `control` ids *within the ledger
being checked*, as ruled. So `uv run tools/verify_claims.py .team/proposed/<role>.jsonl` now exits `4` for
any proposal file whose negatives name controls that live in `claims.jsonl`. Dry-running a proposal in
isolation therefore requires the proposal to carry its own controls — which is arguably the right
discipline, but it is a workflow change for every auditor, and it landed without them being told.
→ 👑 lead: propagate, or authorise resolving `control` against the union with `claims.jsonl`.

### 🔴 GATE-BLOCKER 5 — the GB4 fix exempted a KIND where it should have exempted the ORACLE RECORDS

**My own lesson, applied incompletely — by me.** The lead's GB4 dispatch said *"exempt the four `CONTROL-*`
doc-index/doc-contains oracles."* 🔬 ledger implemented the exemption on the **kind**:

```python
if kind in ("doc-index", "doc-contains"):
    return False   # "they ARE the controls ... and have no partner by construction"
```

That justification is **true for `CONTROL-*` oracle records and false for a `must_fail doc-contains`
negative probe.** Enumerated every `must_fail` `doc-*` record in the merged ledger:

```
CONTROL-utm-settings-apple-devices-is-fabricated       doc-index     oracle=True   control=<<ABSENT>>   OK
CONTROL-disposable-is-not-apple-backend                doc-contains  oracle=True   control=<<ABSENT>>   OK
CONTROL-tart-doc-index-oracle                          doc-index     oracle=True   control=<<ABSENT>>   OK
CONTROL-tart-cirrus-page-has-no-sshpass                doc-contains  oracle=True   control=<<ABSENT>>   OK
CONTROL-licensing-page-never-says-commercial-use-free  doc-contains  oracle=True   control=<<ABSENT>>   OK
CONTROL-tart-blog-is-outside-doc-index-domain          doc-index     oracle=True   control=<<ABSENT>>   OK
CONTROL-tart-faq-does-not-name-the-disk-file           doc-contains  oracle=True   control=<<ABSENT>>   OK
utm-no-tso-toggle-on-apple-virtualization              doc-contains  oracle=FALSE  control=<<ABSENT>>   <-- HOLE
```

Seven oracles, correctly exempt. **Exactly one negative probe, silently unguarded.** Its own `claim` prose
reads: *"Paired with `CONTROL-utm-apple-virtualization-page-has-toggles`; **without that control an empty page
would satisfy this probe**."* The control exists and is correct (`doc-contains`, `expect: "Balloon Device"`).

**The pairing is stated in prose and enforced nowhere.** Break or delete that control and the gate stays green
at `243/243` while the negative probe becomes vacuous — a `doc-contains` probe over a zero-text indexed page
passes silently. **This is the exact failure GB4 was raised to eliminate, and it reappeared inside GB4's own
exemption clause.** It is also **OQ-19**; GB5 and OQ-19 are the same defect and close together.

**Fix → 🔬 ledger:** exempt the *record*, not the *kind*.
```
needs_control(c) := (c.kind == "absent") or (c.must_fail and c.kind in ("cli-help","doc-contains"))
                    and not c.id.startswith("CONTROL-")
```
plus `"control": "CONTROL-utm-apple-virtualization-page-has-toggles"` on the utm record. `just check` must
still exit 0 at 243/243. **A failure there is a finding, not a bug to silence.** No control may be weakened
or deleted to make it pass.

**The generalisation, now stated for the third time and finally enforced:** *a rule the tool does not enforce
is a rule that will be forgotten* — **and that includes the exemption clauses of the rule itself.** Every
exemption is a place where the enforcement stops and prose resumes. GB2 scoped the rule too narrowly to
`cli-help`; GB4 fixed that and scoped its *exemption* too broadly to a kind; GB5 scopes the exemption to the
records that genuinely have no partner. Each round, the hole moved one level up the abstraction. **The
invariant is not "negatives need controls." It is: every claim that can be satisfied by the absence of
evidence must name the positive claim that proves the probe can see.**

---

### 🔬 ledger — GB5 remediation

**The lead is right, and the diagnosis is exact.** GB4's instruction was *"exempt the four `CONTROL-*`
doc oracles"*. I exempted the `doc-contains`/`doc-index` **KIND** instead. That is true of the oracle
records and **false of one negative probe**:

```
utm-no-tso-toggle-on-apple-virtualization   kind=doc-contains  must_fail=true  control=<<ABSENT>>
  expect "TSO" on utm /settings-apple/virtualization/
  its OWN prose: "Paired with CONTROL-utm-apple-virtualization-page-has-toggles;
                  without that control an empty page would satisfy this probe."
```

The pairing was **stated in prose and enforced nowhere**. Break or delete
`CONTROL-utm-apple-virtualization-page-has-toggles` and the gate stayed green at `243/243` while the probe
went silently vacuous — a page with **zero indexed text** satisfies *"the page does not say TSO"* exactly
as well as an honest page does. That is precisely the failure GB4 was raised to eliminate, reproduced by
me, inside my own fix for it. **A rule the tool does not enforce is a rule that will be forgotten —
including my own exemption clause.** GB5 and **OQ-19** were the same defect; both are now closed.

#### The predicate — and one deviation from the ruling, deliberate

The lead's proposed exemption was `id.startswith("CONTROL-")`. **I did not implement that**, because two
genuine negatives are named `CONTROL-*` by history, and a bare name check would have silently exempted
them — re-opening GB4 while closing GB5:

```
CONTROL-d1-packer-dir-does-not-exist                  kind=cli-help  must_fail=true   <- a real negative probe
CONTROL-tart-builder-clone-step-ignores-disk-format   kind=absent                     <- a real negative probe
```

**A name is not a warrant.** The exemption is therefore on the *oracle record*: `CONTROL-*` **and** a doc
kind. Implemented:

```python
is_oracle_control = id.startswith("CONTROL-") and kind in ("doc-index", "doc-contains")
if is_oracle_control:            return False
if kind == "absent":             return True
return must_fail and kind in ("cli-help", "doc-contains", "doc-index")
```

`must_fail` `doc-index` probes are covered too, per the lead's "get the predicate right for the next one":
today every such record is a `CONTROL-*` oracle, so it is moot — but the predicate no longer depends on
that remaining true.

#### The rejection, before the backfill

With the predicate fixed the tool rejected the live ledger naming **exactly one** record — the count the
lead predicted:

```
STRUCTURAL REJECTION — negative evidence without a positive control:
  utm-no-tso-toggle-on-apple-virtualization: kind='doc-contains' must_fail carries NEGATIVE evidence
  but no `control` field. ...
1 offending claim(s).
EXIT=4
```

Then backfilled `"control": "CONTROL-utm-apple-virtualization-page-has-toggles"` (verified present,
`doc-contains`, `must_fail=false`, `expect: "Balloon Device"`), and recorded the GB5 finding in that
probe's own claim prose so it re-executes with the evidence.

#### Adversarial self-tests — four, all executed

```
(A) must_fail doc-contains negative probe, no control      -> STRUCTURAL REJECTION ...   EXIT=4
(B) CONTROL-* doc oracles, no control field                -> 2/2 claims verified        EXIT=0
(C) must_fail doc-index probe NOT named CONTROL-*          -> STRUCTURAL REJECTION ...   EXIT=4
(D) CONTROL-*-named cli-help negative (name is no warrant) -> STRUCTURAL REJECTION ...   EXIT=4
```

(C) and (D) are mine, beyond the ruling. (D) is the one that would have bitten.

`uvx ruff check tools/verify_claims.py` → `All checks passed!`

#### Gate — count held at 243/243, nothing weakened to get there

```
$ just check
🚀 Checking all links in markdown files using lychee
[200] https://github.com/bossjones/zsh-dotfiles | OK (cached)
[200] file:///Users/bossjones/dev/bossjones/macos-ci/specs/macos-ci/00-overview.md
   [... 572 lines elided: lychee [200] lines + PASS lines + marker list ...]
243/243 claims verified
$ echo $?
0
```

`0` FAIL lines. Ledger **243 → 243** (no claim added or removed; one `control` field backfilled, 28 → 29).
All six original `must_fail` controls PRESENT with `must_fail: true` and still failing their evidence —
none weakened, none deleted, none touched. Markers unchanged at **15**. `00-overview.md` untouched;
CONFLICT L1 remains 📚 synth's.

**OQ-19** flipped `NEEDS-HUMAN` → `ANSWERED`, with a `**Resolution:**` appended *inside* its block
(append-only; no other agent's block edited). Its residual point stands and is worth keeping: `STRUCTURE:`
distinguishes *page gone* from *sentence gone*. It was never a guard against *page empty*. **The control
is.**

**Still open from GB4, unchanged:** `control` ids resolve within the ledger being checked, so
`uv run tools/verify_claims.py .team/proposed/<role>.jsonl` exits `4` for any proposal whose negatives name
controls living in `claims.jsonl`. → 👑 lead to propagate or authorise union-resolution.

---

### 📚 synth — CROSS-AUDIT of the ledger

**Charge: the ledger went 50 → 243. Is it load-bearing, or is it padded?**

**Verdict: overwhelmingly load-bearing. The padding is real but small — 5 byte-duplicate records and
roughly a dozen inert existence probes, out of 243. The 24 `must_fail` records and the 26 claims serving
as their controls are the substance, and they are the reason I could not refute much.** But the ledger has
**three structural gaps**, and the most important one guards `CLAUDE.md`'s very first settled fact.

I am the wrong agent to be charitable here, so I tried to break it, not to praise it.

#### What is genuinely load-bearing

Measured, not asserted:

```
must_fail probes                              24
claims naming a control                       29
distinct claims serving as a control          26
cli-help claims whose prose names its partner 24     <- the "a flag in --help proves it parses" discipline
```

Those 24 paired `cli-help`/`doc-contains` records are the ledger's best work. `utmctl-start-help-lists-disposable`
(the flag parses) sitting next to `utmctl-disposable-is-qemu-only` (the docs say it cannot work), with each
naming the other in prose, is a claim that **teaches its reader why it is not enough**. That is not padding.
The `packer-sensitive-*` family observes *behaviour* — a secret redacted from real `packer inspect` output,
under three distinct `PACKER_LOG` overlays, each with a positive control on the same argv proving the probe
would have shown the secret. Those seven records are worth more than the other 236 combined.

#### The padding, named

**5 byte-duplicate evidence groups** — identical `kind`+`target`+`expect`+`line`+`env`+`argv`, two ids:

| ids | note |
|---|---|
| `d1-justfile-44-invokes-absent-template` / `justfile-build-golden-invokes-missing-template` | pure duplicate |
| `d2-justfile-has-no-build-ipsw-recipe` / `justfile-has-no-build-ipsw-recipe` | pure duplicate |
| `vanilla-tahoe-sets-admin-password` / `vanilla-tahoe-ssh-password-is-plain-admin-at-line-20` | pure duplicate |
| `tart-diamond-tier-12-per-core-per-year` / `tart-diamond-tier-grants-unlimited-workers-not-cores` | pure duplicate |
| `tart-vm-location-documented` / `tart-faq-page-exists` | duplicate **and worse — see below** |

Harmless to correctness, but they inflate `243` by 5, and `243/243` is the number the board reports to a
human. **A count that includes duplicates is a count that flatters.** → 🔬 ledger: dedupe, and let the
number fall. A ledger that shrinks because it got honest is the whole point of this run.

**🟡 CONFLICT S1 — `tart-vm-location-documented` is a claim whose prose overclaims its own evidence kind.**
Its `claim` reads *"tart's FAQ **documents** `~/.tart/vms/` as the artifact location, which is what
`just verify-no-secrets` scans."* Its evidence is `doc-index`, `expect: "/faq/"` — which proves **the FAQ
page exists**, and nothing whatever about `~/.tart/vms/`. The tool's own docstring draws exactly this line:
*"doc-index proves a page exists; doc-contains proves the page says it."* The sentence is true — but it is
`tart-faq-documents-vms-directory` (`doc-contains`) that makes it true, and that record already exists.
This one is a `doc-index` claim wearing a `doc-contains` claim's prose. It is not a false claim; it is a
**mislabelled** one, and mislabelling is how `47/47` and `4 pruned dead URLs` survived their cross-checks.
→ 🔬 ledger: retire it, or rewrite its prose down to what `/faq/` in the index actually proves.

**~12 inert existence probes.** `tart-clone-verb-exists`, `tart-delete-verb-exists`, `tart-pull-verb-exists`
and the `*-page-exists` `doc-index` family. No decision in any spec turns on whether `tart` has a `pull`
verb. I flag them and then **defend most of them**: they are cheap, they pin the CLI surface of a specific
binary (`tart-version-is-2-32-1` is the canary that invalidates all 92 `cli-help` records at once if the
host tart changes — an unusually well-designed claim), and the `*-page-exists` records are what the
`doc-contains` records degrade *into* when a page moves, keeping "the page vanished" distinguishable from
"the sentence vanished". Verdict: **not trivia, but not worth their line count either.** No action.

#### The three gaps that matter — filed as OQ-33, OQ-34, OQ-35

**🔴 GAP 1 (OQ-33) — the control requirement has a hole exactly the shape of GB1, and G1 is standing in it.**
`needs_control()` fires on `absent`, and on `must_fail` + (`cli-help`|`doc-contains`|`doc-index`). It keys on
the **flag**, not on what the `expect` string **means**. So:

```
{"id":"no-terraform-provider-at-cirruslabs-tart","kind":"cli-help","expect":"404", ...}   # must_fail unset
```

is a **negative existence claim wearing a positive record's clothes**, and the enforcement never fires. I
executed the hole rather than arguing it:

```
uv run tools/verify_claims.py <one such record, no `control` field>   ->  1/1 verified, EXIT 0
```

It is not vacuous *today*. But if the registry moves `/v1/providers/`, **both probes keep printing `404`,
both keep passing**, and the ledger now "proves" no Terraform provider exists when all it proves is that an
endpoint moved. `STRUCTURE:` was invented to stop precisely this for `doc-contains`; there is no
`STRUCTURE:` for an HTTP probe. **G1 is the first settled fact in `CLAUDE.md` and the load-bearing premise
of the ADR I own.** It rests on two uncontrolled negatives. The fix is one record, which I confirmed passes:

```
curl -sS -o /dev/null -w '%{http_code}' https://registry.terraform.io/v1/providers/hashicorp/aws   -> 200
```

**🔴 GAP 2 (OQ-34) — the UTM half of G1 has zero claims.** `CLAUDE.md:17` asserts *"No Terraform provider
exists for tart **or for UTM**"* as a fact that must not be re-litigated. Every terraform record in the
ledger probes `cirruslabs/*`. Nothing probes UTM. A confident, uncheckable, do-not-re-derive instruction
holding no evidence **is the shape of G10**, and G10 is why this run exists. The better evidence already
sits in `05` and in my own ADR — the maintainer's *"a long way off"* on `utmapp/UTM#3618` — and no evidence
kind can reach a GitHub discussion, so it was never banked.

**🔴 GAP 3 (OQ-35) — the verifier is the one artifact in this repo with no verifier.**
`verify-claims-missing-file-is-unreachable` is `file-contains` over `tools/verify_claims.py`: it greps the
**source** for the string `UNREACHABLE: missing file:`. Its prose asserts a **behaviour**. Move that literal
into a comment, delete the `except FileNotFoundError` handler, and the claim stays green while
`CONTROL-12-line-607-does-not-exist` silently starts passing for the wrong reason. **Zero claims execute the
tool.** Its three trust-bearing behaviours — `must_fail` inversion, `UNREACHABLE:`/`STRUCTURE:`
non-inversion, `needs_control()` rejection — were adversarially tested by 👑 lead **by hand** and recorded
**as prose on the board**. That is the evidence class of Defect A ("the previous board faked the gate with a
bracketed paraphrase"), differing only in the honesty of the transcriber. Each behaviour is one `cli-help`
record over a checked-in fixture ledger. I ran one:

```
uv run tools/verify_claims.py <ledger: one control-less `absent` record>
  -> STRUCTURAL REJECTION — negative evidence without a positive control
  -> EXIT 4
```

#### My own near-miss, reported against myself

Writing the D5 retraction into `11-sources.md`, I reproduced the raw `grep -rh 'UNVERIFIED' specs/` commands
in a fenced block. Those lines carry the bare token without the backticked `<!-- UNVERIFIED` form, so
`Justfile:63`'s discriminator **counted them as real markers**: the budget went **15 → 19** silently. The
gate would still have passed — `just check` does not diff the count — and the inflation would have been
found only by the lead's manual comparison against the baseline.

I rewrote the section to describe the greps instead of printing them, and the count returned to **15**.

**This is OQ-05, demonstrated.** D5′ resolved that `Justfile:63` is *"sound today, but fragile: a line
carrying a real marker **and** a backticked mention would be silently dropped."* The symmetric hazard is the
one I hit: **a document that discusses the marker syntax cannot be written without perturbing the metric
that counts it.** The honesty budget is measured by a `grep` that the retraction log is obliged to trip. It
happens that I inflated rather than deflated it, which is the safe direction, and I caught it because I
measured after editing rather than before. *A budget you can pay down by editing punctuation is not a
budget* — and one you can inflate by quoting a command is not one either. → 👑 lead: OQ-05 is not
theoretical.

#### Files I own — every ledger CONFLICT closed

| | Finding | Resolution |
|---|---|---|
| **L1** | `00:52` restated RETRACTED G10 as fact (*"4 pruned dead URLs"*) | ✅ rewritten to **"No dead links"**, linked to the G10 retraction. Guarded by `synth-07-appendix-declares-no-dead-links` |
| **L2** | `00:56` invented a `[404]` grade `11` explicitly does not have | ✅ now `meaty/thin/cited-as-exclusion`. Guarded by `synth-00-overview-grades-match-11-sources` |
| **L3** | `11:150` attributed to Packer's docs a default the page never states | ✅ **upheld against the page.** `skip_clean` and `expect_disconnect` state defaults; `use_env_var_file` never does. Reworded to say *inference*, citing **OQ-24**. New claim `synth-packer-shell-page-documents-skip-clean-default` pins the documented half |
| **L4** | `11:13`,`:178` "47/47 URLs return 200" — stale, unverifiable | ✅ frozen count replaced by the live check (`just link-check`), citing **OQ-25** |
| **L5** | `10:75` "Diamond custom" drops the per-core rate | ✅ now **$12 per CPU core per year**, unlimited *Workers* not *cores*. Plus the page's **internal inconsistency** (*"4 hosts for Orchard"* vs *"4 Orchard Workers"*), a NEW finding pinned by `synth-tart-licensing-says-4-hosts-for-orchard` |
| **D3** | `00:58` credited `13-build-secrets.md` to `harness` | ✅ → `secrets`. Guarded by `synth-00-overview-credits-13-to-secrets` |
| **note** | `00:67` called the pass "docs-only", never mentioned the ledger | ✅ scope note rewritten: three layers (citations → markers → ledger), naming `just check` as the only definition of done |
| **D5/G13/G9** | retractions unrecorded in `11-sources.md` | ✅ new section **"Further retractions — G10 was not the only one"**, one subsection each. G10's own heading and anchor left untouched (`06` and `07` link to it) |

`specs/macos-ci.md`: **untouched.** Plan-format contract re-verified — all 11 headings, exact order.

**Proposals:** `.team/proposed/synth.jsonl` — **5 claims, dry-run 5/5 PASS, exit 0.** Deliberately five. My
own audit above condemns a ledger padded with easy claims, and it would be incoherent to file twenty. Each
either pins an external fact no record covers (L3, L5) or guards a sentence that was **demonstrably wrong at
HEAD** and would otherwise regress silently (L1, L2, D3). No verb-exists probes.

**Gate after my edits:** `just check` → `EXIT=0` · `243/243 claims verified` · `0 [FAIL]` · `274` links, all
`[200]`, `0` non-200 · markers **15**, unchanged.

#### 📚 synth — round 2: the two gaps in `11-sources.md`, closed

Both confirmed present-and-missing, both now written. **But the lead's grep evidence did not reproduce**,
so I re-derived before editing rather than acting on it.

**🟡 CONFLICT S2 — the lead's two `grep -c` counts are wrong.** Both were cited as `-> 0`:

```
grep -ciE "packer.*installed|1\.15\.4|not privileged" specs/macos-ci/11-sources.md   -> 1   (not 0)
grep -ciE "negative evidence|positive control|JOB 2"  specs/macos-ci/11-sources.md   -> 2   (not 0)
```

The matches are incidental — `:143` mentions `v1.15.4` in passing, and `:231`/`:249` use the words
"positive control" while describing G13 and G9. **The lead's conclusion was right and the lead's evidence
was wrong**, which is the failure mode one rung below a false conclusion: a grep that returns 0 for the
wrong reason is indistinguishable from one that returns 0 for the right one. The correct probe is for the
*retraction*, not for its vocabulary — `grep -in 'G14' → no mention`, `grep -inE 'GB2|GB4|GB5|master
brief' → no mention`. Filed per §1: *the brief is not privileged over the evidence*, and neither is the
lead. → 👑 lead, informational.

**G14 — written.** New subsection *"G14 — the brief asserted a host fact that a one-word command
refuted."* `packer version` → `Packer v1.15.4`; `just --summary` carries no `doctor` recipe. The detail I
kept because it is the sharpest thing in the whole run: **`packer-is-installed` was already passing when
the draft asserting packer was absent got written.** The evidence was green, in-repo, and the prose
contradicted it anyway. Backed by `synth-packer-version-is-1-15-4` (stronger than `packer-is-installed`,
which expects only `Packer v1.` and would survive any 1.x) and `synth-justfile-has-no-doctor-recipe`
(negative → ships `synth-justfile-has-check-recipe` as its positive control on the same file).

**The master brief — written as ONE retraction with its progression**, per instruction. GB2 (the rule is a
*logical impossibility* for a `grep -c` probe: a true negative implies empty output) → GB4 (same hazard,
unguarded, for `absent`; and a `must_fail` control whose target file was **deleted** went green, because
the missing-file handler lacked the `UNREACHABLE:` prefix) → GB5 (the fix exempted the `doc-contains`
**kind** instead of the **oracle records**, stranding `utm-no-tso-toggle-on-apple-virtualization` behind
prose). The stated lesson: **each round the hole moved one level up the abstraction; every exemption
clause is a place where enforcement stops and prose resumes.** The invariant is recorded in its general
form — *every claim satisfiable by the absence of evidence must name the positive claim that proves the
probe can see* — and located in the tool, not the brief.

**I re-derived the progression at HEAD instead of transcribing it.** Two of the three hazards are already
closed, and saying "GB4 went green" in the present tense would have been false:

```
absent claim, no `control` field                  -> exit 4   STRUCTURAL REJECTION
must_fail doc-contains, no `control` field        -> exit 4   GB5 hole, closed
must_fail file-line, target file DELETED          -> exit 3   UNREACHABLE, never inverted -- GB4 hole, closed
```

So `11-sources.md` records GB4's deletion hazard as **history** ("went green", past tense, because the
handler then lacked the prefix), not as a live defect. A retraction log that misreports a fixed bug as
live is a retraction log nobody will trust twice.

**🔴 GAP 4 (OQ-36) — and it is the same hole, one level up, for the fourth time.** While verifying GB4 I
defeated its fix. `check_structure` proves a `control` **exists**; it never proves the control probes the
**same substrate**:

```
{"id":"neg","kind":"absent","target":"<EMPTY file>","expect":"ansible","control":"pos"}
{"id":"pos","kind":"file-contains","target":"Justfile","expect":"build-golden:"}
  -> 2/2 claims verified, EXIT 0
```

`neg` passes vacuously against an empty file. `pos` passes for an unrelated reason. Every structural check
is satisfied. **`control` is a pointer with no semantics.** This is precisely the shape the brief's own
retraction describes — enforcement moved outward, and the new exemption became the soft spot. It is not
believed to be live (all 13 `absent` records were hand-audited when GB4 landed), but *"hand-audited once"*
is the property GB4 existed to stop relying on. Note the fix is **not** `control.target == claim.target`:
that is right for `absent`, and wrong for the `grep -c` shape GB2 retracted, which *cannot* share `argv`
with its control. → 🔬 ledger.

**Re-confirmed for the lead, by grep, not by memory:** `00-overview.md` L1 (no dead-URL residue), L2 (no
`[404]` grade; `:56` reads `graded meaty/thin/cited-as-exclusion`), D3 (`:58` credits `13` to `secrets`) —
all three genuinely fixed. G19's sitemap exception is present in `11` at `:54-55` (*"It does not cover
`/packer/integrations/**`… 0 of the 337"*), with the `curl`-not-grep verification instruction intact.

**Proposals:** `.team/proposed/synth.jsonl` — now **8 claims, dry-run 8/8 PASS, exit 0** (5 from round 1,
3 here, one of which is a required positive control).

**Gate:** `just check` → EXIT 0 · 243/243 · 0 `[FAIL]` · 0 non-200 links · markers **15**, unchanged.

---

### 🔬 ledger — GAP1 / GAP3 / S1 / dedupe remediation

**Ledger 243 → 246.** −6 records (5 byte-duplicate groups + one source-grep claim), +9 executed claims.
`just check` exit `0`, `246/246`, 0 FAIL lines, markers unchanged at **15**.

#### GAP3 / OQ-35 — the verifier had no verifier. It does now. 🔴 the most important of the three

The lead's indictment is correct, and it lands on the ledger, not on the lead.
`verify-claims-missing-file-is-unreachable` was `file-contains` over `tools/verify_claims.py`: it grepped
the **source** for `UNREACHABLE: missing file:` while its prose asserted a **behaviour**. Move that literal
into a comment, delete the `except FileNotFoundError` handler — the claim stays green. **Zero claims
executed the tool.** Its three trust-bearing behaviours were adversarially tested by hand and recorded as
prose on the board. *That is the evidence class of Defect A. It differs only in the honesty of the
transcriber, and honesty is not an evidence kind.*

Five checked-in fixture ledgers now live at `tests/fixtures/verifier/`; nine `cli-help` claims **execute**
the tool against them and assert on its real stdout/stderr:

```
[PASS] verifier-missing-file-emits-unreachable                    absent target -> "UNREACHABLE: missing file:"
[PASS] verifier-missing-file-is-not-inverted-into-a-pass          ...and must_fail does NOT invert it
[PASS] verifier-mustfail-inverts-a-plain-failure                  out-of-range line -> inverted -> "1/1 claims verified"
[PASS] verifier-rejects-an-uncontrolled-negative                  the real "STRUCTURAL REJECTION" message
[PASS] verifier-uncontrolled-negative-never-reaches-evaluation    "claims verified" never printed: a gate, not a warning
[PASS] verifier-accepts-a-wellformed-pair                         a CONTROLLED negative IS admitted -> "2/2 claims verified"
[PASS] CONTROL-verifier-oracle-fixture-executes                   the oracle fixture really runs
[PASS] verifier-exempts-oracle-control-from-structural-check      ...and a CONTROL-* doc oracle is NOT rejected
```

Every negative probe carries its positive control **on the same argv** — my own invariant, applied to
myself. Two design notes:

- `CONTROL-verifier-oracle-fixture-executes` asserts a **claim id**, not `1/1 claims verified`. A network
  outage would make the inner `doc-index` `UNREACHABLE` and a count-based control would go vacuous.
- `verifier-accepts-a-wellformed-pair` is the complement of the rejection claim: together they prove the
  gate is **discriminating**, not a blanket refusal. A rejecter that rejects everything is not a checker.
- The `wellformed-pair` fixture initially FAILED: its `absent` claim searched the very file that contains
  its own `expect` token. A ledger that greps itself can never satisfy `absent`. Retargeted.

`CONTROL-12-line-607-does-not-exist` now carries `"control": "verifier-mustfail-inverts-a-plain-failure"`.
Its dependence on inversion is proved by execution, not by hand-testing. The source-grep claim is
**deleted**, not repaired — it could never have proved what it said.

#### GAP1 / OQ-33 — controlled. And I did **not** tighten the predicate, deliberately.

`no-terraform-provider-at-cirruslabs-{tart,orchard}` are `cli-help`, `expect: "404"`, `must_fail` **unset**
— so `needs_control()` never fires. It keys on the **flag**, not on what `expect` **means**. Reproduced
against a deliberately-moved endpoint:

```
[FAIL] CONTROL-registry-serves-known-provider-MOVED   .../v1/MOVED/hashicorp/aws   did not emit '200'
[PASS] no-provider-probe-MOVED                        .../v1/MOVED/cirruslabs/tart -> still 404, still PASSES
1/2 claims verified   EXIT=2
```

**The probe passes while proving nothing. Only the control turns the gate red.** Added
`CONTROL-terraform-registry-serves-a-known-provider` (`.../v1/providers/hashicorp/aws` → `200`, verified
live) and wired it as the `control` of both probes. G1 is the first settled fact in `CLAUDE.md`; it is no
longer defended by two probes a URL change would turn into decoration.

`check_structure()` also now validates a `control` **whenever present**, not only when required — otherwise
these two positives would name a partner nobody ever checked. Proven: a positive claim naming a nonexistent
control exits `4`.

**On tightening `needs_control()`: I cannot do it without false positives, and I am saying so plainly
rather than shipping a clever heuristic.** `expect` matching `^[45]\d\d$` misfires on any claim whose
subject legitimately *is* a 4xx page. `argv` containing `%{http_code}` misses `grep -c` returning `0`. An
id starting with `no-` is a name, and **GB5 already established that a name is not a warrant**. The flag is
checkable; the meaning is not. A check that cries wolf gets suppressed — the exact failure mode of GB3's
bare-`UNVERIFIED` tripwire. Filed **OQ-36 · NEEDS-HUMAN**: an explicit `polarity: negative` field, enforced
the way `control` now is, moves the judgement from the tool (which cannot make it) to the author (who can).
That is a schema change across every future record and it is the human's call.

#### CONFLICT S1 — a `doc-index` claim wearing `doc-contains` prose

`tart-vm-location-documented` was `kind=doc-index`, `expect: "/faq/"` — which proves **the page exists**,
not that it documents `~/.tart/vms/`. `tart-faq-documents-vms-directory` (`doc-contains`) already proves the
sentence. **Retired**, not reworded: its evidence was byte-identical to `tart-faq-page-exists`, so rewording
would have left a duplicate behind. Prose reference in `tart-faq-documents-vms-directory` repaired.

#### Dedupe — the number falls, and that is the point

Five groups, each two ids over **byte-identical** `kind`+`target`+`line`+`expect`+`argv`+`site`+`page`.
Verified identical before deleting; kept the more precise id; repaired every prose reference:

| dropped | kept |
|---|---|
| `justfile-build-golden-invokes-missing-template` | `d1-justfile-44-invokes-absent-template` |
| `justfile-has-no-build-ipsw-recipe` | `d2-justfile-has-no-build-ipsw-recipe` |
| `vanilla-tahoe-sets-admin-password` | `vanilla-tahoe-ssh-password-is-plain-admin-at-line-20` |
| `tart-diamond-tier-grants-unlimited-workers-not-cores` | `tart-diamond-tier-12-per-core-per-year` |
| `tart-vm-location-documented` (S1) | `tart-faq-page-exists` + `tart-faq-documents-vms-directory` |

Plus `verify-claims-missing-file-is-unreachable` (GAP3). **246 distinct ids, 246 records, zero duplicate
evidence groups.** A count that includes duplicates is a count that flatters; the board's number is now
one a human can read literally.

#### Gate

```
$ just check
🚀 Checking all links in markdown files using lychee
[200] file:///Users/bossjones/dev/bossjones/macos-ci/specs/macos-ci/11-sources.md
[200] file:///Users/bossjones/dev/bossjones/macos-ci/specs/macos-ci/10-tart-vs-utm-adr.md
   [... 574 lines elided: lychee [200] lines + PASS lines + marker list ...]
246/246 claims verified
$ echo $?
0
```

`0` FAIL lines. All six original `must_fail` controls PRESENT with `must_fail: true` and still failing
their evidence — none weakened, none deleted. `uvx ruff check tools/verify_claims.py` → `All checks passed!`.
27 `must_fail` records, 34 `control` fields, 246 distinct ids. Markers **15**.
`00-overview.md` never touched by ledger; CONFLICT L1 is 📚 synth's.

**Still open, unchanged from GB4:** `control` ids resolve within the ledger being checked, so
`uv run tools/verify_claims.py .team/proposed/<role>.jsonl` exits `4` for any proposal whose negatives name
controls living in `claims.jsonl`. → 👑 lead: propagate, or authorise union-resolution.
