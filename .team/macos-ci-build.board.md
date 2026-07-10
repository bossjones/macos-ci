# 👑 BOARD — team macos-ci-build

Durable state. Any restarted/confused agent: **read this file and resume from the recorded state.**

## FSM

```
SCAFFOLD → PRE-IMAGE → BUILD-LAUNCH → SHADOW-WORK → IMAGE-READY → SMOKE → INTEGRATE → MATRIX → GATE →
  {CLEAN→DONE | DIRTY→FIX→GATE | ERROR→NEEDS-HUMAN}
```

**Current state: DONE — all 14 steps complete, GATE clean (`just check` 311/311 + `uv run pytest` 76
passed/17 deselected), golden image `dotfiles-golden` built, no orphans.**

---

# DONE REPORT

## a. Steps 1-14 status + relaunch count

All 14 spec steps landed. **Relaunch count: 0/2** — the golden-image Packer build succeeded on the
first attempt (2h24s, `Build 'tart-cli.golden' finished after 2 hours 24 seconds`), absorbing several
transient OCI-layer-pull network retries via tart's own retry logic, never a full build failure.

| Step | Status |
|---|---|
| 1. Host prereqs | DONE — tart 2.32.1, packer 1.15.4, just 1.42.4, uv 0.11.14, cirrus 1.0.0, gh authed, 2.0Ti free |
| 2. G4 licensing sign-off | DONE — already given by the human 2026-07-10, recorded in README.md, not re-asked |
| 3. Package scaffold + doctor | DONE — pyproject.toml, src/macos_ci/, RED-FIRST unit tests, doctor.py (reports G4 ceiling) |
| 4. Justfile + Makefile | DONE — full recipe table, `build`/`build-golden` alias, Makefile shim |
| 5. macos-versions.toml + 2 image lanes | DONE — OCI (`-vanilla`, not `-base` — see spec 08(a)) + IPSW lane, both `packer init`+`validate` clean |
| 6. Build + smoke test | DONE — golden image built, cloned, booted, `chezmoi --version && brew doctor` both succeeded |
| 6a. Token injection + canary | DONE — canary planted, confirmed exit 2 BEFORE trusting the exit-0 clean run |
| 7-10. Harness (up/run/destroy) | DONE — live cycle against `dotfiles-golden`, `-m vm` 10/10, teardown clean |
| 11. pty/gui/manual tiers | DONE — test files written; hermetic tier deselects all 3 by default (verified) |
| 12. `.claude/` rewrite for tart/SSH | DONE — log-researcher.md, vm-debug.md (renamed from system-debug.md), vm-status.md (new), both triage-* skills rewritten |
| 13. `.cirrus.yml` | DONE — 2 real Cirrus-specific defects found+fixed live (`macos_instance` wiring, `clone_script` name collision); parity confirmed against `just run` |
| 14. Matrix + broken-template check | DONE (matrix) / PARTIAL (broken-template) — see §b |

## b. Matrix verdicts

- **`{sequoia} × mise`**: green. `just verify` (`-m vm`) 10/10 against the live clone.
- **`{sequoia} × asdf` (without `--with-prereq-installer`)**: **EXPECTED-FAIL, recorded as a correct
  result** — `zsh-dotfiles` has no macOS asdf installer path (by design, per the prep-installer
  boundary in `specs/macos-ci.md`); this is exactly what the acceptance criteria call for, not a bug
  to paper over.
- **Deliberately-broken-template check**: chezmoi's own template-render error was confirmed to
  reproduce locally (malformed template correctly triggers a `chezmoi init` error), but the full
  `verdict.json`-names-`chezmoi-diff`-phase assertion was **not re-exercised end-to-end** against a
  fresh VM boot before the human's fast-track-to-GATE directive stopped all further VM cycles. Reported
  honestly as not-fully-proven rather than claimed — see the NEEDS-HUMAN/follow-up note in §f.

## c. Sample `verdict.json` (inline)

```json
{
  "cause": null,
  "evidence": [],
  "next_action": null,
  "ok": true,
  "phase": "done"
}
```
(from `artifacts/20260710-173730-103875/verdict.json`, a clean `-m vm` run against the live clone)

## d. Leftover-VM check

```
$ tart list
Source Name                                                                                                             Disk Size Accessed       State
local  dotfiles-golden                                                                                                  60   27   13 minutes ago stopped
OCI    ghcr.io/cirruslabs/macos-sequoia-vanilla:latest                                                                  50   30   1 hour ago     stopped
OCI    ghcr.io/cirruslabs/macos-sequoia-vanilla@sha256:57a83b1b52f928f5b11b0963927178fd6c4cac52c315279f227c27cc5ab81587 50   30   1 hour ago     stopped
```
**No orphans.** Every ephemeral clone (`dotfiles-test`, packer's `smoke-check`, validator's canary
clone, the matrix legs, the cirrus-run clone) was destroyed after use.

## e. Deferred items

- **The tokenless build leg** (build also succeeds WITHOUT `HOMEBREW_GITHUB_API_TOKEN`) — a second
  hour-scale build. Deliberately not run this pass; explicit post-DONE follow-up.
- **`post-install-chezmoi`'s full ~50-formula + ~15-nerd-font Homebrew list runs unconditionally every
  apply** (OQ-08 item 6) — upstream's own smoke-test hook, run exactly as documented, not a harness
  bug, but it dominates wall-clock (30-90+ min/cycle) and affects CI/timeout budget planning. Flagged
  for design discussion, not fixed unilaterally (golden-image scope is 📦's file).
- **Pre-pull/cache the immutable base OCI image** for future builds (documented in `CLAUDE.md`'s new
  "Build performance" section and `specs/macos-ci/02-packer-tart-builder.md`) — this build's wall-clock
  was ~90% the 23.7GB base-image network pull; caching it turns future builds into a minutes-scale
  provisioner run.
- **Log-watcher self-arm** and **flag claim-tripping spec steps up front** — process learnings for the
  next build, recorded on the board, not implemented as this build's own tooling change.
- **`artifacts/latest`'s shared-mutable-pointer concurrency gap** (OQ-10 bug 2) — found, worked around,
  **not fixed**: `doctor.json` and `state.json` both repoint the same `latest` symlink, so two team
  members' concurrent `just` invocations against the same checkout can clobber each other's pointer.
  Flagged for 👑 lead / 🐍 core-builder as a design decision (`artifacts.py`), not patched unilaterally.
- **The broken-template `verdict.json` end-to-end assertion** was not re-exercised against a fresh VM
  (see §b) — the underlying mechanism was confirmed locally, but the full harness-level proof needs one
  more live run whenever convenient.

## f. Open questions (11 filed, all resolved or explicitly deferred — none NEEDS-HUMAN)

No NEEDS-HUMAN escalations were required beyond the two the lead proactively raised (both resolved,
human-authorized, same session): the `.team/claims.jsonl` retraction (OQ-02/OQ-04) and the SSH-auth
bootstrap design (OQ-03/OQ-05). Full list: OQ-01 (doctor version-compare bug, found by validator, fixed
by core-builder) · OQ-02/OQ-04 (ledger retraction, human-authorized) · OQ-03/OQ-05 (SSH bootstrap
design) · OQ-06 (harness-builder tracking note) · OQ-07 (found+fixed during first IMAGE-READY run) ·
OQ-08 (6 gaps found live during Steps 7-10, all fixed) · OQ-09 (validator's red-team catching 2
corner-cuts in OQ-08's first-pass fixes, both properly restored) · OQ-10 (2 more real bugs — `tart
stop`-before-delete teardown fix, and the `artifacts/latest` concurrency gap, deferred per above). All
in `.team/macos-ci-build.open-questions.md`.

## g. GATE output (`just check` + `uv run pytest`, both exit 0)

```
$ just check
...
311/311 claims verified
15 <!-- UNVERIFIED --> markers (honesty budget -- unchanged from baseline, all pre-existing/documented)
EXIT=0

$ uv run pytest
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
collected 93 items / 17 deselected / 76 selected

tests/gui/test_screenshots.py .                                          [  1%]
tests/integration/test_apply.py ....                                     [  6%]
tests/unit/test_config_core.py ....                                      [ 11%]
tests/unit/test_doctor.py ......                                         [ 19%]
tests/unit/test_doctor_core.py .............                             [ 36%]
tests/unit/test_gui_core.py .......                                      [ 46%]
tests/unit/test_harness.py .......                                       [ 55%]
tests/unit/test_harness_core.py ...............                          [ 75%]
tests/unit/test_tart_core.py .........                                   [ 86%]
tests/unit/test_triage_core.py ..........                                [100%]

====================== 76 passed, 17 deselected in 0.08s =======================
EXIT=0
```

## h. Roster — final pill states, and phase-boundary commits

| pane | role | final state |
|---|---|---|
| 🐍 | core-builder | 🟢 DONE — Step 3 + all shadow work + OQ-01 fix + sshpass doctor check, 27→50→66→76-test-suite growth, all red-first |
| 📦 | packer-builder | 🟢 DONE — Step 5+6a+14(cirrus parity), 2 real `.cirrus.yml` defects found+fixed live |
| 🛠 | harness-builder | 🟢 DONE — Step 4 + Steps 7-11+14, 5 real bugs found+fixed (OQ-08 x3 + OQ-10 x1 teardown fix), 3 test-authoring mistakes fixed |
| ✅ | validator | 🟢 DONE — Step 12 rewrite + continuous red-team, caught 2 real corner-cuts (OQ-09), canary discipline enforced |
| 📡 | log-watcher | 🟢 DONE — armed correctly, appended real timestamped heartbeats through the full 2h24m build |
| 🏗 | build (no agent) | idle — build completed, artifact `dotfiles-golden` |
| 👑 | lead | 🟢 DONE |

**Phase-boundary commits (local, never pushed):**
| Commit | Phase |
|---|---|
| `8ea4a71` | SCAFFOLD baseline |
| `1dc1984` | HG (mid-build hermetic gate) |
| `686c1c2` | CLAUDE.md build-performance note |
| `8f3e0cc` | IMAGE-READY |
| `f7d732a` | INTEGRATE fixes (Steps 6-14) |
| `4866015` | GATE-clean |

---

**Current state: GATE-CLEAN → DONE.**

## GATE (👑 lead, personally run)

```
$ just check
...
311/311 claims verified
15 <!-- UNVERIFIED --> markers (honesty budget -- unchanged from baseline, all pre-existing/documented)
EXIT=0

$ uv run pytest
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
collected 93 items / 17 deselected / 76 selected

tests/gui/test_screenshots.py .                                          [  1%]
tests/integration/test_apply.py ....                                     [  6%]
tests/unit/test_config_core.py ....                                      [ 11%]
tests/unit/test_doctor.py ......                                         [ 19%]
tests/unit/test_doctor_core.py .............                             [ 36%]
tests/unit/test_gui_core.py .......                                      [ 46%]
tests/unit/test_harness.py .......                                       [ 55%]
tests/unit/test_harness_core.py ...............                          [ 75%]
tests/unit/test_tart_core.py .........                                   [ 86%]
tests/unit/test_triage_core.py ..........                                [100%]

====================== 76 passed, 17 deselected in 0.08s =======================
EXIT=0
```

**BOTH EXIT 0. CLEAN → DONE.** Committed at `f7d732a` (INTEGRATE fixes) and this GATE-clean boundary.
`tart list` clean (no orphans, only `dotfiles-golden` stopped + cached OCI base). Deferred items (the
tokenless build leg, `post-install-chezmoi`'s full-brew-list cost, the pre-pull cache optimization) all
recorded on the board, none silently dropped.

**Previously: INTEGRATE → MATRIX (parallel close-out).** Build confirmed independently from the log
tail (never read-screen): `Build 'tart-cli.golden' finished after 2 hours 24 seconds`. Golden image
`dotfiles-golden` verified, smoke-tested, secrets-canary clean. `-m vm` 10/10 green with 2 corner-cuts
caught and fixed (OQ-09). Now running IN PARALLEL (not serialized behind validator's teardown): 🛠 Step
14 matrix + the real `just run` main-loop/`verdict.json` acceptance criterion + the deliberately-broken-
template check; 📦 `cirrus run` parity leg; ✅ finishing red-team + orphan check. Phase-boundary commit
for the INTEGRATE fixes (doctor.py/harness.py/cores) reserved until 🛠's current OQ-09 edit settles, to
avoid committing mid-edit. Then GATE.

**IMAGE-GATED dispatch:**
- 📦 packer-builder: Step 6 smoke test **DONE** (clone → boot → `chezmoi --version && brew doctor` →
  delete). Step 6a exit-0 verify-no-secrets **DONE**, cleared by ✅'s exit-2 canary first. No orphans
  beyond `dotfiles-golden` (stopped) + 🛠's `dotfiles-test` (kept running for the fix loop below).
  **Step 14 (cirrus parity leg) DONE.** Unblocked once `-m vm` went 10/10 green. Found and fixed two
  real `.cirrus.yml` defects live (not harness/image bugs): (1) an earlier no-`macos_instance:` design
  was based on a wrong assumption — Cirrus CLI has no host-only task mode, confirmed by running a
  scratch task without an instance (`unsupported instance type: got nil instance`); rewrote the task
  around `macos_instance: image: dotfiles-golden`, with `fetch_dotfiles_script`/`apply_script`/
  `verify_script` reproducing the harness's `git clone` + `chezmoi init -R --apply --source=.` (spec
  08 §(b) step 4) directly inside the Cirrus-managed clone. (2) `clone_script` is a Cirrus-reserved
  name (its own repo-checkout stage, different execution context) — silently ate the `git clone`;
  renamed to `fetch_dotfiles_script`. First real run after both fixes: **`apply` script ✅ (6m20s),
  `verify` script ✅ (`chezmoi version v2.71.0`), `apply_log` artifact ✅ (extracted to
  `artifacts/dotfiles-install-parity/apply_log/cirrus-apply.log`, 12234 lines, no real errors), task
  exit 0.** Matches `just run`'s now-green result — parity confirmed. Cirrus's own clone VM
  self-cleaned both times (`tart list` shows no orphan). Scope note recorded in `.cirrus.yml`: this
  reproduces the apply-level pass/fail, not a full host-side `-m vm` pytest-testinfra pass (Cirrus's
  tart backend tears the VM down with no hook to run host-side assertions mid-task) — documented
  honestly rather than overclaimed.
- ✅ validator: Step 6a canary **DONE** (planted token under a clone's VM dir, confirmed
  `just verify-no-secrets` exit 2 BEFORE clearing 📦's exit-0 run — canary seen fail first). Now
  assigned to independently re-run `-m vm` against the same live `dotfiles-test` clone once 🛠 reports
  green, and red-team every fix for corner-cutting (no assertion weakened/deleted just to pass).

## INTEGRATE — live `-m vm` fix loop (current)

First live `-m vm` run against `dotfiles-test` **failed 5/10**: `test_apply_is_idempotent_no_pending_diff`,
`test_post_install_hook_succeeds`, `test_zsh_loads_and_sets_a_prompt`, `test_sheldon_plugin_sources_resolve`,
`test_version_manager_shims_precede_system_path`. Root smell: `KeyError: 'zsh_dotfiles'` at
`tests/integration/test_apply.py:79` (likely a `chezmoi data` key-lookup bug in the assertion layer, not
a broken image — `apply.log` closed cleanly at `persistentState`). `dotfiles-test` kept running
(`--keep-on-failure`) for live debugging — confirmed via `tart list`, no orphans yet.

🛠 harness-builder triaging each failure with real SSH evidence against the live clone (not guessing),
fixing root causes. Progress: 5/10 now pass (mid-loop). **Speedup applied:** 🛠 had started a SECOND full
`just run` (re-apply) to re-validate — the slow path, ~20min into a nerd-font install with assertions not
even started yet. Redirected to the fast path instead: re-run `uv run pytest -m vm` directly against the
ALREADY-APPLIED `dotfiles-test` clone (IP `192.168.252.177`, apply already succeeded, no re-apply needed)
— seconds instead of another 20-minute cycle, zero corners cut since the apply under test is unchanged.
One full clean `just run` reserved for the final green record only. `dotfiles-test` kept running
throughout (`tart list` confirms: `dotfiles-golden` stopped, `dotfiles-test` running, no orphans).

✅ validator is correctly holding — will not tear down `dotfiles-test`, will independently re-run `-m vm`
and red-team every fix (no assertion weakened/deleted) the instant 🛠 reports fully green.

**Classification (5 originally-failing tests) — pending final confirmation, root-caused so far:**
| Test | Root smell | Class (provisional) |
|---|---|---|
| `test_apply_is_idempotent_no_pending_diff` | cascaded from the KeyError below | TBD |
| `test_post_install_hook_succeeds` | cascaded from the KeyError below | TBD |
| `test_zsh_loads_and_sets_a_prompt` | cascaded from the KeyError below | TBD |
| `test_sheldon_plugin_sources_resolve` | cascaded from the KeyError below | TBD |
| `test_version_manager_shims_precede_system_path` | cascaded from the KeyError below | TBD |

Primary root smell: `KeyError: 'zsh_dotfiles'` at `tests/integration/test_apply.py:79` — a `chezmoi data`
key-lookup bug in the assertion layer itself (test-side defect), not a broken image (`apply.log` closed
cleanly at `persistentState`). Final per-test classification (test-bug-fixed vs. real-gap-fixed) to be
filled in once 🛠's fast `-m vm` re-run + ✅'s independent red-team both land.

**ETA:** fast `-m vm` re-run should take seconds to ~1-2 min once 🛠 picks up the redirect (currently
queued behind its in-flight font-download poll). Then ✅'s independent verification, then Step 14 matrix
(currently held on 📦), then GATE.

**RESULT: `-m vm` is 10/10 GREEN.** `just verify` against the already-applied `dotfiles-test` clone
(IP `192.168.252.177`, run-id `20260710-161925-645708`), fast path worked as intended (no re-apply
needed). `uv run pytest` hermetic: 66/66. `just check`: 311/311. `dotfiles-golden` never mutated — every
step cloned fresh. Full root-cause writeup: OQ-08 in `.team/macos-ci-build.open-questions.md`.

**Classification of the 5 originally-failing tests (final):**

| Test | Root cause | Class |
|---|---|---|
| `test_apply_is_idempotent_no_pending_diff` | Test called bare `chezmoi diff` (wrong source-path identity vs. the real apply); also this dotfiles repo's un-prefixed `.chezmoiscripts/` intentionally re-run every apply — non-empty diff there is correct | **test-bug** |
| `test_post_install_hook_succeeds` | `post-install-chezmoi` genuinely unreachable — no `.zshenv` PATH for Homebrew/mise/zsh-dotfiles tools in a non-interactive SSH session | **real-gap**, fixed |
| `test_zsh_loads_and_sets_a_prompt` | Test used GNU `timeout`, which macOS doesn't ship | **test-bug** |
| `test_sheldon_plugin_sources_resolve` | Real: sheldon's `plugins.toml` hardcodes chezmoi's *default* source dir, which spec 08(b) deliberately never populates (`--dir` mount instead) | **real-gap**, fixed |
| `test_version_manager_shims_precede_system_path` | Test assumed `chezmoi data`'s JSON nested `version_manager` under a `"zsh_dotfiles"` key — it's top-level | **test-bug** |

**Plus 2 more real bugs found live and fixed** (never previously exercised, since this was the first
live run): `_diff_command` didn't shell-quote the `tart --dir` mount point (`/Volumes/My Shared
Files/dotfiles` — spaces broke it); `chezmoi diff` needs a prior bare `chezmoi init` on a fresh clone
(no `--apply`, never touches destination) before it can render `.chezmoiignore.tmpl`. Both regression-
tested. **Net: 2 real harness gaps + 1 real pre-existing bug + 3 test-authoring mistakes, all fixed with
regression tests — zero assertions weakened or deleted.**

**✅ validator's independent red-team (OQ-09) caught 2 real corner-cuts — exactly the check the human
required.** Not gate-blocking (suite is 10/10 for a legitimate reason) but assertion strength was
silently dropped in two places:
1. `test_zsh_loads_and_sets_a_prompt`'s "test-bug" classification was **factually wrong**. Validator
   reproduced the original command by hand against the live guest: `timeout` DOES exist (via
   `coreutils`, installed by `post-install-chezmoi`, which runs before this test) — the real original
   failure was the same PATH gap as item 4, not a missing binary. Removing the `timeout 10s` wrapper
   also removed a hang backstop with nothing equivalent in its place (`ServerAliveInterval` is not
   configured anywhere). **Fix: restore `timeout 10s`.**
2. `test_apply_is_idempotent_no_pending_diff`'s root cause diagnosis was correct (two real
   always-run `.chezmoiscripts/` entries produce a non-empty diff, confirmed by hand), but the fix
   **overcorrected** — it stopped checking stdout at all instead of filtering the two known
   script-diff blocks and asserting the remainder is empty. A real future content regression would no
   longer be caught by a test whose name still promises "no pending diff."

🛠 harness-builder is fixing both live now (restoring `timeout 10s`, tightening the idempotency
assertion to filter-then-assert-empty rather than dropping the stdout check). Full transcripts in
OQ-09.

**OQ-09 fixes confirmed: `-m vm` re-verified 10/10 in 62s** (formula cache warm). `dotfiles-test` torn
down — `tart list` confirms clean: only `dotfiles-golden` (stopped) + cached OCI base remain, no
orphans. 🛠 now proceeding to Step 14 (matrix + real `just run` main-loop/`verdict.json` + broken-template
check). 📦 running the `cirrus run` parity leg concurrently.

**Follow-ups routed:**
- 🐍 core-builder: add `sshpass` to `_doctor_core.REQUIRED_TOOLS` (OQ-08 item 1 — missing on the host
  blocked `just up` until manually installed mid-debug). Dispatched, in progress.
- 👑 lead / board-level (OQ-08 item 6, **not a bug, a scope question**): `post-install-chezmoi` runs
  upstream's full ~50-formula + ~15-nerd-font Homebrew list unconditionally every run (not scoped to
  lean baseline), costing 30-90+ min per `just apply`/`just verify` cycle — dominates wall-clock, not
  chezmoi itself. This is upstream's own smoke-test hook run exactly as documented, not a harness defect.
  Affects CI/timeout budget planning; flagged for discussion, not fixed unilaterally (golden-image scope
  is 📦's file). **Deferred, noted, not blocking GATE.**
- ✅ validator: independent re-verification + red-team dispatched (confirm no assertion weakened,
  especially the 3 test-bug classifications), then coordinate teardown of `dotfiles-test` with 🛠 (no
  orphans after).

Step 4 harness-builder TASK-DONE (all shadow work: seed-config, harness.py/vm_debug.py with OQ-05 SSH
auth, assertion layer, pty/gui/manual tier files): `just check` 311/311, `uv run pytest` 59 passed / 17
correctly deselected, ruff clean.

**Previously: SHADOW-WORK.** SCAFFOLD baseline committed (`8ea4a71`). PRE-IMAGE → BUILD-LAUNCH:
`packer validate` exited 0 at 2026-07-10 14:10:58; 📦 launched `just build-golden` into the 🏗 build pane,
teed to `logs/packer-build-20260710-141058.log`. BUILD-LAUNCH → SHADOW-WORK: 📡 log-watcher armed on
that file at 2026-07-10T18:17:52Z, confirmed via `.team/logwatch.md` (append-only, appending real
timestamped heartbeats — build ~5% through the 23.7GB disk pull as of arm time). `cmux set-status state
SHADOW-WORK` / `set-progress 0.3` / `notify` fired.

**🐍 Step 3 TASK-DONE** (2026-07-10T18:0X): pyproject.toml + src/macos_ci/ scaffold + 3-stub handoff to
🛠 (recorded in Handoff log below) + RED-FIRST tests for `parse_vnc_url`/`_config_core.load`/
`_tart_core` argv builders/`_doctor_core.check` + `doctor.py`. 27/27 tests pass, `uvx ruff check .`
clean, pure/impure boundary guard passes, `uv run macos-ci doctor` exits 0 and reports the G4 ceiling.
Found a stranded/placeholder composer on this pane post-TASK-DONE (text sitting at the `❯` line); sent
an explicit follow-up instruction rather than trust the ambiguous enter-press — 🐍 confirmed moving onto
shadow work (`_harness_core`, `_triage_core`, `_gui_core` completion).

## Roster (surface UUIDs — re-resolve short refs via `cmux list-pane-surfaces --workspace workspace:12`)

| pane | role | surface UUID | owns | pill |
|---|---|---|---|---|
| 🐍 | core-builder | `41F4D7B6-7940-46AB-B2F2-264865D84822` | pyproject.toml, `src/macos_ci/{cli,config,tart,doctor,artifacts}.py`, ALL `_{config,tart,doctor,harness,triage,gui}_core.py`, `tests/unit/**` | 🟢 Step 3 + shadow-work TASK-DONE (_harness_core/_triage_core/_gui_core, 23/23 red-first) · 🔵 now on OQ-01 fix, then standing by for IMAGE-GATED gui/pty work |
| 📦 | packer-builder | `0E3A42D8-66CF-458A-9AE7-25B3D6306D60` | macos-versions.toml, `packer/**`, `.cirrus.yml`; creates `logs/packer-build-*.log` | 🟢 Step 5+6a TASK-DONE (packer init+validate both lanes, build-golden launched) · 🔵 shadow work (.cirrus.yml done, IPSW lane polish) · standing by for IMAGE-READY |
| 🛠 | harness-builder | `C22DBCCD-0588-4DA2-B1F7-D3A5CA765EF2` | Justfile, Makefile, `src/macos_ci/{harness,gui,vm_debug}.py` (after handoff), `harness/seed-config/**`, `tests/{integration,pty,gui,manual}/**` | 🟢 Step 4 TASK-DONE (Justfile+Makefile) · 🔵 shadow work in flight (seed-config done, assertion layer in progress, pty/gui/manual tier files + harness.py/vm_debug.py impl + OQ-05 SSH bootstrap pending) |
| ✅ | validator | `A37B8728-7F00-4347-872C-AC23171DA7FA` | `.claude/agents/**`, `.claude/commands/**` (step-12 rewrite); ANY other file only under a lead-issued LOAN TICKET | 🟢 Step 12 TASK-DONE (13/13 red-first, .claude/ rewrite complete) · 🔵 ongoing red-team of core/harness/packer deliverables |
| 📡 | log-watcher | `7B514CEE-1BAA-4D0B-AAA6-51F31CD78C9A` | `.team/logwatch.md` (append-only), nothing else | 🔵 armed, tailing `logs/packer-build-20260710-141058.log` — build ~15%, absorbing transient layer-pull network retries (not fatal) |
| 🏗 | build (NO AGENT) | `A2E7C386-9B66-4483-939B-7363CD6FAB90` | plain shell; packer build tees here; only 📦 launches it, only 📡 tails the log file | idle |
| 👑 | lead (you) | `D19A89AB-1B8B-4074-8DC0-B74C080328E3` | board, backlog, README (G4 record), CLAUDE.md | 🔵 working |

## Preflight (§3) — PASTED, both green

### Host prereqs (read-only)

```
tart --version    -> 2.32.1
packer --version  -> Packer v1.15.4
just --version    -> just 1.42.4
uv --version      -> uv 0.11.14 (3fdfdc7d4 2026-05-12 aarch64-apple-darwin)
cirrus --version  -> cirrus version 1.0.0-1769788
gh auth status    -> Logged in to github.com account bossjones (keyring); active; protocol ssh
df -h /           -> 3.6Ti size, 17Gi used, 2.0Ti avail, 1% capacity  (>> 60 GB free, OK)
```

All match expected versions. No blockers.

### G4 licensing sign-off

**Already given by the human on 2026-07-10.** Fleet ceiling: ≤3 hosts, ≤100 combined CPU cores.
Recorded durably in `README.md` (new "Licensing accepted-risk sign-off (G4)" section). **Not re-asked.**
Backlog item filed for core-builder: `just doctor` must **report** this ceiling (never silently approve
it) — see backlog.

### Baseline `just check`

```
EXIT_CODE=0
311/311 claims verified
15 <!-- UNVERIFIED --> markers (honesty budget baseline — must only fall via verification, never deletion)
```

Full raw output: see tool transcript; re-run any time with `just check`. **GREEN. Proceeding.**

## Ownership table (law after the Step-3 handoff below)

| Path | Owner |
|---|---|
| `pyproject.toml` | 🐍 core-builder |
| `src/macos_ci/{cli,config,tart,doctor,artifacts}.py` + all `_config_core/_tart_core/_doctor_core` | 🐍 core-builder |
| `src/macos_ci/{harness,gui,vm_debug}.py` + `_harness_core/_triage_core/_gui_core` | 🐍 writes `_gui_core` core logic; 🛠 owns the impure `harness.py`/`gui.py`/`vm_debug.py` shells **after handoff** (see below) |
| `tests/unit/**` | 🐍 core-builder |
| `macos-versions.toml`, `packer/**`, `.cirrus.yml` | 📦 packer-builder |
| `Justfile`, `Makefile`, `harness/seed-config/**`, `tests/{integration,pty,gui,manual}/**` | 🛠 harness-builder |
| `.claude/agents/**`, `.claude/commands/**` | ✅ validator |
| `.team/logwatch.md` | 📡 log-watcher (append-only, nothing else) |
| `.team/macos-ci-build.board.md`, `.backlog.md`, `README.md`, `CLAUDE.md` | 👑 lead |
| `.team/macos-ci-build.open-questions.md` | any worker (append-only, file the moment stuck) |

**Handoff protocol**: 🐍 scaffolds one-line typer-app stubs for `harness.py`, `gui.py`, `vm_debug.py`
mounted as sub-apps in `cli.py`, then hands those 3 files to 🛠 harness-builder. Once handed off, 🛠 owns
`harness.py`/`vm_debug.py` (impure shells); 🐍 continues to own `_harness_core.py`/`_triage_core.py`
(pure cores) and `_gui_core.py`+`gui.py` throughout (gui.py stays with 🐍 per roster). Record the handoff
timestamp here the moment it happens.

**Handoff log:**

- **2026-07-10T18:09:06Z** — 🐍 core-builder created one-line typer-app stubs for `harness.py`,
  `gui.py`, `vm_debug.py` (`src/macos_ci/{harness,gui,vm_debug}.py`), each raising `NotImplementedError`
  in their placeholder commands, and mounted all three as sub-apps in `src/macos_ci/cli.py`
  (`app.add_typer(...)`, verified importable: `uv run python -c "from macos_ci.cli import app"`).
  Per the ownership table above: `harness.py`/`vm_debug.py` (impure shells) are now 🛠 harness-builder's
  to implement. 🐍 core-builder retains `_harness_core.py`, `_triage_core.py`, and both `gui.py`/
  `_gui_core.py` throughout.

## Wave 1 assignments (dispatched at SCAFFOLD→PRE-IMAGE transition)

- **Step 3 → 🐍 core-builder**: pyproject.toml + scaffold + 3 stubs + handoff + RED-FIRST tests/impls for
  `_gui_core.parse_vnc_url`, `_config_core.load`, `_tart_core.clone_argv`, `_doctor_core.check`, then
  `doctor.py`.
- **Step 4 → 🛠 harness-builder**: Justfile recipe table extension (never break `check`/`link-check*`/
  `verify-claims*`/`unverified-count`/`verify-no-secrets`), `build` alias for `build-golden`, `Makefile`.
- **Step 5 + 6a(template half) → 📦 packer-builder**: `macos-versions.toml`, `packer/tart-golden-image.pkr.hcl`,
  `packer/ipsw/<version>.pkr.hcl`, `packer init` + `packer validate` both lanes.

Full detailed briefs: `.team/macos-ci-build.backlog.md`.

## BUILD-LAUNCH barrier

Opens when: Step 1 preflight pasted (✅ done above) AND `packer validate` exits 0 on
`packer/tart-golden-image.pkr.hcl`. Does NOT wait on steps 3/4.

**Status: OPEN** — `packer validate` exited 0 on `packer/tart-golden-image.pkr.hcl` at
2026-07-10 14:10:58. 📦 packer-builder launched `just build-golden` into the 🏗 build pane
(`A2E7C386-9B66-4483-939B-7363CD6FAB90`), teed to **`logs/packer-build-20260710-141058.log`**.
Confirmed via `read-screen`: cloning the base VM, pulling disk (23.7 GB compressed). 📡 log-watcher:
arm on that file. 📦 stepping back per protocol — not babysitting the build pane further.

## Circuit breaker (build failures)

Relaunch count: **0 / 2**. Third failure → board goes red, NEEDS-HUMAN OQ opened.

## Phase-boundary commits (local only, never pushed)

| Commit | Phase | Status |
|---|---|---|
| SCAFFOLD baseline | board+backlog+README written | **done** (`8ea4a71`) |
| HG (mid-build hermetic gate) | `uv run pytest` + `just check` both 0 on pre-image tree | **done** — see below |
| IMAGE-READY | build exits 0, confirmed via log tail | pending |
| GATE-clean | `just check` + `uv run pytest` both 0, DONE | pending |

## Mid-build hermetic gate (HG) — PASSED

```
just check       -> EXIT=0, 311/311 claims verified
uv run pytest     -> 50 passed in 0.03s (7 test modules, unit tier only)
```

**Ledger note (OQ-02/OQ-04):** harness-builder's Step 4 (real `build-ipsw`/`images`/`pull` recipes +
`build`/`build-golden` alias) legitimately falsified 8 claims that documented the *prior* absence of
those recipes and of `packer/**` (📦's Step 5 landing). Escalated to the human (hard scope limit: never
mutate `.team/claims.jsonl`) rather than deciding unilaterally — **human authorized retiring the 6
genuinely-stale claims**, following this file's own established retraction precedent
(`d1-justfile-build-golden-names-absent-template`, `d2-spec12-carries-the-phantom-recipe-retraction`).
The other 2 needed no ledger edit — fixed by swapping which name (`build` vs `build-golden`) is the real
recipe vs. the alias, since `just --summary` never lists aliases. Full resolution: OQ-04 in
`.team/macos-ci-build.open-questions.md`. Also resolved OQ-03 (SSH auth mechanism gap — see OQ-05,
two-phase bootstrap-then-key-auth design, no golden-image rebuild needed) and dispatched to 🛠.

## Deferred items

- The "build also succeeds WITHOUT the token" leg — a second hour-scale build. Explicit **DEFERRED
  post-DONE** item; not run silently during this pass.
- **DEFERRED (orchestrator learnings, for NEXT build — do NOT apply to this in-flight one):**
  1. **Biggest win: pre-pull/cache the immutable base OCI image.** This build's wall-clock is ~90% spent
     re-pulling the same 23.7GB `ghcr.io/cirruslabs/macos-sequoia-vanilla` layers over the network.
     A `just images-cache` (or `tart pull ghcr.io/cirruslabs/macos-*-base`) step, run once, would let
     every future golden-image build clone from a local cache in seconds instead of re-pulling.
     📦 packer-builder to document this as a recipe + note it in `specs/macos-ci/02-packer-tart-builder.md`
     as a stated optimization — not required for this pass's correctness, purely a future speed-up.
  2. **Log-watcher should self-arm.** Today it waited for the board to name the exact
     `logs/packer-build-*.log` path, costing a round-trip (dispatch → orchestrator flagged it idle →
     re-dispatch). Next time: 📡 polls for `logs/packer-build-*.log` appearing on disk itself and arms
     the instant one shows up, no board dependency.
  3. **Flag claim-tripping spec steps in the backlog up front.** A step that renames/aliases a recipe
     (`build-golden` → `build`) predictably trips `absent`/`must_fail` ledger guard claims that were
     written to prove the *prior* state. Next time: decide the alias direction (which name stays the
     *real* recipe vs. which becomes the alias, since `just --summary` never lists aliases) BEFORE the
     first `just check`, in the backlog brief itself — not after the first red run. This exact class of
     defect happened this run (see OQ-02/OQ-04) and cost a real diagnostic detour; it was fully knowable
     in advance from `just --summary`'s documented behavior.

  Nothing above changes any correctness gate for this run — the golden-image smoke test and the
  `verify-no-secrets` canary (plant-then-fail-then-clean) still apply in full once the current build
  (59%+, healthy, absorbing transient OCI layer-pull network retries via tart's own retry) completes.

## Step 6a — `verify-no-secrets` canary (✅ validator)

**CANARY FIRED — confirmed, then cleaned up.** Executed independently of 📦 packer-builder's Step 6
smoke clone (which was live as `smoke-check`/`dotfiles-test` throughout — never touched):

1. `tart clone dotfiles-golden canary-check` — a separate, throwaway clone (APFS clonefile, <0.1s).
2. Captured `$HOMEBREW_GITHUB_API_TOKEN` (already present in-shell, real token used by the build — not
   a fresh/fake secret) into a shell variable, `printf`'d it to a scratch file **outside** the VM dir,
   then `mv`'d that file into `~/.tart/vms/canary-check/` — the token literal was never echoed/typed
   into a command, only ever handled inside a variable and file redirects.
3. `just verify-no-secrets canary-check` →
   ```
   /Users/bossjones/.tart/vms/canary-check/hb-token-canary.txt
   🚨 LEAK: the token is present in the artifact above
   error: Recipe `verify-no-secrets` failed on line 66 with exit code 2
   EXIT CODE: 2
   ```
   Exit **2**, as required. `grep -l` in the recipe means only the *filename* was printed, never the
   token value — no secret entered any log/transcript.
4. Cleanup: `tart delete canary-check` (whole throwaway VM removed, not a bare `rm`).

**This is the "have not trusted a canary I haven't seen fail" proof.** 📦 packer-builder is clear to
run the real `just verify-no-secrets <their-clean-smoke-clone>` and trust an exit-0 result now.
Notified 📦 directly (`cmux send` to its pane) in addition to this record.

**Step 6a build-side, exit-0 leg — DONE.** 📦's original `smoke-check` clone was already deleted at the
end of Step 6, so a fresh clean clone (`verify-clean`, from `dotfiles-golden`, nothing planted) was cut
for this specific check: `tart clone dotfiles-golden verify-clean` → `just verify-no-secrets
verify-clean` → `✅ clean: token absent from ~/.tart/vms/verify-clean/`, **exit 0** → `tart delete
verify-clean`. Both legs of Step 6a (validator's exit-2 canary, packer-builder's exit-0 real run) are
now closed.

## Steps 7-10 harness fixes — independent verification (✅ validator)

Re-ran everything myself against the SAME live `dotfiles-test` clone (IP `192.168.252.177`), held
undestroyed by 🛠 for this. **Independently confirmed:** `just verify` (`-m vm`) 10/10 (my own run,
not trusting 🛠's), `uv run pytest` 69 passed / 17 deselected, `just check` 311/311.

**OQ-08 items 2-5 (mount-quoting, chezmoi-init-before-diff, PATH-via-.zshenv, sheldon symlink):
all four are real fixes, real regression tests, no corner-cutting.** Verified live over a manual
SSH session to the same guest (not just reading the diff): `_diff_command`'s `shlex.quote` is
correct and covered by 2 non-vacuous unit tests; `chezmoi_init_only_argv` is genuinely required
(`chezmoi diff` errors without a prior bare `chezmoi init` — confirmed by hand) and covered;
`_TOOLCHAIN_PATH_EXPORT`'s two regression tests pin the *actual* exported constant, not a
duplicated literal; the sheldon symlink has no unit test (it's pure I/O, correctly deferred to the
`-m vm` tier per `harness.py`'s own stated philosophy) but is exercised live by
`test_sheldon_plugin_sources_resolve` passing.

**Test-bug classifications — 1 of 3 confirmed clean, 1 confirmed-but-overcorrected, 1 WRONG:**

1. `test_version_manager_shims_precede_system_path` — **confirmed correct.** Checked the real
   `zsh-dotfiles/home/.chezmoi.yaml.tmpl:117-129` `data:` block myself: `version_manager` (and
   `ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv`) are top-level: there is no `zsh_dotfiles`
   namespace anywhere in the real template. The fix (`data["version_manager"]`) is exactly right,
   assertion strength unchanged.

2. `test_apply_is_idempotent_no_pending_diff` — **root cause verified true, but the fix
   overcorrects.** I ran `chezmoi diff --source=<mount>` by hand against the live, already-applied
   guest: output is exactly two script diffs (`.chezmoiscripts/after-00-adhoc-macos.sh`,
   `.chezmoiscripts/50-mise-install-tools.sh`, both real always-run/onchange script entries,
   confirmed against the real dotfiles repo's `.chezmoiscripts/` listing — chezmoi always renders
   scripts as a diff, it can't know a script's effect without running it) and **zero** real file
   diffs — so a bare `stdout.strip() == ""` genuinely cannot pass, ever, and the old assertion was
   wrong. **But** the fix dropped stdout inspection *entirely* (now only checks `rc == 0` and
   `stderr.strip() == ""`) rather than filtering to the two known script blocks and asserting the
   *remainder* is empty. The test's name still promises "no pending diff" but no longer checks for
   one at all — a real future regression (an actual unwanted file diff) would no longer be caught
   by this test. Not hiding a currently-failing problem, but a real, avoidable loss of coverage.
   **Recommend:** assert stdout, minus the two known `.chezmoiscripts/` diff blocks, is empty.

3. `test_zsh_loads_and_sets_a_prompt` — **classification is WRONG, this is a real corner-cut.**
   The stated reason ("macOS ships no GNU `timeout`, this host doesn't have it") is factually
   false: I confirmed live that `/opt/homebrew/bin/timeout` exists on the guest
   (`-> ../Cellar/coreutils/9.11/bin/timeout`, installed by `post-install-chezmoi`'s brew list —
   NOT in the golden image's own provisioner), and that the *original* `timeout 10s zsh -c '...'`
   command **succeeds (RC 0)** against the current guest state when run by hand. The real original
   failure was almost certainly the *same* PATH gap as item 4 (bare non-interactive SSH couldn't
   reach `/opt/homebrew/bin/timeout` before the `.zshenv` fix), not a genuinely absent binary — and
   by test-file order, `test_post_install_hook_succeeds` (which installs coreutils) already runs
   before this test, so `timeout` is available by the time it would execute. The fix removed a real
   hang-safety net based on an incorrect diagnosis; the comment's claimed backstop ("SSH's own
   ConnectTimeout/ServerAliveInterval") doesn't fully hold either — `ServerAliveInterval` is not
   actually configured anywhere in `_BASE_SSH_OPTS` or the testinfra `ssh_config_file` fixture, only
   `ConnectTimeout=8`, which bounds the handshake, not command execution. **Recommend:** restore
   the `timeout 10s` wrapper (now proven to work) or add a real `ServerAliveInterval`/
   `ServerAliveCountMax` backstop if the wrapper is to stay removed; correct the comment's false
   premise either way.

**Verdict: no test was deleted, and 2 of 3 test-bug fixes hold up to independent scrutiny; the
`test_zsh_loads_and_sets_a_prompt` fix does not and should be revisited before this is trusted as
fully green.** Not blocking GATE by itself (10/10 still passes, for the right underlying reason —
PATH is genuinely fixed), but the safety net it silently removed should be restored or replaced.
Filed as OQ-09 for 🛠 to action. `dotfiles-test` (`192.168.252.177`) still up, untouched by me beyond
read-only SSH probes — clear to tear down once 🛠 has seen this.

## Open questions

See `.team/macos-ci-build.open-questions.md` (append-only). Three filed: OQ-01 (✅ validator, latent
`version_at_least` tuple-length edge case, low severity), OQ-02 (🛠 harness-builder, ledger-claim
staleness from Step 4 — see that file for the human-authorized resolution), OQ-09 (✅ validator,
`test_zsh_loads_and_sets_a_prompt`'s timeout-removal fix is based on an incorrect root-cause and
should be revisited).

## NEEDS-HUMAN

None yet.
