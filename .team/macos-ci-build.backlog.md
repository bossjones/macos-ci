# BACKLOG — team macos-ci-build

Detailed per-role briefs. Read your role's section. The board (`.team/macos-ci-build.board.md`) is the
durable FSM state — this file is the task detail. Spec citations are `specs/macos-ci/NN-*.md` unless
otherwise noted. **Evidence > this brief** — if a test/command output contradicts a sentence here, report
the contradiction and follow the evidence.

Binding rules for everyone (full text: `.team/macos-ci-build.lead-brief.md` §1, §9):

- RED FIRST for every pure `_core` function: write the failing test, watch it fail, then implement.
- `uv run pytest` and `uvx ruff check .` stay green continuously.
- Fire `cmux notify --title "<role>" --body "<state>: <one-line>"` on every self-transition and the first
  OQ. Update your tab pill: `<emoji> <role> <n>/<N> [####------] · <one-line log>`.
- Completion sentinel, EXACT: `TASK-DONE: <role> | <one-line summary> | tests+N red-first-Y/N`.
- Never `rm ` (trailing space blocked by hook), never type `.env`, never `--rm`. Use `mv` into scratch.
- Lint with `uvx ruff check <file>` (not on PATH directly). Run Python via `uv run`.
- File `.team/macos-ci-build.open-questions.md` (append-only, `OQ-NN` blocks) the moment you're stuck.
  "presumably / likely / should be" is an OQ, not a sentence.
- Never touch `.team/claims.jsonl` or the inherited `.team/macos-ci.*` files (read-only).

---

## 🐍 core-builder

**Owns**: `pyproject.toml`, `src/macos_ci/{cli,config,tart,doctor,artifacts}.py`, ALL `_core` siblings
(`_config_core.py`, `_tart_core.py`, `_doctor_core.py`, `_harness_core.py`, `_triage_core.py`,
`_gui_core.py`), `tests/unit/**`.

### Step 3 (Wave 1, critical path for the handoff)

1. `pyproject.toml`: hatchling build backend, `[project.scripts] macos-ci = "macos_ci.cli:app"`, dev
   dependency group. New deps per spec `macos-ci.md` Notes: `pytest-testinfra asyncvnc pexpect
   pytest-json-report`. Existing-stack deps to match `zsh-dotfiles/pyproject.toml`: `pytest-sugar
   pytest-mock pytest-timeout pytest-retry pytest-subprocess pytest-skip-slow ruff basedpyright`.
   Configure `[tool.pytest.ini_options]` markers (`vm`, `pty`, `gui`, `manual`) and
   `addopts = "-ra -m 'not vm and not pty and not gui and not manual'"` (spec 12 §"the four test tiers").
2. Scaffold `src/macos_ci/` per spec 12's package layout: `cli.py` (typer entrypoint), `config.py` +
   `_config_core.py`, `tart.py` + `_tart_core.py`, `doctor.py` + `_doctor_core.py`, `artifacts.py`.
   Also create **one-line typer-app stubs** for `harness.py`, `gui.py`, `vm_debug.py` — enough to mount
   as sub-apps in `cli.py` (e.g. `app.add_typer(harness_app, name="harness")` with a stub `@harness_app.command` that just raises `NotImplementedError` or similar placeholder).
3. **HANDOFF**: the moment those 3 stub files exist and are mounted, record the handoff on the board
   (`.team/macos-ci-build.board.md`, "Handoff log" section) — after that, `harness.py` and `vm_debug.py`
   become 🛠 harness-builder's to implement (impure shells); you keep `_harness_core.py`, `_triage_core.py`
   and both `gui.py`/`_gui_core.py` per the roster ownership table.
4. RED-FIRST tests + impls, in this order:
   - `tests/unit/test_gui_core.py::test_parse_vnc_url` — the exact fixture from spec 12:
     `"Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415..."` → `VncTarget(host="127.0.0.1",
     port=59415, password="enhance-chase-volume-push")`. Watch it fail (no `parse_vnc_url` yet), then
     implement `_gui_core.py`.
   - `_config_core.load()` — pure function validating `macos-versions.toml`: unknown `source` values, an
     `ipsw` entry missing `sha256`, a `default` naming a nonexistent image. Three unit tests minimum (spec
     12 §"macos-versions.toml").
   - `_tart_core.clone_argv()` — pure argv builder for `tart clone <golden> <name>`; use
     `pytest-subprocess` to register a fake `tart` binary and assert on constructed argv, no real `tart`
     call. Also add argv builders needed downstream (`run`, `ip`, `--dir` mount) as you discover the
     shape from spec 01 — cite `01-tart-core.md` for exact flag spelling, don't guess.
   - `_doctor_core.check()` — the requirement table + version-compare + verdict logic (pure). Then
     `doctor.py`: `shutil.which` + version probes, Apple Silicon check, macOS floor, login keychain
     unlocked (G8), `$ZSH_DOTFILES` exists, free disk space, **and the G4 fleet-ceiling report** (≤3
     hosts / ≤100 cores — REPORT, never silently approve). `just doctor --json` writes
     `artifacts/<run-id>/doctor.json` and exits 2 on any miss.
5. Guard the pure/impure boundary: `uv run python -c "import macos_ci._tart_core, macos_ci._doctor_core,
   macos_ci._gui_core"` must succeed with zero I/O imports pulled in.

### Shadow work (while the packer build runs)

- `_harness_core.py` (pure): run-id generation, artifact path layout, `chezmoi_argv()` reproducing
  `zsh-dotfiles/scripts/smoke-test-docker.sh:361-365` **verbatim** (the command is quoted in full in
  spec `08-dotfiles-test-harness.md` §(b) step 4 — copy it exactly), parameterized on `version_manager`
  (default `mise`) and `--source` pointed at the `tart --dir` mount path.
- `_triage_core.py` (pure): failure-signature table + `match(log_lines) -> [Finding]`, tested against
  fixture log text (no VM). Seed signatures are in spec `12-tooling-and-agent-loop.md` §"Seed failure
  signatures" — six rows, use them verbatim as your fixture table starting point.
- `_gui_core.py` completion: beyond `parse_vnc_url`, whatever `gui.py` needs (see spec 12 §"gui" tier).

**Acceptance**: `uv run pytest` green, `uvx ruff check .` clean, doctor exits 2 on missing tool and 0 once
present (test both paths with fakes).

---

## 📦 packer-builder

**Owns**: `macos-versions.toml`, `packer/**`, `.cirrus.yml`; creates `logs/packer-build-*.log`.
**Critical path — unblock first.** The BUILD-LAUNCH barrier waits on your `packer validate` exit 0.

### Step 5 + 6a (template half), Wave 1

1. `macos-versions.toml` per spec 12's exact shape:
   ```toml
   default = "sequoia"

   [image.sequoia]
   source = "oci"
   ref    = "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest"

   [image.tahoe]
   source = "oci"
   ref    = "ghcr.io/cirruslabs/macos-tahoe-vanilla:latest"
   ```
   **Use `-vanilla`, NOT `-base`.** Spec `08-dotfiles-test-harness.md` §(a) "The base image is `-vanilla`"
   explains why: `-base` preinstalls `mise`, which short-circuits the dotfiles' own `mise` installer
   (`command -v mise || brew install mise`), silently disarming the one path the harness exists to test.
2. `packer/tart-golden-image.pkr.hcl` per the field reference in `02-packer-tart-builder.md`:
   - `vm_base_name` = the sequoia `-vanilla` ref above (OCI lane).
   - Sized for Homebrew + Xcode CLT build (cpu/memory/disk — check spec 02's sizing guidance).
   - `headless = true`.
   - `ssh_username`/`ssh_password` = `admin`/`admin` (default creds, G8) — **PLAIN, never marked
     `sensitive = true`**. Marking a common word sensitive rewrites every occurrence of it in every log
     output to `<sensitive>` (CLAUDE.md's `packer-sensitive-hides-secret` gotcha) — do not do this to
     `admin`.
   - ONE idempotent shell provisioner installing: Xcode CLT, Homebrew, chezmoi (≥ 2.20.0, per
     `zsh-dotfiles/.chezmoiversion`), and the brew prereq list from `smoke-test-docker.sh:142-143` —
     `wget curl retry go openssl@3 readline libyaml gmp autoconf tmux`. `retry` comes from the
     `kadwanev/brew` tap. **Do NOT install `zsh-dotfiles-prep`** — that's a separate, optional matrix leg.
   - Wire the Homebrew token now (one build, not two): `homebrew_github_api_token` declared
     `sensitive = true`, `default = env("HOMEBREW_GITHUB_API_TOKEN")`. Pass it through the shell
     provisioner's `environment_vars`, wrapped in `compact()` so an unset token omits the variable
     entirely, alongside the `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n` anonymous-HTTPS rewrite for the one
     `git@github.com:` tap URL in `zsh-dotfiles-prep/Brewfile` — full mechanism in
     `13-build-secrets.md`. Leave `use_env_var_file` at its default `false` — `true` writes the secret
     into a file **on the guest**, which is exactly what this design avoids.
3. `packer/ipsw/<version>.pkr.hcl`: `from_ipsw = var.ipsw_url`, Setup Assistant `boot_command`. Crib from
   `~/dev/markkenny/macos-virtualisation/Packs/vanilla-26.1.pkr.hcl` (read-only reference) but **validate
   every wait token** — that file has a typo'd `<wai7s>` token as a cautionary tale (spec 12 §"Prior art").
4. `packer init packer/tart-golden-image.pkr.hcl` then `packer validate` on **both** lanes. The moment
   `packer validate` exits 0 on the golden-image template, the BUILD-LAUNCH barrier is open (combined
   with Step 1 already being pasted — it is). **Immediately** re-resolve the 🏗 build pane's surface UUID
   from `.team/macos-ci-build.spawn.json` and launch (send + send-key enter):
   ```
   just build-golden 2>&1 | tee logs/packer-build-$(date +%Y%m%d-%H%M%S).log
   ```
   Note on the board which log file you launched. Then step back — 📡 log-watcher tails it, nobody else
   touches the build pane.

### While the build runs

- `.cirrus.yml` (step 13) per `03-tart-ci-and-orchard.md`, wrapping `just run` as a Cirrus CLI task for
  local/CI parity, with `--artifacts-dir` extraction wired.
- IPSW lane polish (finish anything left from step 5's second template).
- Do **not** babysit the build pane — that's 📡's job exclusively.

### After the build exits 0 (IMAGE-GATED — confirm exit code from the log tail, never read-screen)

- **Step 6 smoke**: `tart clone` the golden image once, boot it, `chezmoi --version && brew doctor`
  inside, then delete the clone.
- **Step 6a verify half**: after ✅ validator plants a token in a scratch file under the VM dir and
  confirms `just verify-no-secrets <vm>` exits 2 (never trust an unfailed canary), run
  `just verify-no-secrets <vm>` for real and confirm exit 0.
- **Step 14 (parity leg)**: `cirrus run` reproduces the same pass/fail as `just run`.

**Board note**: the "build also succeeds WITHOUT the token" leg is a separate hour-scale build — record
it as **DEFERRED post-DONE**, do not run it in this pass.

---

## 🛠 harness-builder

**Owns**: `Justfile`, `Makefile`, `harness/seed-config/**`, `tests/{integration,pty,gui,manual}/**`, and
(after 🐍's handoff) `src/macos_ci/{harness,gui,vm_debug}.py` — note per roster, `gui.py` stays with 🐍;
you take `harness.py` and `vm_debug.py`'s impure shells post-handoff.

### Step 4, Wave 1

Implement the recipe table from `12-tooling-and-agent-loop.md` §"Recipe reference" into the existing
`Justfile` — **EXTEND, never break** `check`, `link-check*`, `verify-claims*`, `unverified-count`,
`verify-no-secrets` — they must survive VERBATIM (run `just check` after every edit to confirm).

Recipes to add: `doctor`, `build` (the spec calls it `build`; the live Justfile has `build-golden` —
implement `build` as the real recipe and keep `build-golden` as an **alias**, since the ledger's claims
reference `build-golden` by name), `build-ipsw`, `images`, `pull`, `up`, `down`, `destroy`, `recreate`,
`run`, `apply`, `ssh`, `exec`, `logs`, `debug`, `status`, `gui`, `vnc`, `shot`, `test`,
`verify{,-pty,-gui,-manual}`, `matrix`, `lint`, `fmt`, `typecheck`, `ci`, `prune`. Every non-trivial body
delegates to `uv run macos-ci <subcommand>`. `just run` gates on `just doctor` and always writes
`verdict.json`, even on crash.

Keep `set shell := ["bash", "-uc"]`. Variable block per spec 12:
```just
vm       := env_var_or_default("MACOS_CI_VM", "dotfiles-test")
image    := env_var_or_default("MACOS_CI_IMAGE", "sequoia")
dotfiles := env_var_or_default("ZSH_DOTFILES", justfile_directory() / ".." / "zsh-dotfiles")
vm_user  := "admin"
vmgr     := env_var_or_default("MACOS_CI_VERSION_MANAGER", "mise")
ssh_opts := "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=8 -o BatchMode=yes"
```

Add the `Makefile` shim (thin passthrough, no recipe logic of its own — spec 12's exact pattern):
```make
JUST ?= just
.PHONY: up down build run logs ssh doctor test lint verify clean
up down build run logs ssh doctor test lint verify clean:
	@$(JUST) $@
%:
	@$(JUST) $@
```

`Bash(just:*)` is **already** in `.claude/settings.json`'s `permissions.allow` (confirmed by lead
preflight) — do not touch settings.json.

### Shadow work (while the build runs, all hermetic — no image needed)

- `harness.py` (impure, after handoff): compose `tart clone` → headless `tart run` → poll `tart ip` →
  `--dir` mount → SSH **no `-t`** (this is what makes chezmoi's `stdinIsATTY` resolve false — G11) →
  `chezmoi diff` (pre-apply lint, non-empty stderr fails the run *before* apply) → the exact apply
  command from `08-dotfiles-test-harness.md` §(b) step 4, wrapped in `retry -t 4`. Set
  `CM_computer_name`/`CM_hostname` to the run-id per run. **Never mutate the golden image** — every run
  clones fresh.
- Seed-config lever (step 8): write `~/.config/chezmoi/chezmoi.yaml` into the guest before `chezmoi init`
  for toggle-matrix runs (Option A, spec 08 §(b) — the seven boolean flags are unreachable via
  `--promptBool` in non-TTY, this is the only lever, G11).
- Assertion layer (step 9): `tests/integration/` as `pytest-testinfra` modules per spec 08 §(c)'s table —
  apply exit code, post-install hook, shell/prompt load, `dscl` login-shell check, `sheldon lock` (yes,
  mutating — the disposable clone makes that free, see spec 08's OQ-17 discussion), `nvim --headless
  +qa`, `tmux -V`, PATH ordering, non-fatal `brew doctor`, feature-toggle fields via `chezmoi data`.
  `conftest.py` follows `multipass-lab/clusters/*/tests/testinfra/conftest.py`'s session-scoped host
  fixture polling `host.run("true").rc == 0` to a deadline (spec 12 gives the exact fixture code).
- Teardown (step 10): `tart delete <run-id>` always, `--keep-on-failure` opt-in, `just prune` for orphans.
- pty/gui/manual tier **files** (step 11) — write the test files now (they're hermetic to write, even if
  exercising them needs a live clone later): `tests/pty/` (pexpect over `ssh -tt`), `tests/gui/`
  (`_gui_core.parse_vnc_url` + `asyncvnc`, screenshots to `artifacts/<run-id>/screenshots/`),
  `tests/manual/` (`confirm()` fixture that `pytest.skip()`s when `not sys.stdin.isatty()`). Verify a
  bare `uv run pytest` deselects all three tiers plus `vm` — make this an acceptance test.

### After the image lands (IMAGE-GATED)

- **Steps 7–10 live**: first real `just up` / `just run` / `just destroy` cycle against the built image;
  `-m vm` tier green; teardown proven (`tart list` shows no orphans).
- **Step 11**: pty/gui tiers exercised against a live clone (not just written — actually run).

---

## ✅ validator

**Owns**: `.claude/agents/**`, `.claude/commands/**` (step-12 rewrite). ANY other file only under a
lead-issued LOAN TICKET (e.g. if a worker stalls and you're substituted in — the lead records this on the
board).

### Ongoing (as steps 3–5 land)

Red-team each core-builder/harness-builder/packer-builder deliverable as it lands:
- Re-run the unit tests yourself.
- **Stub the implementation** (comment out the real logic, leave a `pass`/`return None`) and confirm the
  test that claimed "red-first" actually goes red against the stub — this is what catches a described-not-
  observed red. A worker's `TASK-DONE` claiming `red-first-Y` without you being able to reproduce the red
  is a defect, flag it.
- Try to break doctor's failure paths (missing tool, wrong macOS version, locked keychain simulation).

### Step 12: rewrite `.claude/` tooling for the tart/SSH model

The four files currently in `.claude/` (`agents/log-researcher.md`, `commands/system-debug.md`, plus two
`triage-*` skills referenced from elsewhere) are Multipass/journalctl/cloud-init tools inherited from
another project — they reference a `tools/system_debug.py` that does not exist here. Rewrite per spec 12
§"The `.claude/` agent loop":

| Path | Change |
|---|---|
| `agents/log-researcher.md` | Rewrite: investigates one macOS **log source** (not a cluster role). Stays haiku, stays distill-not-dump. Collects via `uv run macos-ci vm-debug --source <name> --json`. |
| `commands/system-debug.md` | Rename to `commands/vm-debug.md`. Same three-phase flow: collect evidence → name root cause → `AskUserQuestion` for remediation scope. |
| `commands/vm-status.md` | **New.** Print `artifacts/latest/verdict.json` and `tart list`. Cheap, read-only. |
| `skills/triage-logs/SKILL.md` | Rewrite: fan out one log-researcher per **log source**, not per role. |
| `skills/triage-patterns/SKILL.md` | Rewrite for macOS failure signatures (spec 12's seed table). |

**Crib** `/Users/bossjones/dev/bossjones/multipass-lab/tools/system_debug.py` + its
`_system_debug_core.py` (read-only reference — stdlib-only pure core + ssh-subprocess I/O shell, 0/2/3/4
exit codes, retry/backoff, `--json`), adapting:
- resolve VM via `tart ip <run-id>` (not `tofu output`)
- SSH `admin@` (not `ubuntu@`)
- macOS/tart failure-signature table (spec 12's seed table: `tart ip` never returns, CLT GUI prompt
  firing non-interactively, Rosetta/`/usr/local` vs `/opt/homebrew` mismatch, locked login keychain (G8),
  chezmoi template render errors, asdf shims preceding mise on PATH).

RED-FIRST against fixture log text — this is a `_core`-shaped module (pure signature matching), same
discipline as core-builder's `_triage_core.py`. Coordinate with 🐍 core-builder if there's overlap with
`_triage_core.py` — that module is 🐍's; your rewrite here is the `.claude/` **prose/config** layer that
consumes it, not a second implementation. If you need a new `_triage_core` function that doesn't exist
yet, file it through the backlog (append a note here) rather than writing a second `_triage_core.py`.

### After the image lands (IMAGE-GATED)

- Red-team steps 7–10 live: try to break the harness (kill the VM mid-apply, point at a malformed
  template, etc.) and confirm `verdict.json` correctly names the failing phase.
- **Step 6a canary discipline**: plant the Homebrew token in a scratch file under the built VM's directory
  (use `mv`, never write a fresh secret) and confirm `just verify-no-secrets <vm>` exits 2 **before** 📦
  packer-builder trusts the real exit-0 run. Never trust a canary you haven't seen fail.
- **Step 14**: red-team the matrix — the asdf leg without `--with-prereq-installer` is **expected to
  fail**; confirm that failure is recorded correctly, not silently passed over. Break something on
  purpose (malformed template in a scratch `ZSH_DOTFILES` tree) and confirm `verdict.json` names phase
  `chezmoi-diff` and the cause.

---

## 📡 log-watcher

**Owns**: `.team/logwatch.md` (append-only), nothing else.

1. Wait for 📦 packer-builder to note on the board which `logs/packer-build-*.log` file it launched into
   the 🏗 build pane.
2. Arm on that file: tail it, watching for the process exit (Packer prints a final success/failure banner
   and the `tee` pipeline's exit code is what matters — **confirm the exit code from the log tail or a
   background-job wait, never from `read-screen` on the build pane**, per the lead-brief's rule that
   pixels are never load-bearing evidence).
3. Append every meaningful event to `.team/logwatch.md`: build start, phase transitions Packer logs (VM
   boot, provisioner start, provisioner steps), and above all the terminal outcome.
4. **On failure**: append a `LOGWATCH FATAL` entry with the tail of the failure (last ~50 lines) and
   notify the lead immediately (`cmux notify`). Do not classify the failure yourself — that's ✅
   validator's job once the lead assigns it.
5. **On success**: append `LOGWATCH SUCCESS` with the exit code and log file path, notify the lead.
6. Never touch the build pane yourself beyond tailing its log file on disk. Never edit any file except
   `.team/logwatch.md`.

---

## 👑 lead (reference — this is what you're already doing)

- Board upkeep, backlog routing, FSM transitions, `cmux notify`/`set-status`/`set-progress`.
- **Mid-build hermetic gate (HG)**: while the packer build runs, personally run `uv run pytest` AND
  `just check` on the pre-image tree — both must exit 0, output pasted to the board — BEFORE IMAGE-READY
  is accepted. This ensures integration starts from a known-green tree the moment the image lands.
- Failure handling per lead-brief §8: BUILD FAILS → assign triage to ✅ validator (classify host-issue /
  template-defect / transient) → route to the right owner → circuit breaker at 2 relaunches, 3rd flags
  red + NEEDS-HUMAN OQ.
- WORKER STALLS → nudge, +5min second nudge, still silent → mark 🔴, loan the ticket to ✅ validator,
  re-prompt the stuck pane to read the board and resume. Check for a stranded composer (text above `❯`
  with no `enter` sent).
- GATE: personally run `just check` AND `uv run pytest`, both exit 0, raw output pasted. CLEAN → DONE.
