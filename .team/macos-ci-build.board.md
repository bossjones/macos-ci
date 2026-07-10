# 👑 BOARD — team macos-ci-build

Durable state. Any restarted/confused agent: **read this file and resume from the recorded state.**

## FSM

```
SCAFFOLD → PRE-IMAGE → BUILD-LAUNCH → SHADOW-WORK → IMAGE-READY → SMOKE → INTEGRATE → MATRIX → GATE →
  {CLEAN→DONE | DIRTY→FIX→GATE | ERROR→NEEDS-HUMAN}
```

**Current state: IMAGE-READY.** Build confirmed independently from the log tail (never read-screen):
`Build 'tart-cli.golden' finished after 2 hours 24 seconds`, `==> Builds finished. The artifacts of
successful builds are: --> tart-cli.golden: dotfiles-golden`. `tart list` confirms `dotfiles-golden`
(local, 60GB, stopped, 4 min ago) alongside the cached OCI base. chezmoi v2.71.0 installed. Moving to
IMAGE-GATED work now: Step 6 smoke (📦) → Step 6a canary (✅, plant-then-fail-then-clean) → Steps 7-10
live (🛠) → Step 11 pty/gui (🛠) → Step 14 matrix + broken-template check + cirrus parity → GATE (👑).

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

## Open questions

See `.team/macos-ci-build.open-questions.md` (append-only). None filed yet.

## NEEDS-HUMAN

None yet.
