# 12 — Tooling Surface and the Agent Feedback Loop

The other files in this directory describe *what* the harness does. This one describes *how you drive
it* — and, more importantly, how an autonomous agent knows whether the last thing it did worked.

Everything here is a design specification, not yet built. Where a claim is composed from documented
primitives rather than observed on a running system, it carries an `<!-- UNVERIFIED -->` marker, per
this repo's convention ([00-overview.md](00-overview.md#scope-note)).

## Why this file exists

A harness whose only interface is `harness/run-test.sh` is operator-hostile and agent-hostile in the
same way and for the same reason: there is nothing to run without reading the script, nothing to
unit-test, and no structured signal at the end. An agent handed such a harness has exactly one bit of
information — the process exit code — and must reconstruct everything else by scraping prose from
stdout, which breaks the moment someone adds a colour code.

The feedback cycle *is* the deliverable. The Justfile and the CLI exist to serve it.

## Prior art

Two repos on this machine already solve adjacent problems; this design borrows from both rather than
inventing.

- **`~/dev/bossjones/multipass-lab`** — the Justfile conventions (top variable block, doc-comment-as-help,
  `_`-prefixed private recipes, `uv run` delegation), the testinfra `conftest.py` shape, the PEP-723
  typer+rich CLI style, structured exit codes, and — the load-bearing idea — the **I/O-shell vs pure-core
  split**. `tools/system_debug.py`'s own docstring states the rule:

  > The pure parsing/analysis/policy lives in `_system_debug_core.py` (stdlib-only, hermetically tested
  > in tools/tests/); this file owns the I/O (ssh/tofu subprocess).

  It also documents *why* it shells out to `ssh` rather than opening a socket from Python: to dodge the
  macOS "Local Network" errno-65 block. That reason applies with full force here.

- **`~/dev/markkenny/macos-virtualisation`** — the pinned-IPSW approach to selecting an exact macOS
  point release, and a working (if fragile) Setup Assistant `boot_command`. Note its typo'd `<wai7s>`
  wait token in `Packs/vanilla-26.1.pkr.hcl` as evidence of how brittle keystroke automation is.

## The `macos-ci` package

```
src/macos_ci/
  cli.py                            # typer entrypoint -> `macos-ci` console script
  config.py       _config_core.py   # load/validate macos-versions.toml
  tart.py         _tart_core.py     # argv builders, `tart list --format json`, VNC URL parse
  doctor.py       _doctor_core.py   # requirement table, version compare, verdict
  harness.py      _harness_core.py  # run-id, artifact paths, chezmoi argv, seed-config render
  vm_debug.py     _triage_core.py   # log sweep; failure-signature matching
  gui.py          _gui_core.py      # VNC connect / screenshot / keystrokes
  artifacts.py                      # writes artifacts/<run-id>/*.json
```

### The pure/impure boundary

Each `_core` module is **stdlib-only** and imports nothing from its I/O sibling. Everything that can be
expressed as a pure function — building an argv, parsing a version string, matching a log line against a
signature table, deciding whether a requirement is satisfied — lives there. Everything that touches a
subprocess, a socket, the filesystem, or the clock lives in the sibling.

The payoff: `just test` runs `tests/unit/` and needs **no VM, no network, and no `tart` binary**.
`pytest-subprocess` registers a fake `tart` and the tests assert on the argv the code constructs. This
is the only tier where TDD is practical, and it is the tier an agent runs on every edit.

An obvious first failing test, before a line of implementation exists:

```python
# tests/unit/test_gui_core.py
def test_parse_vnc_url():
    line = "Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415..."
    assert parse_vnc_url(line) == VncTarget(
        host="127.0.0.1", port=59415, password="enhance-chase-volume-push"
    )
```

A cheap guard keeps the boundary honest — if any `_core` grows an I/O import, this fails:

```bash
uv run python -c "import macos_ci._tart_core, macos_ci._doctor_core, macos_ci._gui_core"
```

## `macos-versions.toml` — declarative image selection

Two lanes. The OCI lane clones a cirruslabs prebuilt base image in seconds but only offers the *major*
versions cirruslabs publishes. The IPSW lane builds from a pinned restore image and gets you an exact
point release, at the cost of a long build and a `boot_command` to maintain.

```toml
default = "sequoia"

[image.sequoia]
source = "oci"
ref    = "ghcr.io/cirruslabs/macos-sequoia-base:latest"

[image.tahoe]
source = "oci"
ref    = "ghcr.io/cirruslabs/macos-tahoe-base:latest"

[image."sequoia-15.6.1"]
source = "ipsw"
url    = "https://updates.cdn-apple.com/.../UniversalMac_15.6.1_..._Restore.ipsw"
sha256 = "..."
```

`just up` uses `default`. `just build-ipsw sequoia-15.6.1` drives `packer/ipsw/*.pkr.hcl` with
`from_ipsw = <url>` and verifies the `sha256` before building.

`_config_core.load()` is a pure function and validates: unknown `source` values, an `ipsw` entry missing
`sha256`, and a `default` naming an image that doesn't exist. All three are unit tests.

Direct IPSW links come from MrMacintosh's firmware database, which is what `macos-virtualisation`'s
README also recommends. Apple publishes no stable version-to-URL resolver, so the URL is pinned by hand
and the `sha256` is what makes that pin trustworthy.

## The Justfile

A `Justfile` already exists at the repo root. It sets `set shell := ["bash", "-uc"]` and carries
`default`, `link-check`, `link-check-verbose`, and `link-check-fresh` — lychee over every `*.md`, with
`GITHUB_TOKEN` sourced from `gh auth token` because unauthenticated lychee scrapes GitHub HTML and
rate-limits into spurious 404s. The harness recipes are **added** to that file; it remains the single
source of truth. `Makefile` is a shim, so no recipe is ever written twice:

```make
JUST ?= just
.PHONY: up down build run logs ssh doctor test lint verify clean
up down build run logs ssh doctor test lint verify clean:
	@$(JUST) $@
%:
	@$(JUST) $@
```

Variable block, following `multipass-lab`'s convention:

```just
vm       := env_var_or_default("MACOS_CI_VM", "dotfiles-test")
image    := env_var_or_default("MACOS_CI_IMAGE", "sequoia")
dotfiles := env_var_or_default("ZSH_DOTFILES", justfile_directory() / ".." / "zsh-dotfiles")
vm_user  := "admin"
vmgr     := env_var_or_default("MACOS_CI_VERSION_MANAGER", "mise")
ssh_opts := "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=8 -o BatchMode=yes"
```

`_default:` runs `just --list`; every public recipe carries a doc comment above it that doubles as its
help text; private helpers take a leading `_`; non-trivial bodies delegate to `uv run macos-ci …`.

### Recipe reference

**Lifecycle**

| Recipe | Purpose |
|---|---|
| `doctor` | Preflight every requirement. `--json` for agents. Exit 2 if anything is missing. |
| `up` | `tart clone` → `tart run --no-graphics &` → poll `tart ip` → wait for SSH. |
| `down` (alias `stop`) | Stop the VM, leave the clone on disk. |
| `destroy` | `tart delete` the clone. |
| `recreate` | `destroy` then `up`. |
| `run` | **The main loop.** `doctor` → `up` → `chezmoi diff` → apply → `verify` → `destroy`. |
| `apply` | Only the chezmoi apply, against an already-live VM. Fast iteration. |
| `prune` | Delete orphan clones not tracked under `artifacts/`. |

**Images**

| Recipe | Purpose |
|---|---|
| `build [IMAGE]` | Packer build the golden image via the OCI lane. |
| `build-ipsw VERSION` | Packer build from a pinned IPSW. Verifies `sha256` first. |
| `images` | Print `macos-versions.toml` alongside `tart list`. |
| `pull IMAGE` | `tart pull` the OCI ref. |

**Inspection**

| Recipe | Purpose |
|---|---|
| `ssh` / `exec CMD` | Interactive shell; one-shot remote command. |
| `logs` | Sweep guest logs into `artifacts/<run-id>/logs/`. |
| `debug` | `uv run macos-ci vm-debug --json` — triage, writes `verdict.json`. |
| `status` | `tart list` plus a pretty-printed `artifacts/latest/state.json`. |
| `gui` | `tart run` with a window, for poking at it by hand. |
| `vnc` | `tart run --vnc-experimental`, print the parsed VNC target. |
| `shot LABEL` | Capture one framebuffer PNG into `artifacts/<run-id>/screenshots/`. |

**Testing**

| Recipe | Purpose |
|---|---|
| `test` | Hermetic units. No VM. This is what an agent runs by default. |
| `verify` | `-m vm` — testinfra assertions over SSH. |
| `verify-pty` | `-m pty` — pexpect over `ssh -tt`. |
| `verify-gui` | `-m gui` — VNC screenshots. |
| `verify-manual` | `-m manual` — the only recipe that may ever prompt a human. |
| `matrix` | Cross-product of image × `version_manager`. |

**Quality**

| Recipe | Purpose |
|---|---|
| `lint` / `fmt` / `typecheck` | `ruff check`, `ruff format`, `basedpyright`. |
| `link-check{,-verbose,-fresh}` | **Already implemented.** lychee over every `*.md`, including internal `#anchor` fragments. |
| `ci` | `cirrus run` for local/CI parity. |

## The four test tiers

```toml
[tool.pytest.ini_options]
addopts = "-ra -m 'not vm and not pty and not gui and not manual'"
markers = [
  "vm:     needs a booted tart VM",
  "pty:    needs an interactive PTY (pexpect over `ssh -tt`)",
  "gui:    needs VNC framebuffer access",
  "manual: prompts a human for a y/n verdict",
]
```

Everything heavier than a unit test is opt-in. A bare `uv run pytest` cannot hang, cannot boot a VM,
and cannot block on a human. That property is not a convenience — it is what makes it safe to let an
agent run the test suite on every iteration.

### `vm` — pytest-testinfra over SSH

`conftest.py` follows `multipass-lab/clusters/*/tests/testinfra/conftest.py`: a session-scoped `vm_state`
fixture reads `artifacts/latest/state.json`, an `ssh_config_file` fixture writes a throwaway config, and
the `vm` host fixture polls until reachable before yielding.

```python
@pytest.fixture(scope="session")
def vm(vm_state, ssh_config_file):
    host = testinfra.get_host(f"ssh://admin@{vm_state['ip']}", ssh_config=ssh_config_file)
    deadline = time.monotonic() + 180
    while True:
        try:
            if host.run("true").rc == 0:
                return host
        except Exception:  # noqa: BLE001 — retry until reachable or timeout
            pass
        if time.monotonic() >= deadline:
            raise TimeoutError(f"VM {vm_state['ip']} not SSH-reachable after 180s")
        time.sleep(3)
```

Assertions are ported from `smoke-test-docker.sh`, not invented. The mise-specific ones:

```python
@pytest.mark.vm
def test_mise_is_the_active_version_manager(vm):
    assert vm.run("mise --version").rc == 0
    data = json.loads(vm.run("chezmoi data").stdout)
    assert data["zsh_dotfiles"]["version_manager"] == "mise"

@pytest.mark.vm
def test_asdf_shims_do_not_shadow_mise(vm):
    # ~/.asdf may exist if the optional prereq installer ran; it must not win PATH.
    assert "/.asdf/shims/" not in vm.run("zsh -lc 'which node'").stdout
```

Reuse over reimplementation: `zsh-dotfiles/hack/doctor/check_dev_environment.py` already validates the
dev environment and reads `ZSH_DOTFILES_VERSION_MANAGER`. Run it in-guest as one assertion.

### `pty` — pexpect over `ssh -tt`

Some things are only observable through a terminal: tab completion, keybindings, the escape sequences a
prompt emits. A non-TTY SSH session cannot see any of them.

**This does not contradict G11.** The no-TTY rule governs `chezmoi apply` — it is what makes
`stdinIsATTY` resolve false so prompts take their defaults. Verification runs afterwards and wants the
opposite. Different phase, different requirement.

```python
@pytest.mark.pty
def test_zsh_tab_completion(vm_state):
    child = pexpect.spawn(f"ssh -tt {SSH_OPTS} admin@{vm_state['ip']}", timeout=30)
    child.expect(PROMPT_RE)
    child.send("chezmo\t")
    child.expect("chezmoi")
```

### `gui` — VNC framebuffer

`tart run --vnc-experimental` uses Virtualization.framework's own VNC server and prints its target to
stdout:

```
Opening vnc://:enhance-chase-volume-push@127.0.0.1:59415...
```

`_gui_core.parse_vnc_url()` turns that line into a `VncTarget`; `gui.py` connects with `asyncvnc`, sends
keystrokes, and writes PNGs to `artifacts/<run-id>/screenshots/NN-<label>.png`.

Two reasons this is the right mechanism rather than `screencapture` over SSH:

1. **It sidesteps TCC.** Capture happens on the host, at the hypervisor level. `screencapture` invoked
   from an SSH session is gated by macOS's Screen Recording permission and will fail or return a black
   frame; granting that permission to `sshd` is invasive and version-fragile.
2. **It is already proven.** Packer's `tart-cli` builder drives its entire Setup Assistant
   `boot_command` over exactly this channel — hence its `disable_vnc` and `vnc_port_min`/`vnc_port_max`
   fields ([02-packer-tart-builder.md](02-packer-tart-builder.md)).

Reserve this tier for what only an eye can judge — nerd-font glyph rendering, colourschemes, iTerm2
behaviour. Asserting on pixels is slower and far more brittle than asserting on a PTY's byte stream, so
prefer the `pty` tier whenever the question can be answered there.

The screenshots are also the channel by which Claude *sees*: PNGs under `artifacts/` render visually
when read.

<!-- UNVERIFIED: `--vnc-experimental` is labelled experimental by Tart itself, and the exact stdout
format above is composed from a single reported example, not observed here. Confirm during Phase 1
before relying on `parse_vnc_url`'s regex. `vncdotool` is the fallback if `asyncvnc` misbehaves. -->

### `manual` — the human tier

Real test functions, so verdicts land in the same JSON report as everything else. The `confirm()`
fixture calls `pytest.skip()` when `not sys.stdin.isatty()`, so even an explicit `-m manual` degrades to
skips in a non-interactive context rather than hanging an agent.

```python
@pytest.mark.manual
def test_prompt_renders_with_glyphs(vm_gui, confirm):
    vm_gui.open_terminal()
    assert confirm("Does the starship prompt show a git branch glyph and no tofu boxes?")
```

## The artifacts contract

Every command writes structured state. The agent reads files; it never scrapes prose.

```
artifacts/<run-id>/
  state.json        {vm, ip, image, version_manager, phase, started_at}
  doctor.json       [{tool, required, found, ok}]
  chezmoi-diff.txt  pre-apply lint output (stderr must be empty)
  apply.log         full stdout/stderr of `chezmoi init --apply`
  pytest.json       per-test verdicts (pytest-json-report)
  manual.json       y/n verdicts from the manual tier
  screenshots/NN-<label>.png
  logs/{install,brew,chezmoi,unified}.log
  verdict.json      {ok, phase, cause, evidence: [{file, line, text}], next_action}
artifacts/latest -> <run-id>        # symlink
```

`verdict.json` is the contract. `just run` writes one on every path, including a crash.

### Exit codes

Copied from `multipass-lab/tools/system_debug.py`, whose docstring defines them:

| Code | Meaning |
|---|---|
| `0` | Healthy |
| `2` | Issues found (assertions failed, signatures matched) |
| `3` | VM unreachable |
| `4` | Usage or resolve error |

The distinction between `2` and `3` is what lets an agent decide whether to investigate the dotfiles or
investigate the VM, without reading a single line of English.

## The claims ledger — a feedback loop for *documents*

The harness gives the *code* a feedback loop. The specs need one too, and for the same reason: an agent
writing markdown has no oracle, so plausible-sounding detail costs it nothing.

This repo has already paid for that once. The first research run shipped a ground truth — "G10: these
four `docs.getutm.app` URLs are 404, do not fetch, do not cite" — and it was wrong. Three URLs were
live. The fourth, `settings-apple/devices/`, had never existed: it was fabricated, not dead. **The rule
forbidding verification is precisely what prevented its disproof.** A downstream spec then cited the
wrong page for the Apple-backend device toggles, and `settings-apple/virtualization/` — the page that
actually documents them — went undiscovered.

The fix is to make truth executable:

```bash
just check              # link-check + verify-claims + unverified-count
just verify-claims      # re-run the evidence behind every claim
just verify-claims-json # the same, for an agent to read
```

`.team/claims.jsonl` holds one record per load-bearing assertion. `tools/verify_claims.py` re-executes
its evidence. Evidence kinds, cheapest first:

| Kind | Proves | Kills |
|---|---|---|
| `file-contains` | a local working tree contains a string | claims about repos nobody opened |
| `file-line` | line *N* of a file contains a string | **hallucinated `file:line` citations** |
| `absent` | a string is *not* present | unfalsifiable negative claims |
| `cli-help` | `<tool> --help` emits a flag | remembered flags that don't exist |
| `doc-index` | a path appears in the doc site's own search index | **fabricated URLs (the G10 failure)** |
| — | every URL and internal `#anchor` resolves | dead links, broken anchors (lychee) |

The `doc-index` kind is the direct antidote. Both doc sites publish the static JSON index their search
box uses — `https://tart.run/search/search_index.json` (101 pages) and
`https://docs.getutm.app/assets/js/search-data.json` (281 entries / 78 pages). **The index is the
authoritative page list: if a path is not in it, that page does not exist.** No fetching, no scraping,
no 403. One query for `trackpad` would have found the page G10 missed.

### The ledger tests its own oracle

A verifier nobody verifies is just a second thing to trust. Any claim may set `"must_fail": true`,
inverting the verdict: its evidence is required *not* to reproduce. One control claim asserts the
fabricated `settings-apple/devices/` URL. If it ever starts passing, the `doc-index` oracle has silently
broken and every other `doc-index` claim is worthless — so the run fails loudly instead of going green
on a dead check. (An `UNREACHABLE` result is never inverted; a network failure must not masquerade as a
successful control.)

### Rule of thumb

A claim you cannot express as a ledger entry is a claim you must mark `<!-- UNVERIFIED -->` in the spec.
`just unverified-count` prints the current inventory. That number is an honesty budget, not a warning to
be silenced — it should go down because claims got verified, never because markers got deleted.

## The `.claude/` agent loop

The four files currently in `.claude/` are Multipass/journalctl/cloud-init tools inherited from another
project. They reference a `tools/system_debug.py` and a set of `just` recipes that do not exist in this
repo. They are stale and must be rewritten, not extended.

| Path | Change |
|---|---|
| `agents/log-researcher.md` | Rewrite: investigates one macOS **log source** (not a cluster role). Stays `haiku`, stays distill-not-dump. Collects via `uv run macos-ci vm-debug --source <name> --json`. |
| `commands/system-debug.md` | Rename to `commands/vm-debug.md`. Same three-phase flow: collect evidence → name the root cause → `AskUserQuestion` for remediation scope. |
| `commands/vm-status.md` | **New.** Print `artifacts/latest/verdict.json` and `tart list`. Cheap, read-only orientation. |
| `skills/triage-logs/SKILL.md` | Rewrite: fan out one `log-researcher` per **log source** rather than per role. |
| `skills/triage-patterns/SKILL.md` | Rewrite for macOS failure signatures (below). |

### Log sources

Where a Linux cluster has `journalctl` and `cloud-init status`, a macOS guest has:

| Source | Command |
|---|---|
| OS install / CLT | `/var/log/install.log` |
| Homebrew | `brew config`, `~/Library/Logs/Homebrew/` |
| chezmoi apply | `artifacts/<run-id>/apply.log` (captured host-side) |
| Unified log | `log show --predicate '...' --last 30m` |
| launchd | `launchctl print system/<label>` |

### Seed failure signatures

Ship `triage-patterns` with these and grow it from real Phase-1 failures rather than inventing more:

| Signature | Root cause |
|---|---|
| `tart ip <vm>` never returns | Guest never got DHCP. Check the softnet/bridged networking mode. |
| `xcode-select: note: install requested` | The CLT GUI prompt fired inside a non-TTY run. The golden image must install CLT non-interactively via `softwareupdate --install <label>`. |
| `Cannot install under Rosetta 2` / `/usr/local` vs `/opt/homebrew` | Architecture mismatch. The VM is arm64; Homebrew must live at `/opt/homebrew`. |
| Headless boot + `The specified item could not be found in the keychain` | The login keychain is locked. This is G8 — see [01-tart-core.md](01-tart-core.md#headless-mode-and-the-macos-15-keychain-requirement-g8). |
| `chezmoi: template: ...` on `chezmoi diff` | Template render error. The run must fail here, *before* apply. |
| `which node` resolves to `~/.asdf/shims/node` under `version_manager=mise` | asdf shims precede mise on `PATH`. See [09-dotfiles-under-test.md](09-dotfiles-under-test.md#the-version_manager-selector-asdf--mise). |

### Networking caveat

`vm_debug.py` shells out to `ssh` rather than opening a socket from Python. This is deliberate, and the
reason is recorded in `multipass-lab/tools/system_debug.py`: it dodges the macOS "Local Network" errno-65
block, which otherwise causes Python-initiated connections to VM IPs to fail in ways that look like the
VM is down. `pytest-testinfra` is configured with the `ssh` backend and an explicit `ssh_config` for the
same reason.

## Closing the loop

The end-to-end check that the feedback cycle actually works is not a passing test — it is a *failing*
one, correctly reported. Point `ZSH_DOTFILES` at a tree containing a deliberately malformed chezmoi
template, run `just run`, and confirm that:

1. The run fails at the `chezmoi-diff` phase, before any install step executes.
2. `artifacts/latest/verdict.json` names that phase and cites the offending template line.
3. The process exits `2`, not `3`.
4. `/vm-debug` reaches the same conclusion from the artifacts alone, without re-running anything.

If all four hold, the agent has a feedback cycle. If any fails, it has a log file and a guess.
