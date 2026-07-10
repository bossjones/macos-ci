# 👑 BOARD — team macos-ci-build

Durable state. Any restarted/confused agent: **read this file and resume from the recorded state.**

## FSM

```
SCAFFOLD → PRE-IMAGE → BUILD-LAUNCH → SHADOW-WORK → IMAGE-READY → SMOKE → INTEGRATE → MATRIX → GATE →
  {CLEAN→DONE | DIRTY→FIX→GATE | ERROR→NEEDS-HUMAN}
```

**Current state: SCAFFOLD** (writing this board + backlog, about to make the SCAFFOLD-baseline commit
and dispatch Wave 1).

## Roster (surface UUIDs — re-resolve short refs via `cmux list-pane-surfaces --workspace workspace:12`)

| pane | role | surface UUID | owns | pill |
|---|---|---|---|---|
| 🐍 | core-builder | `41F4D7B6-7940-46AB-B2F2-264865D84822` | pyproject.toml, `src/macos_ci/{cli,config,tart,doctor,artifacts}.py`, ALL `_{config,tart,doctor,harness,triage,gui}_core.py`, `tests/unit/**` | 🔵 not yet dispatched |
| 📦 | packer-builder | `0E3A42D8-66CF-458A-9AE7-25B3D6306D60` | macos-versions.toml, `packer/**`, `.cirrus.yml`; creates `logs/packer-build-*.log` | 🔵 not yet dispatched |
| 🛠 | harness-builder | `C22DBCCD-0588-4DA2-B1F7-D3A5CA765EF2` | Justfile, Makefile, `src/macos_ci/{harness,gui,vm_debug}.py` (after handoff), `harness/seed-config/**`, `tests/{integration,pty,gui,manual}/**` | 🔵 not yet dispatched |
| ✅ | validator | `A37B8728-7F00-4347-872C-AC23171DA7FA` | `.claude/agents/**`, `.claude/commands/**` (step-12 rewrite); ANY other file only under a lead-issued LOAN TICKET | 🔵 not yet dispatched |
| 📡 | log-watcher | `7B514CEE-1BAA-4D0B-AAA6-51F31CD78C9A` | `.team/logwatch.md` (append-only), nothing else | 🔵 not yet dispatched |
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

**Handoff log:** _(none yet)_

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

**Status: NOT YET OPEN** (waiting on 📦 packer-builder template + validate).

## Circuit breaker (build failures)

Relaunch count: **0 / 2**. Third failure → board goes red, NEEDS-HUMAN OQ opened.

## Phase-boundary commits (local only, never pushed)

| Commit | Phase | Status |
|---|---|---|
| SCAFFOLD baseline | board+backlog+README written | pending |
| HG (mid-build hermetic gate) | `uv run pytest` + `just check` both 0 on pre-image tree | pending |
| IMAGE-READY | build exits 0, confirmed via log tail | pending |
| GATE-clean | `just check` + `uv run pytest` both 0, DONE | pending |

## Deferred items

- The "build also succeeds WITHOUT the token" leg — a second hour-scale build. Explicit **DEFERRED
  post-DONE** item; not run silently during this pass.

## Open questions

See `.team/macos-ci-build.open-questions.md` (append-only). None filed yet.

## NEEDS-HUMAN

None yet.
