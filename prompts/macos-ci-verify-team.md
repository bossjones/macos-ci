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

## What changed vs. the research prompt

| Research run | Verification run |
|---|---|
| "DOCS ONLY … rather than running it" | Read-only verification **required**; explicit allowlist |
| Ground truths are commandments | Ground truths are **claims to refute**; G10 retracted in-prompt |
| Citations = a URL | Citations = a **re-executable ledger entry** |
| Authors self-review | **Rotated cross-audit**; red-team posture, default-to-refuted |
| DONE = lead reads it | DONE = **`just check` exits 0**, output pasted |
| 6 panes | 7 panes (adds 🔬 `ledger`) |

## The feedback loop this run depends on

Already built, on disk, and passing `14/14`. Agents use it; they don't reinvent it.

- `.team/claims.jsonl` — one record per load-bearing assertion
- `tools/verify_claims.py` — re-executes the evidence behind each one
- `just check` — `link-check` + `verify-claims` + `unverified-count`

Evidence kinds: `file-contains`, `file-line` (catches hallucinated `file:line` citations), `absent`
(negative claims), `cli-help` (proves a flag exists), `doc-index` (proves a doc page exists — the direct
antidote to G10). One claim carries `"must_fail": true` and asserts the fabricated URL; if it ever starts
passing, the oracle has broken and the run fails loudly rather than going green on a dead check.

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
/boss-cmux Boot a 7-pane VERIFICATION/AUDIT team for the repo /Users/bossjones/dev/bossjones/macos-ci.

Reuse the open cmux window; add a NEW workspace named "macos-ci-verify" (cwd = that repo; do NOT pass
--env-file — the Claude panes use the existing login). Launch all 7 panes as
`claude --dangerously-skip-permissions` (I authorize bypass mode). Colour the workspace, label the tabs,
and after launching the 6 workers hand the lead its brief. Drive the LEAD only; the lead drives the rest.

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

Three lessons, binding on every agent here:

  1. A rule that forbids verification does not protect truth. It launders a guess into an axiom.
     In this run, read-only verification is MANDATORY, not forbidden.
  2. An assertion with a citation is not verified. It is decorated. A URL that resolves says nothing
     about whether the sentence citing it is true. Evidence must be re-executable.
  3. Authors cannot audit their own claims. Cross-audit is rotated, below.

SCOPE. This run writes markdown and ledger entries. NO agent installs tart/packer/UTM, pulls a VM image,
boots a VM, runs `brew install`, or mutates the host.

But read-only verification is REQUIRED, and these commands are explicitly ALLOWED and encouraged:

  - `<tool> --help` / `<tool> --version`   (tart, just, uv, cirrus, lychee, gh installed; packer is NOT)
  - `curl -fsSL <doc-index-url>`           (the search indexes below)
  - `grep` / `sed` / `rg` over the LOCAL clones of zsh-dotfiles and zsh-dotfiles-prep
  - `just link-check`, `just verify-claims`, `just check`
  - `uv run tools/verify_claims.py [--json]`
  - `git log`, `git show`, `git blame`

If you CAN check something with a read-only command and you don't, that is a defect, not caution.

════════════════════════════════════════════════════════════════════════════
THE ORACLE — use it before you ever type a URL
════════════════════════════════════════════════════════════════════════════

Both doc sites publish the static JSON index their own search box uses. THE INDEX IS THE AUTHORITATIVE
PAGE LIST: if a path is not in it, that page does not exist. No scraping, no 403, no guessing.

    # tart.run (MkDocs Material) — 101 pages, entries under .docs[]
    curl -fsSL https://tart.run/search/search_index.json |
      python3 -c 'import json,sys
    d=json.load(sys.stdin)
    for e in d["docs"]:
        if "fair source" in (e["title"]+e["text"]).lower(): print(e["title"], "->", e["location"])'

    # docs.getutm.app (Just the Docs) — 281 entries / 78 pages
    curl -fsSL https://docs.getutm.app/assets/js/search-data.json |
      python3 -c 'import json,sys
    d=json.load(sys.stdin)
    for v in d.values():
        if "trackpad" in (v["title"]+v["content"]).lower(): print(v["title"], "->", v["relUrl"])'

`docs.getutm.app` 403s WebFetch. Use `curl -fsSL`. One query for `trackpad` would have found the page
G10 missed. Query the index FIRST; fetch the page only to read its content.

════════════════════════════════════════════════════════════════════════════
THE FEEDBACK LOOP — this is how you know you are right
════════════════════════════════════════════════════════════════════════════

Already built and passing on the working tree. Do not reinvent it; USE it.

    just check              # link-check + verify-claims + unverified-count  <- THE GATE
    just verify-claims      # re-execute the evidence behind every claim
    just verify-claims-json # machine-readable; read this instead of scraping prose
    just unverified-count   # the honesty budget

`.team/claims.jsonl` — one JSON record per load-bearing assertion.
`tools/verify_claims.py` — re-executes the evidence. Exit 0 verified · 2 a claim failed ·
3 evidence unreachable · 4 usage.

Evidence kinds:

  file-contains  a local file contains a string        kills: claims about repos nobody opened
  file-line      line N of a file contains a string    kills: HALLUCINATED file:line CITATIONS
  absent         a string is NOT present               kills: unfalsifiable negative claims
  cli-help       `<tool> --help` emits a flag          kills: remembered flags that don't exist
  doc-index      a path is in the site's search index  kills: FABRICATED URLs — the G10 failure

Example records (exact shape; `.team/claims.jsonl` already has 14 passing):

    {"id":"G11-stdinIsATTY-line-2","kind":"file-line","file":"specs/macos-ci/09-dotfiles-under-test.md","target":"/Users/bossjones/dev/bossjones/zsh-dotfiles/home/.chezmoi.yaml.tmpl","line":2,"expect":"stdinIsATTY","claim":".chezmoi.yaml.tmpl:2 defines $interactive := stdinIsATTY"}
    {"id":"tart-has-vnc-experimental","kind":"cli-help","argv":["tart","run","--help"],"expect":"--vnc-experimental","claim":"tart run exposes --vnc-experimental"}
    {"id":"CONTROL-utm-settings-apple-devices-is-fabricated","kind":"doc-index","must_fail":true,"site":"utm","expect":"/settings-apple/devices/","claim":"CONTROL: must NOT verify. If it passes, the oracle is broken."}

THE LEDGER TESTS ITS OWN ORACLE. Any claim may set `"must_fail": true`, inverting the verdict. The
control claim above asserts the fabricated URL. If it ever starts PASSING, the `doc-index` oracle has
silently broken and every `doc-index` claim is worthless — the run must fail loudly rather than go green
on a dead check. Never delete or "fix" the control. (An UNREACHABLE result is never inverted.)

The rule of thumb, and it is not optional:

  Every non-obvious claim in a spec must resolve to one of three states:
    (a) a passing ledger entry,
    (b) an explicit `<!-- UNVERIFIED -->` marker on the line, or
    (c) deletion.
  There is no fourth state. "It sounds right" is state (c).

`just unverified-count` is an honesty budget. It must fall because claims got VERIFIED, never because
markers got DELETED. The lead records the count before and after and will reject a silent drop.

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
  📚 synth     — audits 00-overview.md, 10-tart-vs-utm-adr.md, 11-sources.md, specs/macos-ci.md;
                 reconciles cross-file contradictions  [BARRIER: idle until CROSS-AUDIT is CLEAN]

EXCLUSIVE FILE OWNERSHIP. An agent edits ONLY its own files. Everything else goes through
`.team/macos-ci.backlog.md`. Proposed claims go to `.team/proposed/<role>.jsonl`; ONLY 🔬 ledger merges
them into `.team/claims.jsonl`.

════════════════════════════════════════════════════════════════════════════
ROTATED CROSS-AUDIT — nobody grades their own homework
════════════════════════════════════════════════════════════════════════════

After each auditor finishes its OWN files, it red-teams ANOTHER agent's files:

    tart-core -> audits utm's files
    utm       -> audits harness's files
    harness   -> audits tart-ci's files
    tart-ci   -> audits tart-core's files
    synth     -> audits the ledger itself (are the claims load-bearing, or trivia?)
    ledger    -> audits synth's files

RED-TEAM POSTURE: TRY TO REFUTE, DEFAULT TO REFUTED. For each non-obvious claim in the file you are
auditing, attempt to construct the read-only command that would DISPROVE it. If you cannot verify it and
cannot disprove it, it goes to `<!-- UNVERIFIED -->`. Do not be charitable. The last run was charitable
and shipped a fabricated URL. File every refutation in the backlog as a CONFLICT.

════════════════════════════════════════════════════════════════════════════
FSM
════════════════════════════════════════════════════════════════════════════

  SCAFFOLD
    -> AUDIT-OWN      (tart-core | tart-ci | utm | harness in parallel; ledger seeds infra)
    -> LEDGER-MERGE   (ledger folds .team/proposed/*.jsonl into claims.jsonl)
    -> CROSS-AUDIT    (rotated, per the table above)
    -> GATE           (lead runs `just check`; MUST exit 0)
        |- CLEAN    -> SYNTH -> REVIEW -> DONE
        |- CONFLICT -> RECONCILE -> GATE (loop)
        \- ERROR    (unrecoverable)

FIRE `cmux notify --title "<role>" --body "<state>: <one-line>"` ON EVERY TRANSITION (each agent on its
own; lead on the global ones) so I'm pinged through the whole process.

THE FSM CANNOT REACH DONE UNTIL `just check` EXITS 0. Not "looks good." Exit zero. The lead pastes the
actual command output into `.team/macos-ci.board.md`. A claimed pass without pasted output is treated as
a failure.

════════════════════════════════════════════════════════════════════════════
STATUS BOARD
════════════════════════════════════════════════════════════════════════════

- Flags below were verified against cmux 0.64.17. Still trust `--help` over memory; never guess a flag.
- On EVERY state change, rename your OWN tab to a pill. `rename-tab` resolves its target as
  --tab -> --surface -> $CMUX_TAB_ID/$CMUX_SURFACE_ID -> focused tab, so renaming yourself needs NO
  target flag:

      cmux rename-tab "<emoji> <role> <n>/<N> [<progressbar>] · <one-line log>"

  emoji = 🔵 working / 🟢 done / 🔴 error / 🟡 refuted-a-claim, progressbar like [####------].
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
- LEAD keeps a board table (agent | state | n/N | claims-added | claims-refuted | last log) in
  `.team/macos-ci.board.md` and a living task list in `.team/macos-ci.backlog.md`.

════════════════════════════════════════════════════════════════════════════
LEAD BRIEF
════════════════════════════════════════════════════════════════════════════

1) SCAFFOLD. `mkdir -p .team/proposed`. Record the BASELINE: run `just check` and
   `just unverified-count`, paste both outputs into the board. Write the backlog. Dispatch ledger +
   the 4 auditors IN PARALLEL. synth STAYS IDLE (barrier).

2) Wait on `cmux events --name notification.created --no-heartbeat --no-ack` matching this workspace_id.
   Do NOT busy-poll. Once notified, confirm with `cmux read-screen --surface <ref> --scrollback
   --lines 40` and check for `TASK-DONE: <role> | <summary>`.

3) LEDGER-MERGE. Release 🔬 ledger to fold `.team/proposed/*.jsonl` into `.team/claims.jsonl`.
   `just verify-claims` must exit 0 before CROSS-AUDIT begins. A proposed claim that fails is a finding,
   not a bug to silence: route it back to the owning agent as a CONFLICT.

4) CROSS-AUDIT. Dispatch the rotation. Collect refutations from the backlog.

5) GATE. Run `just check` PERSONALLY and paste the output. Exit 0 or the FSM does not advance.
   Then verify the honesty budget: `just unverified-count` may only have dropped where a corresponding
   ledger claim was ADDED. Diff it against the baseline from step 1. A marker that vanished without a
   claim is a CONFLICT.

6) SYNTH. Release synth. It reconciles cross-file contradictions and updates 00 / 10 / 11 /
   `specs/macos-ci.md`. It must NOT introduce a new claim without a ledger entry.

7) REVIEW + DONE. Lead reads `specs/macos-ci.md` end-to-end against the PLAN-FORMAT CONTRACT below.
   Re-run `just check`. Set the board all-🟢, `cmux set-status state done --workspace <ws>
   --color "#196F3D"`, notify DONE, and report: the roster (pane -> role -> surface), the rendered board,
   the claims delta (added / refuted / still-UNVERIFIED), and EVERY GROUND TRUTH THAT WAS RETRACTED.

════════════════════════════════════════════════════════════════════════════
GROUND TRUTHS — now CLAIMS, not commandments
════════════════════════════════════════════════════════════════════════════

Each of these was asserted by the previous run. YOUR JOB IS TO TRY TO BREAK THEM. A ground truth that
survives a genuine refutation attempt earns a ledger entry. One that cannot be checked either way gets
`<!-- UNVERIFIED -->`. One that fails gets RETRACTED, loudly, in the board and in `11-sources.md`.

Report retractions to the lead. Do not silently pick a side.

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
  G6. UTM's Apple backend does NOT support multiple graphical displays.
  G7. `advanced/rosetta` is about running x86_64 ELF binaries in LINUX guests, not macOS guests.
  G8. tart headless on macOS 15+ hosts has a keychain requirement; nested virtualisation needs M3/M4
      AND a Linux guest. Prebuilt ghcr.io images cover macOS 12-26; default creds admin/admin.
  G9. NEITHER dotfiles repo uses Ansible. Ansible is a wrapper we may CHOOSE, not something inherited.

  ~~G10.~~ RETRACTED — WAS FALSE. Three of the four "404" URLs return HTTP 200. The fourth,
      `settings-apple/devices/`, was FABRICATED — it is absent from UTM's 78-page search index. The real
      device-toggle page is `settings-apple/virtualization/`. A `must_fail` control claim now guards
      this. NEVER RESTORE G10. Its existence is the reason this run exists.

  G11. NON-INTERACTIVE CHEZMOI IS SOLVED UPSTREAM. Both repos are checked out LOCALLY — read them, do
      not WebFetch:  /Users/bossjones/dev/bossjones/zsh-dotfiles  and  .../zsh-dotfiles-prep
      Already ledger-verified (14/14 passing); CONFIRM, do not re-derive:
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

  G12. NEW — THE PREP-INSTALLER BOUNDARY. Verify each; they reshape the golden image.
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

  G13. NEW — THE GUI IS REACHABLE. `tart run --help` (tart 2.32.1) exposes `--no-graphics`, `--vnc`, and
      `--vnc-experimental`. The latter uses Virtualization.framework's own VNC server and prints
      `Opening vnc://:<password>@127.0.0.1:<port>...`. Packer's tart builder drives `boot_command` over
      this same channel (`disable_vnc`, `vnc_port_min/max`).
      THE EXACT STDOUT FORMAT IS `<!-- UNVERIFIED -->` — it comes from one reported example, not from a
      booted VM. Do NOT upgrade it to fact without booting one, which this run may not do.

  G14. NEW — HOST STATE. `tart` 2.32.1, `just`, `uv`, `cirrus`, `lychee` 0.22.0, `gh` are installed.
      `packer` is NOT. Confirm with `cli-help` ledger entries; this is `just doctor`'s first test case.

════════════════════════════════════════════════════════════════════════════
HOUSE STANCE (every spec must remain consistent with this)
════════════════════════════════════════════════════════════════════════════

TART IS PRIMARY for CI and automated dotfiles testing (Packer builder, OCI registry, CLI, orchestrator).
UTM IS THE ESCAPE HATCH for interactive/GUI work, recovery-mode fiddling, and non-ARM guests.
Reasons: G1, G3, G5. The licensing risk (G4) is the price, documented as an explicit accepted-risk
section with the core-count threshold we stay under. `mise` is the default `version_manager` (G12).

════════════════════════════════════════════════════════════════════════════
PLAN-FORMAT CONTRACT — specs/macos-ci.md feeds `/agent-harness:plan`
════════════════════════════════════════════════════════════════════════════

synth MUST keep these EXACT headings, in this EXACT order (note "Step by Step Tasks" has no hyphens, and
Acceptance Criteria comes BEFORE Validation Commands):

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
  and passes 14/14; extend it only if a new evidence KIND is genuinely needed (justify in the backlog).
  Merge `.team/proposed/*.jsonl` -> `.team/claims.jsonl`: dedupe by `id`, reject malformed records,
  reject claims whose evidence does not reproduce (send back as CONFLICT), and keep `just verify-claims`
  exiting 0. NEVER delete or weaken the `must_fail` CONTROL claim. Report the claims delta.
  Then CROSS-AUDIT synth's files.

🍎 tart-core -> 01-tart-core.md, 02-packer-tart-builder.md
  Re-verify every CLI verb and every Packer field against a source. `tart --help` and `tart <verb> --help`
  are installed and allowed — USE THEM; a flag you remember is not a flag that exists. For tart.run pages,
  query the search index first. Propose `cli-help` claims for every flag the specs depend on
  (`--no-graphics`, `--vnc-experimental`, `--dir`, `clone`, `ip`, `delete`). `packer` is NOT installed, so
  Packer builder fields must be verified against the HashiCorp page (canonical; the plugin README is a
  thin stub) and marked `<!-- UNVERIFIED -->` where the page is silent.
  Then CROSS-AUDIT utm's files.

🏭 tart-ci -> 03-tart-ci-and-orchard.md, 04-tart-licensing-risk.md
  G4's dollar figures and core thresholds are the highest-risk numbers in this repo — a human signs off
  on them. Re-verify EVERY tier number against tart.run/licensing (find it via the search index) and
  propose a ledger claim per threshold. If a number moved, RETRACT loudly. Confirm the Oct-2025
  enforcement announcement still says what 04 claims. `cirrus` IS installed — `cirrus --help` and
  `cirrus run --help` are allowed.
  Then CROSS-AUDIT tart-core's files.

🖥 utm -> 05-utm-automation.md, 06-utm-macos-guest.md, 07-utm-settings-appendix.md
  You own the files that carried the G10 damage. For EVERY docs.getutm.app URL in your three files:
  confirm it exists in the search index (`doc-index` claim), then `curl -fsSL` it and confirm the page
  actually says what the spec claims. Any URL absent from the index was FABRICATED — retract it, find the
  real page via the index, and file the correction. 07's table must carry accurate link status.
  Re-confirm G5, G6, G7 from the pages themselves, not from the previous run's summary.
  Then CROSS-AUDIT harness's files.

🧪 harness -> 08-dotfiles-test-harness.md, 09-dotfiles-under-test.md, 12-tooling-and-agent-loop.md
  READ THE LOCAL CLONES; they are the authority. Do NOT WebFetch GitHub for them:
      /Users/bossjones/dev/bossjones/zsh-dotfiles      /Users/bossjones/dev/bossjones/zsh-dotfiles-prep
  G12 is new and reshapes the golden image — verify every bullet with a `file-contains` / `absent` /
  `file-line` claim, and RE-DERIVE the line numbers (they are approximate). Confirm the exact
  `smoke-test-docker.sh` apply invocation and the `retry -t 4` wrapper (the golden image must therefore
  install `retry` — verify `retry` appears in the brew prereq list). 12 describes tooling that does NOT
  exist yet except `Justfile`/`lychee.toml`/`CLAUDE.md`/`tools/verify_claims.py`/`.team/claims.jsonl` —
  make sure 12 says "to build" where nothing exists and "already implemented" where it does. Its VNC
  stdout format must stay `<!-- UNVERIFIED -->` (G13).
  Then CROSS-AUDIT tart-ci's files.

📚 synth -> 00-overview.md, 10-tart-vs-utm-adr.md, 11-sources.md, specs/macos-ci.md
  [BARRIER — idle until CROSS-AUDIT is CLEAN. You need everyone's retractions.]
  Reconcile contradictions ACROSS files — that is your unique value; nobody else sees the whole set.
  Check every cross-file `#anchor` (lychee already validates fragments; `just link-check` must be green).
  `11-sources.md` is the audit trail: each URL graded `[meaty | thin | fabricated-retracted]` with a
  one-line "what it gave us". Retractions get their own section — a reader must be able to see what the
  previous run got WRONG, not just what it got right. Update `specs/macos-ci.md` to the PLAN-FORMAT
  CONTRACT. Introduce NO claim without a ledger entry.
  Before the barrier lifts, CROSS-AUDIT the ledger: are the 14 claims load-bearing, or trivia? A ledger
  full of easy claims is a green check that means nothing. Name the three most important claims that are
  MISSING.

════════════════════════════════════════════════════════════════════════════
RULES EVERY AGENT OBEYS
════════════════════════════════════════════════════════════════════════════

- Edit ONLY your owned files. Propose claims to `.team/proposed/<role>.jsonl`. Everything else -> backlog.
- NO installs, no VM boots, no host mutation. Read-only verification is REQUIRED (see the allowlist).
- Query the doc search index BEFORE typing a URL. A URL not in the index does not exist.
- Cite the source URL inline for every non-obvious claim, AND propose a ledger entry for it.
  Anything you assert but cannot verify gets an explicit `<!-- UNVERIFIED -->` on the line.
  Never present inference as fact. Never delete an UNVERIFIED marker without adding a passing claim.
- Prefer a shorter spec that is entirely true over a long one padded with plausible detail.
- If a GROUND TRUTH conflicts with what you read, STOP and report to the lead in the backlog as a
  RETRACTION candidate. Do not silently pick a side. G10 IS PROOF THAT THE GROUND TRUTHS CAN BE WRONG.
- When red-teaming, default to refuted. Charity is how the last run shipped a fabricated URL.
- Keep your tab pill current on every state change. Fire `cmux notify` on every FSM transition.
- End with exactly: `TASK-DONE: <role> | <one-line summary> | claims+N refuted-M unverified-K`
- The pre_tool_use hook blocks the substrings `rm `, `.env`, and `--rm`: use `mv` into the scratchpad
  instead of `rm`, and avoid the literal `.env` token.
- Lint Python with `uvx ruff check <file>` (ruff/ty are not on PATH). Bash is auto-rewritten through rtk.
  zsh does not word-split unquoted vars — inline lists or use `${=var}`.
- `just check` is the only definition of done. Paste its output; do not describe it.

Report back when the team is up with the roster (pane -> role -> surface) and the board rendered. When the
FSM reaches DONE, tell me — and lead with WHAT WE GOT WRONG, then what we confirmed.
````

---

## After the run

When the FSM reports DONE, `just check` should still exit 0 from a clean shell:

```bash
cd /Users/bossjones/dev/bossjones/macos-ci
just check && echo "trustworthy"
```

Then `/agent-harness:plan specs/macos-ci.md` in a separate terminal.
