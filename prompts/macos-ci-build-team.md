# boss-cmux — macos-ci BUILD run

Third prompt in the lineage. [`macos-ci-research-team`](macos-ci-research-team.md) **wrote** the specs.
[`macos-ci-verify-team`](macos-ci-verify-team.md) **proved** them. This run **builds** what they describe:
the `macos-ci` package, the Justfile, both Packer lanes, and the real golden macOS image — implementing
[specs/macos-ci.md](../specs/macos-ci.md) steps 1–14, TDD red-first.

## What changed vs. the verify run

| Verify run | Build run |
|---|---|
| Read-only; `packer build` forbidden | **Mutating**: writes code, runs the real `packer build`, boots VMs |
| 8 panes, all auditors | 7 panes: 5 builders/watchers + a lead + a **plain terminal** that runs the build |
| DONE = `just check` exits 0 | DONE = `just check` **AND** full `uv run pytest` exit 0, output pasted |
| Human drives the lead ad hoc | An **orchestrator session** drives the lead: 60s polls, 2-min reports, 3-min stall probes |
| No long-running ops | An hour-scale image build, watched by a dedicated 📡 log-watcher with a transient-vs-fatal triage table |

Two lessons this run inherits unchanged: **the prompt is not privileged over the evidence**, and
**silence is never success**. Two lessons it adds, from the orchestration retrospective of the verify
run (the `probe-stalled-agent-fleets` note in the operator's Claude memory): poll by
**artifacts, not pixels** (screens go stale; files and exit codes do not), and **some build-time errors
are weather, not climate** — packer retrying SSH for ten minutes is a Tuesday; the log-watcher exists to
tell the difference instead of crying wolf or going quiet.

## The request that generated this prompt

> The time has come to create a new prompt to implement the specs/macos-ci.md … One of the agents should
> actively look at logs from tart, utm, packer or whatever to ensure we have a quick feedback loop … some
> build time errors might not immediately be an issue and might resolve themselves over time … The main
> claude prompt (the orchestrator that kicks off all of the cmux windows/panes) should check on the status
> every 2 mins … In the past I've found myself waiting to hear back and had to prompt the orchestrator to
> check on the status manually … as much parallel work as possible without the agents stepping over each
> other. KISS. Remember TDD.

Decisions recorded at authoring time (2026-07-10): all workers run **Sonnet**; the golden image is built
**for real** this run; **G4 licensing sign-off is GIVEN** (see Wave 0); the tokenless-build acceptance leg
is deferred rather than doubling the critical path.

---

## The prompt

Paste everything inside the fence into a fresh Claude Code session started in
`/Users/bossjones/dev/bossjones/macos-ci`. That session is the ORCHESTRATOR.

````text
/boss-cmux Boot a 7-pane BUILD team for the repo /Users/bossjones/dev/bossjones/macos-ci and implement
specs/macos-ci.md steps 1-14, TDD red-first, including the real golden-image Packer build.

You are the ORCHESTRATOR. You spawn the workspace, hand the lead its brief, then run the HEARTBEAT loop
(below) until DONE — you never go quiet on the human. Drive the LEAD only; the lead drives the workers.

Reuse the open cmux window; add a NEW workspace named "macos-ci-build" (cwd = the repo; do NOT pass
--env-file — the Claude panes use the existing login, and the literal `.env` token is hook-blocked
anyway). Launch the 6 agent panes as `claude --model sonnet --dangerously-skip-permissions` (I authorize
bypass mode). The 7th pane is a PLAIN SHELL — no agent — reserved for the packer build so its output is
a tee'd file anyone can tail.

DO NOT run `cmux hooks setup` — `cmux hooks --help` states Claude Code hooks are injected automatically
by the cmux Claude wrapper. Regardless, every agent ALSO fires `cmux notify` explicitly on each FSM
transition and prints a `TASK-DONE:` sentinel, because a semantic per-transition signal beats a generic
turn-stop.

════════════════════════════════════════════════════════════════════════════
BINDING LESSONS — from two previous runs; every agent obeys them
════════════════════════════════════════════════════════════════════════════

1. THE PROMPT IS NOT PRIVILEGED OVER THE EVIDENCE. If anything below contradicts a passing ledger claim,
   a failing test, or a command you just ran, the evidence wins. Report the contradiction; do not soften
   what you observed. (The verify run retracted two of its own ground truths this way.)
2. `cmux send` TYPES; `cmux send-key <ref> enter` SUBMITS; `cmux read-screen --surface <ref> --lines 15`
   CONFIRMS. Three steps, every dispatch. A skipped enter strands the prompt in the composer silently —
   the target agent never runs, never errors, and anyone waiting on its sentinel waits forever. One
   SINGLE-LINE task per send: every newline submits a separate prompt. There is no Ctrl-C; to stop a
   pane, `close-surface` it.
3. CONFIRM BY ARTIFACTS, NOT PIXELS. Progress = `git status --short` deltas, `.team/` file mtimes, log
   byte offsets, test/gate exit codes, `cmux tree --all` pill changes. `read-screen --scrollback` has
   been observed to return only the viewport — never rely on scrollback for anything load-bearing; rely
   on sentinels, files, and exit codes. Never match spinner text. SILENCE IS NEVER SUCCESS.
4. cmux short refs (`surface:N`) are positional and renumber. The stable handles are the window UUID and
   the roster file. Re-resolve surface refs at the moment of use via
   `cmux list-pane-surfaces --workspace <ws>`, and scope every split/send with `--workspace`.
5. Flags below were spot-checked against cmux 0.64.17 on this host. Still trust `cmux <cmd> --help` over
   memory; never guess a flag.

SCOPE. This run writes code, runs `uv`, `pytest`, `packer init/validate/build`, `just` recipes, boots and
deletes tart VMs it created, and makes LOCAL git commits at phase boundaries (conventional messages,
current branch). It does NOT: push, switch branches, touch `~/.tart` VMs it did not create, mutate
`.team/claims.jsonl` (read-only inheritance — `just check` must stay green the entire run), or delete the
`.team/macos-ci.*` files from previous runs.

════════════════════════════════════════════════════════════════════════════
WORKSPACE SETUP — exact recipe
════════════════════════════════════════════════════════════════════════════

Preflight; auto-launch cmux if the socket is down:

    if ! cmux identify --json >/dev/null 2>&1; then
      open -a cmux
      for i in $(seq 1 30); do cmux identify --json >/dev/null 2>&1 && break; sleep 0.5; done
    fi

Reuse the open window (only `new-window` if none exists), then:

    read WS LEAD < <(cmux workspace create --window "$WIN" --name "macos-ci-build" \
                       --cwd "$REPO" --focus true --json | jq -r '[.workspace_ref,.surface_ref]|@tsv')
    cmux focus-window --window "$WIN"
    CORE=$(cmux new-split right --workspace "$WS" --surface "$LEAD"  --json | jq -r .surface_ref)  # lead = left half
    PACK=$(cmux new-split down  --workspace "$WS" --surface "$CORE"  --json | jq -r .surface_ref)
    HARN=$(cmux new-split right --workspace "$WS" --surface "$CORE"  --json | jq -r .surface_ref)
    VALD=$(cmux new-split right --workspace "$WS" --surface "$PACK"  --json | jq -r .surface_ref)
    WTCH=$(cmux new-split down  --workspace "$WS" --surface "$VALD"  --json | jq -r .surface_ref)
    BULD=$(cmux new-split down  --workspace "$WS" --surface "$PACK"  --json | jq -r .surface_ref)  # plain shell

Identity, so the human can tell everyone apart at a glance:

    cmux rename-tab --workspace "$WS" --surface "$LEAD" "👑 lead"
    cmux rename-tab --workspace "$WS" --surface "$CORE" "🐍 core-builder"
    cmux rename-tab --workspace "$WS" --surface "$PACK" "📦 packer-builder"
    cmux rename-tab --workspace "$WS" --surface "$HARN" "🛠 harness-builder"
    cmux rename-tab --workspace "$WS" --surface "$VALD" "✅ validator"
    cmux rename-tab --workspace "$WS" --surface "$WTCH" "📡 log-watcher"
    cmux rename-tab --workspace "$WS" --surface "$BULD" "🏗 build (no agent)"
    cmux workspace-action --action set-color --workspace "$WS" --color Orange
    cmux set-status state SCAFFOLD --workspace "$WS" --icon hammer.fill --color "#1565C0"

Persist the roster to `.team/macos-ci-build.spawn.json` (window UUID, workspace ref, role -> surface ref,
sentinel `TASK-DONE`). Launch the FIVE WORKERS first (type each launch line INTO its pane via send +
send-key enter; kickoff = "You are <role> on team macos-ci-build. Read .team/macos-ci-build.backlog.md
for your brief. Reply 'ready: <role>' and wait for the lead."), wait ~6s, then launch the lead with its
brief. The BUILD pane gets no agent — leave it at a shell prompt.

════════════════════════════════════════════════════════════════════════════
ROLES AND EXCLUSIVE FILE OWNERSHIP — no file has two writers, ever
════════════════════════════════════════════════════════════════════════════

  👑 lead            .team/macos-ci-build.board.md, .team/macos-ci-build.backlog.md,
                     README.md (the G4 sign-off record), CLAUDE.md
  🐍 core-builder    pyproject.toml, src/macos_ci/{cli,config,tart,doctor,artifacts}.py,
                     ALL pure cores src/macos_ci/_{config,tart,doctor,harness,triage,gui}_core.py,
                     tests/unit/**
  📦 packer-builder  macos-versions.toml, packer/**, .cirrus.yml; creates logs/packer-build-*.log
  🛠 harness-builder Justfile, Makefile, src/macos_ci/{harness,gui,vm_debug}.py (after the handoff),
                     harness/seed-config/**, tests/{integration,pty,gui,manual}/**
  ✅ validator       .claude/agents/**, .claude/commands/** (the step-12 rewrite); ANY other file only
                     under a lead-issued LOAN TICKET (backlog entry naming the file, the defect, the
                     owner cc'd; ownership returns when the ticket closes)
  📡 log-watcher     .team/logwatch.md (append-only) — and NOTHING else

ONE recorded handoff at SCAFFOLD: core-builder scaffolds `src/macos_ci/` including one-line typer-app
stubs for `harness.py`, `gui.py`, `vm_debug.py`, mounted as sub-apps in `cli.py`; then ownership of those
three stubs transfers to harness-builder, logged on the board. After that the table above is law.
Cross-fence needs (e.g. harness-builder wants a new `_harness_core` function) go through the backlog.
`.team/macos-ci.{board,backlog,open-questions}.md` and `.team/claims.jsonl` from previous runs are
READ-ONLY inheritance. The open-questions protocol continues in `.team/macos-ci-build.open-questions.md`
— same rules as the verify run: append-only, `OQ-NN` blocks, file one THE MOMENT you are stuck, notify on
first open, "presumably/likely/should be" is an OQ not a sentence, an open question is a SUCCESS.

════════════════════════════════════════════════════════════════════════════
TDD — non-negotiable, checked by the validator
════════════════════════════════════════════════════════════════════════════

- RED FIRST for every pure core: the failing unit test exists and FAILS before the implementation does.
  Your TASK-DONE sentinel carries `red-first-Y/N` and the validator will check the test actually fails
  when the implementation is stubbed out.
- Hermetic tier touches NO network, NO VM: `pytest-subprocess` registers a fake `tart` binary and tests
  assert on argv. `uv run pytest` and `uvx ruff check .` stay green continuously — a red tree blocks
  everyone, fix it before new work.
- `-m vm/pty/gui/manual` tiers are DESELECTED by default; a bare `uv run pytest` must deselect all of
  them (spec step 11 makes this an acceptance criterion — test it).
- The validator independently re-runs the tests before accepting any TASK-DONE. A described pass is a
  failure.

════════════════════════════════════════════════════════════════════════════
STEP ASSIGNMENTS — waves, and the one barrier that matters
════════════════════════════════════════════════════════════════════════════

WAVE 0 — lead, minutes, before dispatching anyone:
  Step 1: verify host prereqs READ-ONLY (`tart --version` 2.32.1, `packer --version` 1.15.4, `just`,
    `uv`, `cirrus`, `gh auth status`; free disk >= 60GB via `df -h`) and paste the output to the board.
  Step 2: G4 LICENSING SIGN-OFF WAS GIVEN BY THE HUMAN ON 2026-07-10 (fleet ceiling: <=3 hosts,
    <=100 combined CPU cores). DO NOT RE-ASK. Record it durably in README.md with the date, and file a
    backlog item for core-builder: `just doctor` must REPORT the ceiling; it must never silently
    approve it.
  Baseline: run `just check` (must exit 0) and paste. If it does not, STOP and report to the
    orchestrator before dispatching — the inherited ledger is broken and this run may not proceed on a
    red gate.

WAVE 1 — parallel; 📦 is the critical path, unblock it first:
  Step 3  -> 🐍 core-builder: pyproject.toml (hatchling, `[project.scripts] macos-ci = "macos_ci.cli:app"`),
             scaffold, then RED-FIRST tests + implementations for `_gui_core.parse_vnc_url`,
             `_config_core.load`, `_tart_core.clone_argv`, `_doctor_core.check`; then `doctor.py`
             (`just doctor --json` writes `artifacts/<run-id>/doctor.json`, exit 2 on any miss, reports
             the G4 ceiling).
  Step 4  -> 🛠 harness-builder: implement the spec-12 recipe table in the Justfile — EXTEND, never
             break: `check`, `link-check*`, `verify-claims*`, `unverified-count`, `verify-no-secrets`
             survive verbatim; spec calls the build recipe `build`, the live Justfile has `build-golden`
             — implement `build` and keep `build-golden` as an alias (ledger claims reference it).
             Makefile shim. Add `Bash(just:*)` to .claude/settings.json permissions.allow.
  Step 5 + 6a(template half) -> 📦 packer-builder: `macos-versions.toml`; `packer/tart-golden-image.pkr.hcl`
             per specs/macos-ci/02 (vm_base_name = ghcr.io/cirruslabs/macos-*-base, sized for
             Homebrew+CLT, headless = true, ssh admin/admin PLAIN — G16: never mark a common word
             sensitive); ONE idempotent shell provisioner installing Xcode CLT, Homebrew, chezmoi, and
             the brew prereq list INCLUDING `retry`, and NOT zsh-dotfiles-prep. Wire the token NOW so
             there is ONE build, not two: `homebrew_github_api_token` declared `sensitive = true`,
             `default = env("HOMEBREW_GITHUB_API_TOKEN")`, passed with the `GIT_CONFIG_COUNT/KEY_n/VALUE_n`
             anonymous-HTTPS rewrite through the provisioner's `environment_vars` wrapped in `compact()`;
             `use_env_var_file` stays default false (true writes the secret INTO the guest — G15).
             Also `packer/ipsw/<version>.pkr.hcl` (`from_ipsw = var.ipsw_url`, boot_command — validate
             every wait token; remember upstream's typo'd `<wai7s>` cautionary tale).
             Then `packer init` + `packer validate` BOTH lanes.

BUILD-LAUNCH — the barrier opens when step 1 is pasted AND `packer validate` exits 0 (it does NOT wait
for steps 3/4). 📦 packer-builder re-resolves the 🏗 build pane's ref from the roster workspace and
launches INTO IT (send + send-key enter):

    just build-golden 2>&1 | tee logs/packer-build-$(date +%Y%m%d-%H%M%S).log

Then 📡 log-watcher arms on the newest log file. Nobody else touches the build pane.
Note for the board: the acceptance leg "build also succeeds WITHOUT the token" implies a second
hour-scale build — record it as an explicit DEFERRED post-DONE item, do not run it silently.

SHADOW WORK — while the build runs (an hour is a terrible thing to waste); ALL of this is authorable and
hermetically testable with no image:
  🐍 core-builder: RED-FIRST `_harness_core` (run-id, artifact layout, `chezmoi_argv()` reproducing
     smoke-test-docker.sh:361-365 verbatim, parameterized on version_manager, default mise),
     `_triage_core` (failure-signature table + `match(log_lines)`, tested against fixture log text),
     `_gui_core` completion.
  🛠 harness-builder: `harness.py` (clone -> headless run -> poll `tart ip` -> `--dir` mount -> SSH no
     `-t` -> `chezmoi diff` then apply under `retry -t 4`, CM_computer_name/CM_hostname per run, never
     mutate the golden image); seed-config lever (step 8, `~/.config/chezmoi/chezmoi.yaml` pre-seed — no
     `--promptBool` non-TTY, G11); assertion layer (step 9, pytest-testinfra `-m vm`, conftest polls
     `host.run("true").rc == 0` to a deadline); teardown (step 10, `--keep-on-failure`, `just prune`);
     pty/gui/manual tier FILES (step 11).
  📦 packer-builder: `.cirrus.yml` (step 13) + IPSW lane polish. It does NOT babysit the build — that is
     the watcher's job.
  ✅ validator: red-team steps 3-5 as they land (re-run tests, stub implementations to prove reds were
     red, try to break doctor's failure paths); rewrite the inherited Multipass `.claude/` triage tooling
     for the tart/SSH log model (step 12); fix small defects under loan tickets or bounce to the owner.
  👑 lead: board upkeep, backlog routing, and the MID-BUILD HERMETIC GATE (HG): `uv run pytest` AND
     `just check` both exit 0 on the pre-image tree, output pasted. HG must pass BEFORE IMAGE-READY is
     accepted, so integration starts from a known-green tree the moment the image lands.

IMAGE-GATED — only after the build exits 0:
  Step 6 smoke: `tart clone` the golden image once, boot it, `chezmoi --version && brew doctor` inside,
     delete the clone. (📦)
  Step 6a verification half: `just verify-no-secrets <vm>` exits 0 — AND the ✅ validator first PLANTS
     the token in a scratch file under the VM dir and confirms the recipe exits 2. Never trust a canary
     you have not seen fail.
  Steps 7-10 live: first real `just up` / `just run` / `just destroy` cycle; `-m vm` tier runs green;
     teardown proven (`tart list` shows no orphans). (🛠 executes, ✅ red-teams)
  Step 11: pty/gui tiers exercised against a live clone.
  Step 14: `just matrix` across {sequoia} x {mise, asdf}: the asdf leg WITHOUT --with-prereq-installer is
     EXPECTED to fail and that failure is a CORRECT RESULT TO RECORD, not a bug to paper over. Then break
     something on purpose (malformed template in a scratch ZSH_DOTFILES tree) and confirm verdict.json
     names phase `chezmoi-diff` and the cause. `cirrus run` parity check (step 13's acceptance). (🛠 + ✅)

════════════════════════════════════════════════════════════════════════════
FSM
════════════════════════════════════════════════════════════════════════════

  SCAFFOLD -> PRE-IMAGE (wave 1 in parallel)
    -> BUILD-LAUNCH   (packer validate exit 0; tee'd build starts in the 🏗 pane; watcher arms)
    -> SHADOW-WORK    (concurrent with the build; HG gate must pass inside this state)
    -> IMAGE-READY    (build exit 0 — watcher reports it, lead confirms THE EXIT CODE FROM THE LOG TAIL,
        |              never from read-screen)
        |- BUILD-FAILED -> TRIAGE -> FIX -> BUILD-LAUNCH   (max 2 relaunches, then NEEDS-HUMAN,
        |                                                   board flagged red)
    -> SMOKE -> INTEGRATE (validator red-team loop) -> MATRIX
    -> GATE           (lead PERSONALLY runs `just check` AND `uv run pytest`; BOTH exit 0; raw output
        |              PASTED into the board — a described pass is a failure)
        |- CLEAN  -> DONE
        |- DIRTY  -> FIX -> GATE (loop)
        \- ERROR  -> NEEDS-HUMAN

Every agent fires `cmux notify --title "<role>" --body "<state>: <one-line>"` on every transition of its
own, and the first time it opens an OQ. The lead fires the global ones. Tab pills on every state change
(self-rename needs no target flag): `<emoji> <role> <n>/<N> [####------] · <one-line log>` with
🔵 working / 🟢 done / 🔴 error / 🟡 fixing-a-defect / ❓ blocked-on-OQ. Lead mirrors coarse state:
`cmux set-status state <STATE> --workspace <ws> --color <#1565C0 working|#196F3D done|#C0392B error>`
and `cmux set-progress <0.0-1.0> --label "<state>" --workspace <ws>`. Completion sentinel, exact:
`TASK-DONE: <role> | <one-line summary> | tests+N red-first-Y/N`.
The BOARD IS THE DURABLE STATE: any restarted or confused agent is told "read
.team/macos-ci-build.board.md and resume from the recorded state". Local git commits at phase
boundaries (SCAFFOLD baseline, HG, IMAGE-READY, GATE-clean) — lead commits, conventional messages,
NEVER push.

════════════════════════════════════════════════════════════════════════════
📡 LOG-WATCHER PROTOCOL — watch the build, review the repo, feed the lead intel
════════════════════════════════════════════════════════════════════════════

The tee'd LOG FILE is the single source of truth. `read-screen` on the 🏗 build pane is BANNED —
scrollback wraps and re-renders. Each cycle (~45-60s, bounded loops only):

    LOG=$(ls -t logs/packer-build-*.log | head -1)
    SIZE=$(stat -f%z "$LOG")                      # vs $LAST from the previous cycle
    tail -c +$((LAST+1)) "$LOG" | tail -n 40      # only NEW bytes, bounded
    pgrep -f 'packer build' >/dev/null || echo "PROCESS GONE"

Track: byte offset, wall-clock of last growth, inferred phase (pull -> boot -> ssh-wait -> provision ->
export), and the packer PID. A dead process with no success line is itself FATAL.

TRIAGE TABLE — the human's words: "some build time errors might not immediately be an issue and might
resolve themselves over time." Judge accordingly:

  "Waiting for SSH to become available..." repeating   BENIGN <=20 min or <=25 repeats; then WARN
  OCI pull progress (tens of GB), slow/bursty          BENIGN; WARN only if byte offset frozen >10 min
  Xcode CLT / softwareupdate / brew crawling           BENIGN (CLT alone can take 20+ min);
                                                       WARN at >15 min with ZERO new bytes
  provisioner `retry: attempt N/4`                     note at 2, WARN at 3, FATAL only if exit!=0 after 4
  single connection reset/EOF/timeout, then output     IGNORE unless the build subsequently errors
  GitHub/brew HTTP 429 / rate limit                    WARN NOW: "confirm HOMEBREW_GITHUB_API_TOKEN
                                                       reached the env" — this is the exact failure the
                                                       token exists to prevent
  keychain / "not permitted" / local-network errno 65  FATAL with the G8 pointer (keychain unlock /
                                                       Sequoia local-network workaround)
  "Build ... errored" / "no artifacts" / panic: / PID gone   FATAL immediately, last 40 lines attached
  DEADMAN, any phase not excepted above:               no new bytes 10 min = WARN;
                                                       20 min = FATAL-suspected, suggest
                                                       "check `tart list` + vnc"

REPORT FORMAT — one line, machine-scannable, via `cmux notify` AND appended to `.team/logwatch.md`:

  LOGWATCH <INFO|WARN|FATAL> t+<mm>m phase=<pull|boot|ssh-wait|provision|export|repo>
    signal="<one line>" evidence="<newest matching log line>" bytes=<offset> stale=<min>
    suggest="<ONE concrete next action for the lead>"

Healthy heartbeat INFO at least every 10 min — a silent watcher is itself a fault the lead must nudge.

REVIEWER ROLE, between build cycles: `git status --short`, `ls artifacts/`, skim board deltas and
validator findings; convert observations into ACTIONABLE intel for the lead ("same testinfra fixture
flaked twice — suggest a loan ticket to validator, not another rerun", "harness-builder's pill hasn't
moved in 15 min — probe it"). Two hard rules: the watcher NEVER restarts the build, and NEVER declares
success — it reports "build exited 0, artifact line seen" and the LEAD advances the FSM.

════════════════════════════════════════════════════════════════════════════
FAILURE HANDLING — roles are fixed; nobody negotiates during an incident
════════════════════════════════════════════════════════════════════════════

BUILD FAILS: watcher fires LOGWATCH FATAL -> lead assigns triage to ✅ validator, who reads the FULL log
file (never the screen) and classifies: (a) host issue (keychain, disk, rate limit) -> lead, may need
NEEDS-HUMAN; (b) template defect -> 📦 packer-builder (sole owner of packer/**) fixes, re-runs
`packer validate`, relaunches the same tee'd command with a FRESH timestamped log; watcher re-arms;
(c) transient -> relaunch, no fix. The barrier just stays closed; ALL shadow work continues — a build
failure costs wall time, never worker time. CIRCUIT BREAKER: max 2 relaunches; the third failure flags
the board red and opens a NEEDS-HUMAN OQ with the classified failures side by side.

WORKER STALLS (no sentinel, stale pill): lead nudges the pane; +5 min, second nudge asking for a
one-line status; still silent -> mark 🔴, move the in-flight ticket to ✅ validator (the standing
substitute) via a loan entry, and re-prompt the stuck pane with "read the board, resume". The board and
backlog are the durable state — no pane restart loses work. Check the stuck pane for a stranded composer
(text sitting above the `❯` line = a send that never got its enter).

LEAD STALLS: that is the orchestrator's job — see HEARTBEAT.

════════════════════════════════════════════════════════════════════════════
ORCHESTRATOR HEARTBEAT — you (the orchestrator) run this until DONE
════════════════════════════════════════════════════════════════════════════

The human's standing complaint: "I found myself waiting to hear back and had to prompt the orchestrator
to check on the status manually." That never happens again. After the lead is briefed:

1. ARM THE DOORBELL once:
     cmux events --name notification.created --no-heartbeat --no-ack --reconnect \
       --cursor-file "$SCRATCH/cmux.seq" > "$SCRATCH/cmux.ev" &
   Poll the FILE (`wc -l` delta + `tail`); a `| jq &` one-liner stalls on stdout buffering.

2. POLL EVERY 60s — one bounded Bash call per cycle (e.g. two 60s ticks per call), each tick checking
   ARTIFACTS: new lines in $SCRATCH/cmux.ev; `git -C "$REPO" status --short | head`; mtimes of
   .team/macos-ci-build.{board,backlog,logwatch}.md; newest packer log's byte offset; `cmux tree --all`
   pill states. Liveness = something changed since last tick. Never parse spinner text.

3. REPORT TO THE HUMAN AT LEAST EVERY 2 MINUTES — one line, even when healthy:
     [hh:mm] FSM=<state> build=<phase, t+Xm, bytes=<n>> pills=<🔵4 🟢1 🔴0> issues=<none | ...>

4. ESCALATE IMMEDIATELY — do not wait for the tick — on: any 🔴/❓ pill; any LOGWATCH WARN or FATAL; a
   NEEDS-HUMAN OQ; a build relaunch; IMAGE-READY; every GATE result. Tell the human what happened, what
   the team is doing about it, and what (if anything) you need from them.

5. THE 3-MINUTE STALL RULE: if NOTHING observable changed for 3 minutes during an active phase, probe
   the LEAD with what you saw from outside ("board mtime frozen 3 min, core-builder pill unchanged,
   composer text visible above the prompt in pane X — did a send miss its enter?"). The lead cannot see
   its workers' composers; you can. Never wait passively. EXCEPTION: during BUILD-LAUNCH/SHADOW-WORK a
   quiet minute is normal for the BUILD (the watcher covers it) — the stall rule applies to the AGENTS.

6. If the LEAD itself is unresponsive for ~3 polls: re-prompt it with "read
   .team/macos-ci-build.board.md and resume the FSM from the recorded state." Nothing depends on the
   lead's memory.

════════════════════════════════════════════════════════════════════════════
GOTCHAS — inherited from two runs; do not rediscover them
════════════════════════════════════════════════════════════════════════════

- The pre_tool_use hook blocks the substrings `rm `, `.env`, and `--rm`. Use `mv` into the scratchpad
  instead of `rm`; never type the literal `.env` token (hence no --env-file). `tart delete` is fine.
- Bash is auto-rewritten through rtk. zsh does not word-split unquoted vars — inline lists or `${=var}`.
- Lint with `uvx ruff check <file>` (ruff/ty are not on PATH). Python runs via `uv run`.
- `docs.getutm.app` 403s WebFetch — use `curl -fsSL`. Doc questions go through the search-index oracles
  in CLAUDE.md, never guessed URLs.
- Every URL you write in any doc is a real markdown link (lychee checks them, including #fragments).
  `just check` is part of the GATE — a broken link or a red claim blocks DONE.
- Honesty budget: `just unverified-count` may fall only because a claim got VERIFIED, never because a
  marker got deleted. New unverifiable assertions get `<!-- UNVERIFIED -->` + an OQ number.
- Prefer a shorter document that is entirely true over a longer one padded with plausible detail.

════════════════════════════════════════════════════════════════════════════
DONE REPORT — lead compiles, orchestrator relays to the human, in this order
════════════════════════════════════════════════════════════════════════════

  a. Golden image tag + build duration + relaunch count.
  b. Matrix verdicts, INCLUDING the recorded expected-fail asdf leg.
  c. One sample artifacts/<run-id>/verdict.json, inline.
  d. Leftover-VM check: `tart list` output pasted — no orphans.
  e. The deferred items (tokenless build leg, anything else on the board).
  f. Open questions, NEEDS-HUMAN first.
  g. The GATE output (just check + pytest), pasted.
  h. Roster table with final pill states, and the phase-boundary commit list.

Report back when the team is up with the roster (pane -> role -> surface) and the board rendered. Then
start the heartbeat and do not stop until DONE or NEEDS-HUMAN.
````

---

## After the run

```bash
cd /Users/bossjones/dev/bossjones/macos-ci
just check && uv run pytest && echo "trustworthy"
tart list        # no orphan clones
```

Read `.team/macos-ci-build.open-questions.md` first — the `NEEDS-HUMAN` entries are yours. The deferred
tokenless-build leg is on the board; run it when an hour of wall clock is cheap. The natural successor to
this prompt is a small verify-style run over whatever `<!-- UNVERIFIED -->` markers the build added.
