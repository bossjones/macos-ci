# boss-cmux — macos-ci VERIFICATION / RECONCILE run

Successor to the original 6-pane research run (`macos-ci-research-team`). That run **wrote** the specs.
This run **proves them**.

## Why a second run

The first run shipped a GROUND TRUTH that was false:

> G10. These 4 URLs are 404 — prune them, do not fetch, do not cite:
> `docs.getutm.app/settings-apple/devices/`, …

Three of those URLs return HTTP 200. The fourth, `settings-apple/devices/`, was never a dead page — **it
does not exist and never did. It was fabricated.** The clause *"do not fetch"* is precisely what prevented
its disproof. A downstream spec then cited the wrong page for the UTM Apple-backend device toggles, while
the page that actually documents them ([`settings-apple/virtualization/`](https://docs.getutm.app/settings-apple/virtualization/))
went undiscovered. See the retraction in `11-sources.md` and commit `7f56031`.

The lesson generalizes: **a rule that forbids verification does not protect truth, it launders a guess
into an axiom.** So this prompt inverts the old one's posture — read-only verification is *mandatory*,
ground truths are *claims with evidence* rather than commandments, and no agent grades its own homework.

## This prompt has itself been retracted once

An earlier draft of this file asserted `packer` was not installed (its G14) and taught an unscoped oracle
rule that would have caused an agent to declare a *real* HashiCorp page fabricated — G10's failure mode
running backwards. Both are fixed below. The moral is in the prompt now, as a binding rule: **the briefing
is not privileged over the evidence.** A ground truth that a passing ledger claim contradicts is retracted
on sight, and G14 is the worked example.

## What changed vs. the research prompt

| Research run | Verification run |
|---|---|
| "DOCS ONLY … rather than running it" | Read-only verification **required**; explicit allowlist |
| Ground truths are commandments | Ground truths are **claims to refute**; G10 and G14 retracted in-prompt |
| Citations = a URL | Citations = a **re-executable ledger entry** |
| Authors self-review | **Rotated cross-audit**; red-team posture, default-to-refuted |
| Confusion stays in one agent's head | **`.team/macos-ci.open-questions.md`** — a standing, human-readable record of every thing the team could not settle |
| DONE = lead reads it | DONE = **`just check` exits 0**, output pasted |
| 6 panes | 8 panes (adds 🔬 `ledger`, 🔐 `secrets`) |

## The feedback loop this run depends on

Already built, on disk, and passing `50/50`. Agents use it; they don't reinvent it.

- `.team/claims.jsonl` — one record per load-bearing assertion
- `tools/verify_claims.py` — re-executes the evidence behind each one
- `just check` — `link-check` + `verify-claims` + `unverified-count`

Six evidence kinds: `file-contains`, `file-line` (catches hallucinated `file:line` citations), `absent`
(negative claims), `cli-help` (runs `argv`, optionally under an `env` overlay), `doc-index` (proves a doc
page exists — the direct antidote to G10), and `doc-contains` (proves a page *says* a given sentence — the
antidote to `cli-help`'s unsoundness). Six claims carry `"must_fail": true`; four guard the doc oracles and
two are negative probes paired with positive controls.

---

## The request that generated this prompt

> Note in a different claude session I worked with claude to add lychee because in the previous cmux run
> it couldn't access all of the info required. so there might be some changes you weren't aware of. when
> you're done with your edits, I might need to re-run the cmux multi team agent prompt to verify all of
> our assumptions are correct etc. when you are done making your changes, give me a new prompt similar to
> this one to kick off the agent team in cmux again. If you have an ideas on giving claude a better
> feedback loop before doing that, let me know, I don't want there to be any assumptions, I want
> everything to be grounded in truth. here's the old prompt: `[macos-ci-research-team prompt]`

---

## The prompt

Copy everything inside the fence into cmux.

````text
/boss-cmux Boot an 8-pane VERIFICATION/AUDIT team for the repo /Users/bossjones/dev/bossjones/macos-ci.

Reuse the open cmux window; add a NEW workspace named "macos-ci-verify" (cwd = that repo; do NOT pass
--env-file — the Claude panes use the existing login). Launch all 8 panes as
`claude --dangerously-skip-permissions` (I authorize bypass mode). Colour the workspace, label the tabs,
and after launching the 7 workers hand the lead its brief. Drive the LEAD only; the lead drives the rest.

DO NOT run `cmux hooks setup`. Claude Code is absent from its agent list because it does not need it —
`cmux hooks --help` states "Claude Code hooks are injected automatically by the cmux Claude wrapper."
Hooks are ALREADY active for these panes. Regardless, every agent ALSO fires `cmux notify` EXPLICITLY on
each FSM transition and prints a `TASK-DONE:` sentinel, because a semantic per-transition signal beats a
generic turn-stop. The lead waits on `cmux events --name notification.created --no-heartbeat --no-ack`
(matching workspace_id) and confirms with `cmux read-screen`.

════════════════════════════════════════════════════════════════════════════
WHY THIS RUN EXISTS — READ THIS FIRST, IT IS THE WHOLE POINT
════════════════════════════════════════════════════════════════════════════

The previous run shipped a GROUND TRUTH that was FALSE:

  > G10. These 4 URLs are 404 — prune them, do not fetch, do not cite:
  >      docs.getutm.app/settings-apple/devices/, …

Three of those URLs return HTTP 200. The fourth, `settings-apple/devices/`, was never a dead page —
it does not exist and never did. IT WAS FABRICATED. The clause "do not fetch" is precisely what
prevented its disproof. A downstream spec then cited the wrong page for the UTM Apple-backend device
toggles, while the page that actually documents them (`settings-apple/virtualization/`) went
undiscovered. See the retraction in `11-sources.md` and commit `7f56031`.

AND THEN THIS PROMPT MADE THE SAME CLASS OF ERROR. An earlier draft told you `packer` was not installed.
It is (v1.15.4), and `.team/claims.jsonl` ALREADY CONTAINED the claim that proves it. The briefing was
stale and the evidence was right there.

Four lessons, binding on every agent here:

  1. A rule that forbids verification does not protect truth. It launders a guess into an axiom.
     In this run, read-only verification is MANDATORY, not forbidden.
  2. An assertion with a citation is not verified. It is decorated. A URL that resolves says nothing
     about whether the sentence citing it is true. Evidence must be re-executable.
  3. Authors cannot audit their own claims. Cross-audit is rotated, below.
  4. THIS PROMPT IS NOT PRIVILEGED OVER THE EVIDENCE. If a GROUND TRUTH below contradicts a passing
     ledger claim, or contradicts a read-only command you just ran, THE GROUND TRUTH IS RETRACTED.
     Report it; do not "reconcile" it by softening what you observed. G14 is the worked example.

SCOPE. This run writes markdown, ledger entries, and the open-questions file. NO agent installs
tart/packer/UTM, pulls a VM image, boots a VM, runs `brew install`, or mutates the host.

READ-ONLY VERIFICATION IS REQUIRED. These commands are explicitly ALLOWED and encouraged:

  - `<tool> --help` / `<tool> --version`
        installed: tart 2.32.1 · packer 1.15.4 · just · uv · cirrus · lychee 0.22.0 · gh · utmctl
  - `packer version` and `packer inspect <dir>`   (`just check` already runs `packer inspect
        tests/fixtures/packer-sensitive` six times — this is not optional, it is the gate)
  - `curl -fsSL <doc-index-url>` and `curl -sS -o /dev/null -w '%{http_code}'` (the oracles below)
  - `grep` / `sed` / `rg` over the LOCAL clones of zsh-dotfiles and zsh-dotfiles-prep
  - `just link-check`, `just verify-claims`, `just check`, `just unverified-count`
  - `uv run tools/verify_claims.py [--json]`
  - `git log`, `git show`, `git blame`

EXPLICITLY FORBIDDEN, even though the binaries exist:

  - `packer build`   and  `just build-golden`  (Justfile:41-44 shells out to `packer build`)
  - `packer init`    (downloads the tart plugin binary; writes ~/.config/packer — host mutation)
  - `just verify-no-secrets <vm>`  (Justfile:52 — takes a VM argument and scans ~/.tart/vms/<vm>/.
        No VM exists and none may be booted. It is deliberately NOT part of `just check`.)

If you CAN check something with an ALLOWED read-only command and you don't, that is a defect, not caution.

════════════════════════════════════════════════════════════════════════════
THE ORACLES — use them before you ever type a URL
════════════════════════════════════════════════════════════════════════════

Three sites, three page lists. No scraping, no 403, no guessing.

    # tart.run (MkDocs Material) — 101 entries across 20 pages, under .docs[]
    curl -fsSL https://tart.run/search/search_index.json |
      python3 -c 'import json,sys
    d=json.load(sys.stdin)
    for e in d["docs"]:
        if "fair source" in (e["title"]+e["text"]).lower(): print(e["title"], "->", e["location"])'

    # docs.getutm.app (Just the Docs) — 281 entries across 78 pages
    curl -fsSL https://docs.getutm.app/assets/js/search-data.json |
      python3 -c 'import json,sys
    d=json.load(sys.stdin)
    for v in d.values():
        if "trackpad" in (v["title"]+v["content"]).lower(): print(v["title"], "->", v["relUrl"])'

    # developer.hashicorp.com — no search JSON. The sitemap IS the page list, for /packer/docs/** ONLY.
    curl -fsSL https://developer.hashicorp.com/server-sitemap.xml |
      grep -o '<loc>https://developer.hashicorp.com/packer[^<]*</loc>'      # 337 entries

`docs.getutm.app` 403s WebFetch. Use `curl -fsSL`. One query for `trackpad` would have found the page
G10 missed. Query the index FIRST; fetch the page only to read its content.

────────────────────────────────────────────────────────────────────────────
THE RULE, AND ITS DOMAIN — read this twice, it is where the last draft broke
────────────────────────────────────────────────────────────────────────────

An index is authoritative FOR THE PREFIXES IT COVERS. Inside that domain, absence from the index is
proof of fabrication. OUTSIDE it, ABSENCE IS EVIDENCE OF NOTHING — go fetch the URL.

  EXCEPTION, LOAD-BEARING:  /packer/integrations/**  IS NOT IN THE HASHICORP SITEMAP.

      $ curl -fsSL .../server-sitemap.xml | grep -o '...packer[^<]*' | grep -c 'packer/integrations'
      0                                    # ...out of 337 /packer/* entries
      $ curl -sS -o /dev/null -w '%{http_code}' \
          https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart
      200                                  # THE PAGE IS REAL

  HashiCorp renders integration pages from the PLUGIN'S OWN REPO, not from its CMS. The actual source is
  cirruslabs/packer-plugin-tart's `.web-docs/` directory on GitHub. Verify these pages with a plain
  `curl -sS -o /dev/null -w '%{http_code}'`, or by reading `.web-docs/` — NEVER by grepping the sitemap.

  This is G10 RUNNING BACKWARDS. G10 declared a fake page real. Grepping the sitemap for the Tart builder
  reference cited in 02-packer-tart-builder.md would declare a REAL page FAKE — and "default to refuted"
  would make you retract a correct citation with total confidence. The oracle rule is not wrong. It was
  UNSCOPED. Scope it.

════════════════════════════════════════════════════════════════════════════
THE FEEDBACK LOOP — this is how you know you are right
════════════════════════════════════════════════════════════════════════════

Already built and passing on the working tree. Do not reinvent it; USE it.

    just check              # link-check + verify-claims + unverified-count  <- THE GATE
    just verify-claims      # re-execute the evidence behind every claim
    just verify-claims-json # machine-readable; read this instead of scraping prose
    just unverified-count   # the honesty budget

`.team/claims.jsonl` — one JSON record per load-bearing assertion; every record carries a `file` field
naming the spec it defends. `tools/verify_claims.py` — re-executes the evidence.
Exit 0 verified · 2 a claim failed · 3 evidence unreachable · 4 usage.

Evidence kinds:

  file-contains  a local file contains a string        kills: claims about repos nobody opened
  file-line      line N of a file contains a string    kills: HALLUCINATED file:line CITATIONS
  absent         a string is NOT present in a file     kills: unfalsifiable negative claims
  cli-help       runs `argv` (optional `env` overlay)  kills: remembered flags that don't exist
  doc-index      a path is in the site's search index  kills: FABRICATED URLs — the G10 failure
  doc-contains   that page CONTAINS a given sentence   kills: real URL, invented sentence

────────────────────────────────────────────────────────────────────────────
`cli-help` IS UNSOUND FOR BACKEND QUESTIONS. `doc-contains` IS THE ANTIDOTE.
────────────────────────────────────────────────────────────────────────────

A FLAG IN `--help` PROVES THE ARGUMENT PARSER ACCEPTS IT. NOTHING MORE.

`utmctl start --help` advertises `--disposable` on a host that can only run Apple-backend macOS guests.
docs.getutm.app/advanced/disposable/ says "Disposable mode is only supported on QEMU backend." Both are
true. The flag parses; the feature cannot work. So the ledger PAIRS them, and the `claim` prose of each
NAMES its partner:

  {"id":"utmctl-start-help-lists-disposable","kind":"cli-help","file":"specs/macos-ci/05-utm-automation.md",
   "argv":["utmctl","start","--help"],"expect":"--disposable",
   "claim":"TRAP: ... A flag in --help proves it parses, not that it works. The refutation is
            utmctl-disposable-is-qemu-only."}

  {"id":"utmctl-disposable-is-qemu-only","kind":"doc-contains","file":"specs/macos-ci/05-utm-automation.md",
   "site":"utm","page":"/advanced/disposable/","expect":"only supported on QEMU backend",
   "claim":"...This is the refutation of utmctl-start-help-lists-disposable."}

Any `cli-help` claim about what a flag DOES (rather than that it parses) needs this treatment.

────────────────────────────────────────────────────────────────────────────
`must_fail` HAS TWO JOBS
────────────────────────────────────────────────────────────────────────────

Any claim may set `"must_fail": true`, inverting the verdict. There are six. They do two different things.

JOB 1 — GUARD THE ORACLES. Four controls assert something that must NEVER verify:

  {"id":"CONTROL-utm-settings-apple-devices-is-fabricated","kind":"doc-index","must_fail":true,
   "file":"specs/macos-ci/11-sources.md","site":"utm","expect":"/settings-apple/devices/",
   "claim":"CONTROL: ...Its evidence must NOT verify; if it does, the doc-index oracle has broken and
            every doc-index claim is worthless."}

  ...plus CONTROL-disposable-is-not-apple-backend, CONTROL-tart-doc-index-oracle, and
  CONTROL-tart-cirrus-page-has-no-sshpass. If ANY of them starts PASSING, that oracle has silently broken
  and every claim of its kind is worthless — the run must FAIL LOUDLY rather than go green on a dead
  check. NEVER delete, weaken, or "fix" a control. A verifier nobody verifies is a second thing to trust.

JOB 2 — EXPRESS A NEGATIVE OVER A `cli-help` PROBE. `absent` only takes a FILE, so a negative assertion
about a COMMAND'S OUTPUT can only be written as `must_fail`.

  A BARE NEGATIVE PROBE IS WORTHLESS. "The secret does not appear in the output" is equally satisfied by
  NO OUTPUT AT ALL. So EVERY negative probe MUST ship a POSITIVE CONTROL running THE SAME COMMAND and
  asserting a non-sensitive literal IS present. They live next to each other; the control names its
  partner. The worked pair:

  {"id":"packer-sensitive-hides-secret","kind":"cli-help","must_fail":true,
   "argv":["packer","inspect","tests/fixtures/packer-sensitive"],"expect":"ghp_FIXTURE_SENTINEL",
   "claim":"the sensitive value never reaches packer's output. Paired with
            CONTROL-packer-inspect-prints-plain-literals."}

  {"id":"CONTROL-packer-inspect-prints-plain-literals","kind":"cli-help",
   "argv":["packer","inspect","tests/fixtures/packer-sensitive"],"expect":"plain_FIXTURE_CONTROL",
   "claim":"CONTROL for packer-sensitive-hides-secret: packer inspect DOES print non-sensitive literals.
            If this fails, 'the secret was absent' proves nothing — inspect printed nothing."}

  (`packer-sensitive-hides-secret-under-debug-log` / `CONTROL-packer-debug-log-prints-plain-literals` are
   the same pair under an `"env": {"PACKER_LOG": "1"}` overlay.)

────────────────────────────────────────────────────────────────────────────
TWO FAILURE PREFIXES ARE NEVER INVERTED BY `must_fail`
────────────────────────────────────────────────────────────────────────────

Neither is evidence about the claim (tools/verify_claims.py:282):

  UNREACHABLE:   network down, binary absent. Says nothing about the world.
  STRUCTURE:     a `doc-contains` page is missing from the index entirely.

`STRUCTURE:` keeps "the page vanished" distinguishable from "the sentence vanished", and stops a control
from silently "passing" because its page 404'd.

────────────────────────────────────────────────────────────────────────────

Two more real records, for shape (note the `file` field; `cli-help` may carry `env`):

  {"id":"G11-stdinIsATTY-line-2","kind":"file-line","file":"specs/macos-ci/09-dotfiles-under-test.md",
   "target":"/Users/bossjones/dev/bossjones/zsh-dotfiles/home/.chezmoi.yaml.tmpl","line":2,
   "expect":"stdinIsATTY","claim":".chezmoi.yaml.tmpl:2 defines $interactive := stdinIsATTY"}

  {"id":"tart-ip-has-agent-resolver","kind":"cli-help","file":"specs/macos-ci/01-tart-core.md",
   "argv":["tart","ip","--help"],"expect":"agent; default: dhcp",
   "claim":"tart ip takes three resolvers (dhcp, arp, agent); dhcp is the default."}

The rule of thumb, and it is not optional:

  Every non-obvious claim in a spec must resolve to one of four states:
    (a) a passing ledger entry,
    (b) an explicit `<!-- UNVERIFIED -->` marker on the line,
    (c) an entry in `.team/macos-ci.open-questions.md`, or
    (d) deletion.
  There is no fifth state. "It sounds right" is state (d).

`just unverified-count` is an honesty budget. It must fall because claims got VERIFIED, never because
markers got DELETED. The lead records the count before and after and will reject a silent drop.

════════════════════════════════════════════════════════════════════════════
OPEN QUESTIONS — `.team/macos-ci.open-questions.md`  ◀ THE HUMAN READS THIS
════════════════════════════════════════════════════════════════════════════

A shared, append-only file. This is where the human looks to see WHERE THE TEAM IS STUCK. Silence is
not a signal; an empty open-questions file after eight agents audit fourteen specs is a red flag, not
a triumph.

WRITE AN ENTRY THE MOMENT YOU ARE STUCK — DO NOT WAIT UNTIL YOU FINISH. An entry costs nothing. Guessing
costs a fabricated URL. If you find yourself about to write "presumably", "it appears", "likely", or
"should be", STOP and file an open question instead.

FILE AN ENTRY WHEN:
  - You cannot verify a claim AND cannot disprove it with any allowed read-only command.
  - Settling it would need something SCOPE forbids (booting a VM, `packer build`, installing a tool).
  - Two sources disagree and you cannot tell which is authoritative.
  - A GROUND TRUTH below contradicts what you read. (Also file it as a RETRACTION in the backlog.)
  - You need a decision only the human can make (a tradeoff, a preference, a risk to accept).
  - You are about to mark something `<!-- UNVERIFIED -->` and the reason is interesting.

FORMAT — one `##` block per question, appended, never rewritten by another agent:

    ## OQ-<NN> · <role> · <one-line question ending in a question mark>
    **Status:** OPEN | ANSWERED | BLOCKED-BY-SCOPE | NEEDS-HUMAN
    **Spec:** specs/macos-ci/NN-xxx.md:LINE
    **What I tried:** the exact read-only commands I ran, and what they returned.
    **Why it is stuck:** what would settle it, and why I cannot run that.
    **My best guess, explicitly labelled a guess:** ...
    **Cost of guessing wrong:** what breaks downstream if my guess is inverted.

RULES:
  - APPEND ONLY. Never edit or delete another agent's block. To answer one, append a `**Resolution:**`
    line INSIDE its block and flip `**Status:**`. Ownership of this file is shared; that is deliberate.
  - Number them `OQ-01`, `OQ-02`, … Take the next free number; if you race, renumber yours upward.
  - `NEEDS-HUMAN` means the human must decide. `BLOCKED-BY-SCOPE` means a booted VM would settle it.
  - Every `<!-- UNVERIFIED -->` marker you ADD must cite an OQ number in its comment text.
  - The LEAD reports the full list at DONE, grouped by status, NEEDS-HUMAN first.
  - An open question is a SUCCESS. It is the run correctly refusing to invent an answer.

SEED IT AT SCAFFOLD. The lead writes the file with a header and these two already known:

    OQ-01 · secrets · BLOCKED-BY-SCOPE — does `disk_format = "asif"` (macOS 26+, sparse) preserve the
      unlink-does-not-zero residue that 13-build-secrets.md:54 assumes? Needs a booted VM.
    OQ-02 · harness · BLOCKED-BY-SCOPE — is `--vnc-experimental`'s stdout format really
      `Opening vnc://:<password>@127.0.0.1:<port>...`? (G13) Comes from one reported example, not a boot.

════════════════════════════════════════════════════════════════════════════
ROLES — 👑 lead on the left half; the rest in a grid on the right
════════════════════════════════════════════════════════════════════════════

  👑 lead      — orchestrator (I talk to this one); owns .team/ board+backlog; runs THE GATE
  🔬 ledger    — SOLE owner of .team/claims.jsonl and tools/verify_claims.py; merges every
                 agent's proposed claims, dedupes, keeps `just verify-claims` green
  🍎 tart-core — audits 01-tart-core.md, 02-packer-tart-builder.md
  🏭 tart-ci   — audits 03-tart-ci-and-orchard.md, 04-tart-licensing-risk.md
  🖥  utm      — audits 05-utm-automation.md, 06-utm-macos-guest.md, 07-utm-settings-appendix.md
  🧪 harness   — audits 08-dotfiles-test-harness.md, 09-dotfiles-under-test.md,
                 12-tooling-and-agent-loop.md
  🔐 secrets   — audits 13-build-secrets.md   [NEW PANE — 13 backing claims, the densest spec in the repo]
  📚 synth     — audits 00-overview.md, 10-tart-vs-utm-adr.md, 11-sources.md, specs/macos-ci.md;
                 reconciles cross-file contradictions  [BARRIER: idle until CROSS-AUDIT is CLEAN]

EXCLUSIVE FILE OWNERSHIP. An agent edits ONLY its own files. Everything else goes through
`.team/macos-ci.backlog.md`. Proposed claims go to `.team/proposed/<role>.jsonl`; ONLY 🔬 ledger merges
them into `.team/claims.jsonl`. `.team/macos-ci.open-questions.md` is the ONE shared, append-only file.

════════════════════════════════════════════════════════════════════════════
ROTATED CROSS-AUDIT — nobody grades their own homework
════════════════════════════════════════════════════════════════════════════

After each auditor finishes its OWN files, it red-teams ANOTHER agent's files (a 7-node derangement):

    tart-core -> audits utm's files
    utm       -> audits harness's files
    harness   -> audits tart-ci's files
    tart-ci   -> audits secrets' files
    secrets   -> audits tart-core's files
    synth     -> audits the ledger itself (are the claims load-bearing, or trivia?)
    ledger    -> audits synth's files

RED-TEAM POSTURE: TRY TO REFUTE, DEFAULT TO REFUTED. For each non-obvious claim in the file you are
auditing, attempt to construct the read-only command that would DISPROVE it. If you cannot verify it and
cannot disprove it, it goes to `<!-- UNVERIFIED -->` AND to an open question. Do not be charitable. The
last run was charitable and shipped a fabricated URL. File every refutation in the backlog as a CONFLICT.

ONE CARVE-OUT, AND ONLY ONE: "default to refuted" DOES NOT APPLY to a page you have not fetched. Absence
from an index only refutes inside that index's domain (see THE ORACLES). Refuting a `/packer/integrations/`
URL because it is missing from the sitemap is a DEFECT, not diligence.

════════════════════════════════════════════════════════════════════════════
FSM
════════════════════════════════════════════════════════════════════════════

  SCAFFOLD
    -> AUDIT-OWN      (tart-core | tart-ci | utm | harness | secrets in parallel; ledger seeds infra)
    -> LEDGER-MERGE   (ledger folds .team/proposed/*.jsonl into claims.jsonl)
    -> CROSS-AUDIT    (rotated, per the table above)
    -> GATE           (lead runs `just check`; MUST exit 0)
        |- CLEAN    -> SYNTH -> REVIEW -> DONE
        |- CONFLICT -> RECONCILE -> GATE (loop)
        \- ERROR    (unrecoverable)

FIRE `cmux notify --title "<role>" --body "<state>: <one-line>"` ON EVERY TRANSITION (each agent on its
own; lead on the global ones) so I'm pinged through the whole process. ALSO fire a notify the first time
you open an OQ — I want to know when someone gets stuck, not just when they finish.

THE FSM CANNOT REACH DONE UNTIL `just check` EXITS 0. Not "looks good." Exit zero. The lead pastes the
actual command output into `.team/macos-ci.board.md`. A claimed pass without pasted output is treated as
a failure. An OPEN question does NOT block DONE — an UNREPORTED one does.

════════════════════════════════════════════════════════════════════════════
STATUS BOARD
════════════════════════════════════════════════════════════════════════════

- Flags below were verified against cmux 0.64.17. Still trust `--help` over memory; never guess a flag.
- On EVERY state change, rename your OWN tab to a pill. `rename-tab` resolves its target as
  --tab -> --surface -> $CMUX_TAB_ID/$CMUX_SURFACE_ID -> focused tab, so renaming yourself needs NO
  target flag:

      cmux rename-tab "<emoji> <role> <n>/<N> [<progressbar>] · <one-line log>"

  emoji = 🔵 working / 🟢 done / 🔴 error / 🟡 refuted-a-claim / ❓ blocked-on-an-open-question,
  progressbar like [####------].
  e.g. "🔵 utm 4/9 [####------] · querying search index for trackpad"
  (Only the LEAD, renaming someone ELSE's tab by ref, needs the context flags:
   `cmux rename-tab --workspace <ws> --surface <ref> "<title>"`.)
- Surfaces have NO colour attribute — colour lives on the workspace. LEAD (and only lead) sets the
  workspace pill on each transition. `set-status --color` takes a #hex:

      cmux set-status state <STATE> --workspace <ws> --icon checkmark.seal \
        --color <#1565C0 working | #196F3D done | #C0392B error>

  and mirrors coarse progress with `cmux set-progress <0.0-1.0> --label "<state>" --workspace <ws>`.
  Optionally tint the row once at SCAFFOLD:
      cmux workspace-action --action set-color --workspace <ws> --color Teal
  (named colours: Red, Crimson, Orange, Amber, Olive, Green, Teal, Aqua, Blue, Navy, Indigo, Purple,
   Magenta, Rose, Brown, Charcoal — or #RRGGBB.)
- LEAD keeps a board table (agent | state | n/N | claims-added | claims-refuted | open-questions |
  last log) in `.team/macos-ci.board.md` and a living task list in `.team/macos-ci.backlog.md`.

════════════════════════════════════════════════════════════════════════════
LEAD BRIEF
════════════════════════════════════════════════════════════════════════════

0) ARCHIVE THE STALE STATE FIRST. `.team/macos-ci.board.md` and `.team/macos-ci.backlog.md` are
   LEFTOVERS FROM THE RESEARCH RUN: they show all-🟢 DONE over files 00-11 and never mention 12, 13, the
   claims ledger, or tools/verify_claims.py. `mkdir -p .team/archive` and `mv` both into it (the
   pre_tool_use hook blocks the substring `rm `). Do not trust a word in them.

1) SCAFFOLD. `mkdir -p .team/proposed`. Create `.team/macos-ci.open-questions.md` with a header and the
   two seed entries (OQ-01, OQ-02) from the OPEN QUESTIONS section.

   Record the BASELINE by running `just check` and `just unverified-count`; paste both outputs into the
   fresh board. A CLEAN TREE MUST GIVE:

       just check          -> exit 0, "50/50 claims verified"
       unverified-count    -> 22 lines, across 11 files under specs/

   IF THE BASELINE DIVERGES, THAT IS ITSELF A FINDING. It means the working tree is dirty or a doc site
   changed under us. Open an OQ and report to me BEFORE dispatching anyone.

   Write the fresh backlog covering 00-13, seeded with the FIVE KNOWN DEFECTS below. Dispatch ledger +
   the 5 auditors IN PARALLEL. synth STAYS IDLE (barrier).

   YOU (lead) OWN THE `Justfile`. No worker does. D1 and D5 both land there; fix them yourself or file
   them for me.

   KNOWN DEFECTS — found before the run started; do not spend cycles rediscovering them:
     D1. `packer/tart-golden-image.pkr.hcl` DOES NOT EXIST, but `Justfile:44` invokes it.
         `just build-golden` is broken today.                        -> 🔐 secrets + 🧪 harness
     D2. `12-tooling-and-agent-loop.md:200-202` documents recipes `build [IMAGE]`, `build-ipsw VERSION`,
         and `images`. NONE exist. The real recipe is `build-golden`. -> 🧪 harness
     D3. `00-overview.md:58` credits 13-build-secrets.md to owner `harness`. The roster now says
         `secrets`.                                                   -> 📚 synth
     D4. 12 frames its tooling as "not yet built", but `verify-claims`, `verify-claims-json`,
         `unverified-count`, `check`, `verify-no-secrets` and `build-golden` are all REAL recipes now.
         Its "to build" / "already implemented" split needs redrawing. -> 🧪 harness
     D5. THE HONESTY BUDGET IS INFLATED, AND IT CAN BE GAMED SILENTLY. `Justfile:63` runs
         `grep -rc 'UNVERIFIED' specs/` — the BARE WORD, not the marker. So it also counts prose that
         merely DESCRIBES the convention. Five of the 22 counted lines are not markers on any claim:
             specs/macos-ci.md:505 · 00-overview.md:68 · 01-tart-core.md:191 · 12:7 · 12:459
         Real markers take the form `<!-- UNVERIFIED: <reason> -->` or a bare `<!-- UNVERIFIED -->`
         inline. The consequence is the reason this matters: DELETING THE SENTENCE "…marks the claim
         `<!-- UNVERIFIED -->`" FROM 01-tart-core.md:191 LOWERS THE BUDGET BY ONE WITHOUT VERIFYING
         ANYTHING — and the lead's baseline diff cannot see the difference between that and honest work.
         A budget you can pay down by deleting a sentence about the budget is not a budget.
         Tighten the grep to the marker form, re-baseline, and note the true starting count in the board.
         -> 👑 lead (owns Justfile), with 🧪 harness for 12's two lines

2) Wait on `cmux events --name notification.created --no-heartbeat --no-ack` matching this workspace_id.
   Do NOT busy-poll. Once notified, confirm with `cmux read-screen --surface <ref> --scrollback
   --lines 40` and check for `TASK-DONE: <role> | <summary>`.

3) LEDGER-MERGE. Release 🔬 ledger to fold `.team/proposed/*.jsonl` into `.team/claims.jsonl`.
   `just verify-claims` must exit 0 before CROSS-AUDIT begins. A proposed claim that fails is a finding,
   not a bug to silence: route it back to the owning agent as a CONFLICT.

4) CROSS-AUDIT. Dispatch the rotation. Collect refutations from the backlog and OQs from the shared file.

5) GATE. Run `just check` PERSONALLY and paste the output. Exit 0 or the FSM does not advance.
   Then verify the honesty budget: `just unverified-count` may only have dropped where a corresponding
   ledger claim was ADDED. Diff it against the baseline from step 1. A marker that vanished without a
   claim is a CONFLICT. Every marker that was ADDED must cite an OQ number.

6) SYNTH. Release synth. It reconciles cross-file contradictions and updates 00 / 10 / 11 /
   `specs/macos-ci.md` (and fixes D3). It must NOT introduce a new claim without a ledger entry.

7) REVIEW + DONE. Lead reads `specs/macos-ci.md` end-to-end against the PLAN-FORMAT CONTRACT below.
   Re-run `just check`. Set the board all-🟢, `cmux set-status state done --workspace <ws>
   --color "#196F3D"`, notify DONE, and report IN THIS ORDER:
     a. EVERY GROUND TRUTH THAT WAS RETRACTED.  (G14 is already one. Find the others.)
     b. The full `.team/macos-ci.open-questions.md`, grouped by status, NEEDS-HUMAN FIRST.
     c. The claims delta (added / refuted / still-UNVERIFIED).
     d. The roster (pane -> role -> surface) and the rendered board.

════════════════════════════════════════════════════════════════════════════
GROUND TRUTHS — now CLAIMS, not commandments
════════════════════════════════════════════════════════════════════════════

Each of these was asserted by a previous run or a previous draft of this prompt. YOUR JOB IS TO TRY TO
BREAK THEM. A ground truth that survives a genuine refutation attempt earns a ledger entry. One that
cannot be checked either way gets `<!-- UNVERIFIED -->` AND an open question. One that fails gets
RETRACTED, loudly, in the board and in `11-sources.md`.

Report retractions to the lead. Do not silently pick a side. TWO OF THESE ARE ALREADY RETRACTED.

  G1. No Terraform provider exists for tart or for UTM. Tart's orchestration story is Orchard.
      utmapp/UTM#3618 is the open IaC request; maintainer says "a long way off" (tracked in #3718).
  G2. The tonyyo11 blog uses Terraform to manage JAMF PRO RESOURCES, not VMs. The repo README's
      "Terraform" line is aspirational.
  G3. packer-plugin-tart is TART-ONLY. No UTM Packer builder exists. UTM automation is AppleScript/JXA
      (`utmctl`) + the `utm://` URL scheme.
  G4. Tart is Fair Source and ACTIVELY ENFORCED as of the Oct 2025 announcement. Free on personal
      workstations; commercial free <=100 CPU cores (tart) / 4 Orchard workers; Gold $12K/yr (500/20),
      Platinum $36K/yr (3000/200), Diamond ~$12/core/yr. NO open-source exemption.
      -> VERIFY the tier numbers against tart.run/licensing via the search index. Numbers rot.
  G5. UTM "disposable mode" (run-without-saving) is QEMU-BACKEND ONLY; it does not work for macOS
      guests, which require the Apple Virtualization.framework backend.
      -> `utmctl start --help` ADVERTISES `--disposable` anyway. That is the canonical `cli-help` trap.
         The pair `utmctl-start-help-lists-disposable` / `utmctl-disposable-is-qemu-only` settles it.
         Do not "resolve" the contradiction; it is the point.
  G6. UTM's Apple backend does NOT support multiple graphical displays.
  G7. `advanced/rosetta` is about running x86_64 ELF binaries in LINUX guests, not macOS guests.
  G8. tart headless on macOS 15+ hosts has a keychain requirement; nested virtualisation needs M3/M4
      AND a Linux guest. Prebuilt ghcr.io images cover macOS 12-26; default creds admin/admin.
      -> THOSE CREDS ARE PUBLIC AND MUST NEVER BE MARKED `sensitive`. See G16.
  G9. NEITHER dotfiles repo uses Ansible. Ansible is a wrapper we may CHOOSE, not something inherited.

  ~~G10.~~ RETRACTED — WAS FALSE. Three of the four "404" URLs return HTTP 200. The fourth,
      `settings-apple/devices/`, was FABRICATED — it is absent from UTM's 78-page search index. The real
      device-toggle page is `settings-apple/virtualization/`. A `must_fail` control claim now guards
      this. NEVER RESTORE G10. Its existence is the reason this run exists.

  G11. NON-INTERACTIVE CHEZMOI IS SOLVED UPSTREAM. Both repos are checked out LOCALLY — read them, do
      not WebFetch:  /Users/bossjones/dev/bossjones/zsh-dotfiles  and  .../zsh-dotfiles-prep
      Already ledger-verified; CONFIRM, do not re-derive:
      - `.chezmoiroot` = `home`; `.chezmoiversion` = `2.20.0`.
      - `home/.chezmoi.yaml.tmpl:2` = `{{- $interactive := stdinIsATTY -}}`. Every promptString/promptBool
        for name/email/computer_name/hostname/ruby/pyenv/nodejs/k8s/cuda/fnm/opencv sits INSIDE
        `{{- if $interactive -}}`. In a non-TTY run those prompts never fire and defaults are used.
      - Non-TTY defaults: ruby/pyenv/nodejs/k8s/cuda/fnm/opencv ALL `false`. "The dotfiles installed"
        means the LEAN set.
      - `computer_name`/`hostname` read env first: `CM_computer_name` / `CM_hostname`.
      - `version_manager` is DELIBERATELY OUTSIDE the `$interactive` block (`:102-107`) precisely so a
        non-TTY run can select it. Upstream default is `asdf` (`:20`). Override with
        `--promptString version_manager=mise`.
      - Upstream's non-TTY invocation, verbatim (`scripts/smoke-test-docker.sh:361-365`):
            retry -t 4 -- "$chezmoi_bin" init -R --debug -v --apply --force \
                --promptString version_manager="$VERSION_MANAGER" --source=.
      - `chezmoi verify` does NOT work pre-apply. Upstream uses `chezmoi diff`.
      - `--promptBool` CANNOT reach the seven bools non-TTY. Levers: a pre-seeded chezmoi config, or an
        upstream change lifting them out of the guard the way `version_manager` was.

  G12. THE PREP-INSTALLER BOUNDARY. Verify each; they reshape the golden image.
      - `zsh-dotfiles` installs mise ITSELF on macOS: `home/.chezmoiscripts/
        run_onchange_before_02-macos-install-mise.sh.tmpl`, gated on `(eq .version_manager "mise")`.
      - `zsh-dotfiles` CANNOT install asdf on macOS — there is no `02-macos-install-asdf` script, only
        `-centos-`/`-ubuntu-`. asdf on macOS comes only from `zsh-dotfiles-prep`
        (`bin/zsh-dotfiles-prereq-installer` ~`:578`, ~`:752`).
      - `zsh-dotfiles` NEVER installs Homebrew (`install.sh:206` hard-errors) or Xcode CLT
        (no `xcode-select` anywhere).
      - `home/.chezmoiignore.tmpl:5` enforces mise/asdf mutual exclusion at the FILE level.
      => Therefore `mise` is the harness default (the only VM `zsh-dotfiles` can bootstrap unaided), the
        golden image owns CLT+Homebrew+chezmoi+`retry`, and the asdf leg needs `--with-prereq-installer`.
      LINE NUMBERS ABOVE ARE APPROXIMATE — re-derive them with `file-line` ledger entries.

  G13. THE GUI IS REACHABLE. `tart run --help` (tart 2.32.1) exposes `--no-graphics`, `--vnc`, and
      `--vnc-experimental`. The latter uses Virtualization.framework's own VNC server and prints
      `Opening vnc://:<password>@127.0.0.1:<port>...`. Packer's tart builder drives `boot_command` over
      this same channel (`disable_vnc`, `vnc_port_min/max`).
      THE EXACT STDOUT FORMAT IS `<!-- UNVERIFIED -->` — it comes from one reported example, not from a
      booted VM. Do NOT upgrade it to fact without booting one, which this run may not do. See OQ-02.

  ~~G14.~~ RETRACTED — WAS FALSE. An earlier draft of this prompt asserted `packer` was NOT installed and
      pointed at a `just doctor` recipe. BOTH WRONG: `packer version` prints `Packer v1.15.4`, the ledger
      claim `packer-is-installed` was ALREADY PASSING when that draft was written, and no `doctor` recipe
      exists in the Justfile. The briefing is not privileged over the evidence. This is the worked example
      for lesson 4. The corrected inventory:

  G14'. HOST STATE. Installed and confirmable with `--version`: `tart` 2.32.1, `packer` 1.15.4, `just`,
      `uv`, `cirrus`, `lychee` 0.22.0, `gh`, `utmctl`. `packer inspect` is ALLOWED and load-bearing —
      six ledger claims run it against `tests/fixtures/packer-sensitive`. `packer build`, `packer init`,
      `just build-golden` and `just verify-no-secrets` are FORBIDDEN (see SCOPE). Confirm the inventory
      with `cli-help` ledger entries.

  G15. NEW — DELETING A SECRET FROM THE GUEST DOES NOT ERASE IT. `rm` unlinks an inode; it does not zero
      the blocks. Plaintext written to the guest survives in `~/.tart/vms/<name>/`'s disk image and
      `strings` still finds it. Therefore NEVER write a build secret to the guest filesystem: pass it
      through the shell provisioner's `environment_vars` with `use_env_var_file = false` (true writes a
      tempfile INTO the guest), and there is nothing to clean up.
      -> The reproduction on record used `hdiutil` against a UDIF/APFS image on the HOST, not a tart VM
         against its own disk image. Unlink-does-not-zero is generic to block-backed filesystems, but the
         tart-specific reproduction — and whether `disk_format = "asif"` (macOS 26+, sparse) behaves the
         same — is `<!-- UNVERIFIED -->`. See OQ-01.

  G16. NEW — PACKER'S `sensitive = true` MASKS VALUES, NOT VARIABLES. It redacts EVERY occurrence of the
      string, anywhere in the output, including under `PACKER_LOG=1`. So NEVER mark a common word
      sensitive: `ssh_password = "admin"` marked sensitive would rewrite every `admin` in every log to
      `<sensitive>`. G8's `admin/admin` default creds are public. Leave them plain.

  G17. NEW — THE BUILD NEEDS NO SECRETS BEYOND ONE TOKEN. No SSH key, no `~/.gitconfig`, no
      `~/.ssh/config`, and no `HOMEBREW_GITHUB_PACKAGES_TOKEN`. Every repo and tap involved is PUBLIC; the
      one `git@github.com:` tap URL is rewritten to anonymous HTTPS via
      `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_n` / `GIT_CONFIG_VALUE_n`. `HOMEBREW_GITHUB_API_TOKEN` is
      wanted only to lift GitHub's 60-req/hr unauthenticated REST cap to 5,000. See 13-build-secrets.md.

  G18. NEW — `utmctl` IS A WRAPPER AROUND UTM'S APPLESCRIPT INTERFACE, NOT A SECOND AUTOMATION SURFACE.
      UTM's own docs say so. `exec` / `file` / `ip-address` are the Guest Suite and require the QEMU guest
      agent, which Apple-backend macOS guests DO NOT HAVE. `start --disposable` and `usb` parse but are
      QEMU-backend-only. UTM's macOS-guest automation surface is LIFECYCLE plus host-side serial.
      THERE IS NO UTM-LANE `tart ip`: utmctl cannot report a macOS guest's IP address. See 05 §4.

  G19. NEW — THE SITEMAP EXCEPTION. `developer.hashicorp.com/server-sitemap.xml` lists 337 `/packer/*`
      pages and ZERO under `/packer/integrations/`. Those pages nonetheless return HTTP 200; HashiCorp
      renders them from the plugin repo's own `.web-docs/` directory. The Tart builder field reference
      cited by 02-packer-tart-builder.md is one of them. ABSENCE FROM THE SITEMAP DOES NOT REFUTE A
      `/packer/integrations/` URL. Verify those with `curl -sS -o /dev/null -w '%{http_code}'` or by
      reading `cirruslabs/packer-plugin-tart`'s `.web-docs/`. Re-check this; do not inherit it.

════════════════════════════════════════════════════════════════════════════
HOUSE STANCE (every spec must remain consistent with this)
════════════════════════════════════════════════════════════════════════════

TART IS PRIMARY for CI and automated dotfiles testing (Packer builder, OCI registry, CLI, orchestrator).
UTM IS THE ESCAPE HATCH for interactive/GUI work, recovery-mode fiddling, and non-ARM guests.
Reasons: G1, G3, G5, G18. The licensing risk (G4) is the price, documented as an explicit accepted-risk
section with the core-count threshold we stay under. `mise` is the default `version_manager` (G12).
The golden image carries no build secret (G15, G17).

════════════════════════════════════════════════════════════════════════════
PLAN-FORMAT CONTRACT — specs/macos-ci.md feeds `/agent-harness:plan`
════════════════════════════════════════════════════════════════════════════

synth MUST keep these EXACT headings, in this EXACT order (note "Step by Step Tasks" has no hyphens, and
Acceptance Criteria comes BEFORE Validation Commands). They CURRENTLY CONFORM — do not regress them:

  # Plan: <task name>
  ## Task Description
  ## Objective
  ## Problem Statement
  ## Solution Approach
  ## Relevant Files          (### New Files subsection allowed)
  ## Implementation Phases   (### Phase 1: Foundation / ### Phase 2: Core Implementation / ### Phase 3: Integration & Polish)
  ## Step by Step Tasks      (### 1. <Task>, ### 2. <Task>, ...)
  ## Testing Strategy
  ## Acceptance Criteria
  ## Validation Commands
  ## Notes

task_type=feature, complexity=complex (every conditional section REQUIRED). `specs/macos-ci.md` must be
self-contained enough to hand to `/agent-harness:build` but LINK OUT to `specs/macos-ci/NN-*.md` for
depth. Target 250-400 lines; the depth lives in the sub-files.

════════════════════════════════════════════════════════════════════════════
WORKER BRIEFS
════════════════════════════════════════════════════════════════════════════

🔬 ledger -> .team/claims.jsonl, tools/verify_claims.py   [start immediately; you unblock everyone]
  You are the ONLY agent that may edit these two files. Read `tools/verify_claims.py` first — it works
  and passes 50/50; extend it only if a new evidence KIND is genuinely needed (justify in the backlog).
  Merge `.team/proposed/*.jsonl` -> `.team/claims.jsonl`: dedupe by `id`, reject malformed records (every
  record needs a `file` field), reject claims whose evidence does not reproduce (send back as CONFLICT),
  and keep `just verify-claims` exiting 0.
  ENFORCE THE TWO INVARIANTS: (a) NEVER delete or weaken any of the six `must_fail` claims; (b) EVERY
  negative `must_fail` probe over a `cli-help` command MUST have a positive control running the same
  argv+env — reject a bare negative probe as unfalsifiable.
  Report the claims delta. Then CROSS-AUDIT synth's files.

🍎 tart-core -> 01-tart-core.md, 02-packer-tart-builder.md
  Re-verify every CLI verb and every Packer field against a source. `tart --help` and `tart <verb> --help`
  are installed and allowed — USE THEM; a flag you remember is not a flag that exists. For tart.run pages,
  query the search index first. Propose `cli-help` claims for every flag the specs depend on
  (`--no-graphics`, `--vnc-experimental`, `--dir`, `clone`, `ip`, `delete`).
  READ G19 BEFORE YOU TOUCH 02. The Tart builder field reference lives at
  `developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart`, which is
  ABSENT FROM THE HASHICORP SITEMAP AND RETURNS 200. If you "refute" it by grepping the sitemap you have
  reproduced G10 in reverse and the run has failed. Verify it with `curl -sS -o /dev/null -w '%{http_code}'`
  or by reading `cirruslabs/packer-plugin-tart`'s `.web-docs/` on GitHub.
  `packer` IS installed (G14'). `packer inspect <dir>` is ALLOWED; `packer build`/`init` are NOT. Fields
  the docs page is silent on stay `<!-- UNVERIFIED -->` + an OQ.
  Then CROSS-AUDIT utm's files.

🏭 tart-ci -> 03-tart-ci-and-orchard.md, 04-tart-licensing-risk.md
  G4's dollar figures and core thresholds are the highest-risk numbers in this repo — a human signs off
  on them. Re-verify EVERY tier number against tart.run/licensing (find it via the search index) and
  propose a ledger claim per threshold. If a number moved, RETRACT loudly AND open a NEEDS-HUMAN OQ:
  a licence-cost change is a decision I make, not one you make. Confirm the Oct-2025 enforcement
  announcement still says what 04 claims. `cirrus` IS installed — `cirrus --help` and `cirrus run --help`
  are allowed.
  Then CROSS-AUDIT secrets' files.

🖥 utm -> 05-utm-automation.md, 06-utm-macos-guest.md, 07-utm-settings-appendix.md
  You own the files that carried the G10 damage. For EVERY docs.getutm.app URL in your three files:
  confirm it exists in the search index (`doc-index` claim), then `curl -fsSL` it and confirm the page
  actually SAYS what the spec claims (`doc-contains` claim). A URL that resolves is not a sentence that is
  true. Any URL absent from the index was FABRICATED — retract it, find the real page via the index, and
  file the correction. 07's table must carry accurate link status.
  Re-confirm G5, G6, G7, G18 from the pages themselves, not from the previous run's summary. G5 is the
  canonical `cli-help` trap: `utmctl start --help` advertises `--disposable`, the docs say QEMU-only, and
  BOTH claims belong in the ledger, naming each other.
  Then CROSS-AUDIT harness's files.

🧪 harness -> 08-dotfiles-test-harness.md, 09-dotfiles-under-test.md, 12-tooling-and-agent-loop.md
  READ THE LOCAL CLONES; they are the authority. Do NOT WebFetch GitHub for them:
      /Users/bossjones/dev/bossjones/zsh-dotfiles      /Users/bossjones/dev/bossjones/zsh-dotfiles-prep
  G12 reshapes the golden image — verify every bullet with a `file-contains` / `absent` / `file-line`
  claim, and RE-DERIVE the line numbers (they are approximate). Confirm the exact `smoke-test-docker.sh`
  apply invocation and the `retry -t 4` wrapper (the golden image must therefore install `retry` — verify
  `retry` appears in the brew prereq list).
  YOU OWN DEFECTS D2 AND D4. Spec 12's recipe table (`:200-202`) lists `build [IMAGE]`, `build-ipsw
  VERSION`, `images` — NONE of which exist; the Justfile has `build-golden`. And 12's "not yet built"
  framing is now wrong for `verify-claims`, `verify-claims-json`, `unverified-count`, `check`,
  `verify-no-secrets`, `build-golden` and `tools/verify_claims.py`, which ARE real. Redraw the
  "to build" / "already implemented" split against `just --summary` and `ls tools/ tests/`.
  12's VNC stdout format must stay `<!-- UNVERIFIED -->` (G13, OQ-02).
  Then CROSS-AUDIT tart-ci's files.

🔐 secrets -> 13-build-secrets.md   [NEW — the densest spec in the repo: 13 backing claims]
  Verify G15, G16, G17 line by line. `packer inspect tests/fixtures/packer-sensitive` is ALLOWED and is
  what four of your claims already run; `packer build` and `just build-golden` are FORBIDDEN.
  YOUR HARDEST JOB IS THE TWO must_fail/CONTROL PAIRS. For each pair
  (`packer-sensitive-hides-secret` ↔ `CONTROL-packer-inspect-prints-plain-literals`, and the
  `PACKER_LOG=1` pair), reason explicitly about WHY the bare negative probe is unfalsifiable alone: an
  empty output would satisfy "the secret is absent". Confirm the control asserts a literal that the SAME
  argv+env genuinely prints. A pair whose control is vacuous is a green check that means nothing — say so.
  Confirm the two `<!-- UNVERIFIED -->` markers at `13:51` and `13:54` STAY unverified: the residue
  reproduction used `hdiutil` on the host, not tart's own disk image, and `disk_format = "asif"` (macOS
  26+, sparse) may not behave like a raw image. Neither can be settled without booting a VM (OQ-01).
  YOU OWN DEFECT D1 (with harness): `Justfile:44` invokes `packer/tart-golden-image.pkr.hcl`, which does
  not exist. Say so in 13 rather than describing a template as though it were on disk.
  Then CROSS-AUDIT tart-core's files.

📚 synth -> 00-overview.md, 10-tart-vs-utm-adr.md, 11-sources.md, specs/macos-ci.md
  [BARRIER — idle until CROSS-AUDIT is CLEAN. You need everyone's retractions.]
  Reconcile contradictions ACROSS files — that is your unique value; nobody else sees the whole set.
  Check every cross-file `#anchor` (lychee already validates fragments; `just link-check` must be green).
  YOU OWN DEFECT D3: `00-overview.md:58` credits 13-build-secrets.md to owner `harness`; it is now
  `secrets`. Add 13 to any table that stops at 12.
  `11-sources.md` is the audit trail: each URL graded `[meaty | thin | fabricated-retracted]` with a
  one-line "what it gave us". Retractions get their own section — a reader must be able to see what the
  previous run got WRONG, not just what it got right. G14 belongs there too: the PROMPT was wrong, and
  that is worth recording. Document the G19 sitemap exception in `11-sources.md` next to the existing
  Packer-docs-URL-verification writeup.
  Update `specs/macos-ci.md` to the PLAN-FORMAT CONTRACT — it currently CONFORMS, so do not regress it.
  Introduce NO claim without a ledger entry.
  Before the barrier lifts, CROSS-AUDIT the ledger: are the 50 claims load-bearing, or trivia? A ledger
  full of easy claims is a green check that means nothing. Name the three most important claims that are
  MISSING, and open an OQ for each.

════════════════════════════════════════════════════════════════════════════
RULES EVERY AGENT OBEYS
════════════════════════════════════════════════════════════════════════════

- Edit ONLY your owned files. Propose claims to `.team/proposed/<role>.jsonl`. Everything else -> backlog.
  `.team/macos-ci.open-questions.md` is the ONE file everybody may append to. Append; never rewrite.
- NO installs, no VM boots, no host mutation. Read-only verification is REQUIRED (see the allowlist).
  `packer inspect` YES. `packer build` / `packer init` / `just build-golden` / `just verify-no-secrets` NO.
- Query the doc search index BEFORE typing a URL. A URL not in the index does not exist — WITHIN THAT
  INDEX'S DOMAIN. `/packer/integrations/**` is outside the sitemap's domain (G19); fetch it instead.
- Cite the source URL inline for every non-obvious claim, AND propose a ledger entry for it.
  Anything you assert but cannot verify gets an explicit `<!-- UNVERIFIED -->` on the line, citing an OQ
  number. Never present inference as fact. Never delete an UNVERIFIED marker without adding a passing claim.
- THE MOMENT YOU ARE STUCK, OPEN AN OQ. Do not save it for your final report. If you catch yourself typing
  "presumably" / "it appears" / "likely" / "should be", that is an OQ, not a sentence.
- Prefer a shorter spec that is entirely true over a long one padded with plausible detail.
- If a GROUND TRUTH conflicts with what you read, STOP and report to the lead in the backlog as a
  RETRACTION candidate, and open an OQ. Do not silently pick a side. G10 and G14 ARE PROOF THAT THE
  GROUND TRUTHS — AND THIS PROMPT — CAN BE WRONG.
- When red-teaming, default to refuted. Charity is how the last run shipped a fabricated URL. The ONE
  carve-out is G19: never refute a page you have not fetched.
- Keep your tab pill current on every state change. Fire `cmux notify` on every FSM transition AND the
  first time you open an OQ.
- End with exactly:
  `TASK-DONE: <role> | <one-line summary> | claims+N refuted-M unverified-K open-questions-J`
- The pre_tool_use hook blocks the substrings `rm `, `.env`, and `--rm`: use `mv` into the scratchpad
  instead of `rm`, and avoid the literal `.env` token.
- Lint Python with `uvx ruff check <file>` (ruff/ty are not on PATH). Bash is auto-rewritten through rtk.
  zsh does not word-split unquoted vars — inline lists or use `${=var}`.
- `just check` is the only definition of done. Paste its output; do not describe it.

Report back when the team is up with the roster (pane -> role -> surface) and the board rendered. When the
FSM reaches DONE, tell me — and lead with WHAT WE GOT WRONG, then THE OPEN QUESTIONS (NEEDS-HUMAN first),
then what we confirmed.
````

---

## After the run

When the FSM reports DONE, `just check` should still exit 0 from a clean shell:

```bash
cd /Users/bossjones/dev/bossjones/macos-ci
just check && echo "trustworthy"
```

Read `.team/macos-ci.open-questions.md` before you read anything else the team produced — the
`NEEDS-HUMAN` entries are the ones only you can close.

Then `/agent-harness:plan specs/macos-ci.md` in a separate terminal.
