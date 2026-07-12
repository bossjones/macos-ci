# Plan: Make UTM a first-class manual/GUI lane

## Task Description

[docs/tutorials/01-getting-started.md](../docs/tutorials/01-getting-started.md) names UTM only to
exclude it ("present in this stack only as a manual escape hatch… not part of the automated
harness"). That framing is correct per the ADR
([specs/macos-ci/10-tart-vs-utm-adr.md](macos-ci/10-tart-vs-utm-adr.md) — tart is primary, UTM is
the escape hatch), but the escape hatch is currently **prose-only**: zero `just utm-*` recipes, zero
Python, no config lane, no tests, no doctor row.

The actual need is exactly what the ADR reserves UTM for: boot a macOS VM **with a GUI**, get the
zsh-dotfiles onto it, and manually evaluate the experience in iTerm2 (prompt rendering, plugins,
colors, keybindings) from a human perspective — judging whether the dotfiles are a good user
experience, not just whether they apply cleanly. This plan makes that lane real, with feedback loops
at every layer: evidence-first spikes with kill criteria, an SSH verification channel, recorded UX
verdicts, TDD, and pyrefly/basedpyright gates.

Tart remains the automated CI lane. This lane never gates CI.

## Objective

- `just utm-up` boots a windowed UTM clone of a golden image and prints its IP.
- `just utm-bootstrap-dotfiles` prints the exact guest-side commands (VirtioFS mount + chezmoi
  apply) to paste into iTerm2 — the human drives the apply.
- `just utm-ssh` / `just utm-exec` provide the feedback loop; `just utm-verify-manual` records the
  UX checklist verdict per session.
- All new Python follows the pure-core/impure-shell split, TDD-first, pyrefly/basedpyright clean.
- Net-new verified facts land as amendments to
  [specs/macos-ci/05-utm-automation.md](macos-ci/05-utm-automation.md) and
  [specs/macos-ci/06-utm-macos-guest.md](macos-ci/06-utm-macos-guest.md), plus new entries in
  `.team/claims.jsonl`. No new spec corpus.

## Problem Statement

The specs prove (with ledger claims) that Apple-backend macOS guests have **no QEMU guest agent**:
`utmctl exec` / `file` / `ip-address` do not work
([05-utm-automation.md](macos-ci/05-utm-automation.md) §4.2, claims
`utmctl-exec-needs-qemu-guest-agent`, `utmctl-help-lists-ip-address`). Spec 05 currently says the
UTM lane has no equivalent of `tart ip`. That statement is *about utmctl*, not about the host:
`tart ip` works by reading `/var/db/dhcpd_leases` keyed by MAC, and a UTM Shared-Network VM leases
from the same host vmnet stack, with its MAC recorded in the `.utm` bundle's `config.plist`. So a
`utm ip` equivalent is buildable host-side — pending a verification spike. Likewise there is no
automated path from the tart golden image to a UTM VM; the Apple-backend drive-import constraint
("Only raw images are supported",
[settings-apple/drive/#creation](https://docs.getutm.app/settings-apple/drive/#creation)) needs a
spike with a documented fallback.

## Solution Approach

Two evidence-first spikes (their captured output becomes unit-test fixtures), then a pure core
`_utm_core.py` + impure shell `utm.py` mirroring the existing `_tart_core.py`/`tart.py` pattern, a
`utm` Typer sub-app, `just utm-*` recipes, an optional-tool row in `doctor`, a UTM manual-UX
checklist test file, and the docs/spec/claims deliverables.

### Decisions already made (settled with the repo owner — do not re-litigate)

1. **Reuse the tart golden image.** Verify a tart-`disk.img` → UTM Apple-backend import; fallback if
   the imported disk won't boot: one-time manual golden UTM VM, cloned per session via
   `utmctl clone`. Either way the downstream workflow is identical.
2. **SSH + IP discovery.** MAC from `config.plist` → `/var/db/dhcpd_leases` lookup; mDNS
   `<hostname>.local` fallback; serial console as the documented degraded path.
3. **Python core + recipes, TDD, pyrefly-clean.** Unit tests first; gates after every phase.
4. **Human drives the dotfiles.** VirtioFS shared directory delivers the source
   ([guest-support/macos/#shared-directories](https://docs.getutm.app/guest-support/macos/#shared-directories),
   macOS 13+ guests); the user applies interactively in the GUI. SSH is the *feedback* channel, not
   the applier.
5. **Recorded UX checklist** via the existing `pytest -m manual` human-verdict lane.
6. **Full citizenship**: optional `doctor` row (never fails tart-only users) + a real tutorial 01
   section.
7. **Structure**: this single spec + amendments to specs 05/06 + ledger claims. No
   `specs/utm-lane/` breakout.

### Verified facts this design rests on (UTM docs search index, 2026-07-10, UTM docs as published)

- Apple-backend drive **Importing**: "the image will be copied to the .utm package. Only raw images
  are supported." — [settings-apple/drive/#creation](https://docs.getutm.app/settings-apple/drive/#creation)
- **VirtioFS shared directories for macOS 13+ guests**: `mkdir -m 777 -p <mnt>` then
  `mount_virtiofs share <mnt>` in the guest —
  [guest-support/macos/#shared-directories](https://docs.getutm.app/guest-support/macos/#shared-directories)
- **Missing features** on the Apple backend: USB sharing; clipboard sharing *before macOS 15*;
  dynamic resolution *before macOS 14*; save states *before macOS 14* —
  [guest-support/macos/#missing-features](https://docs.getutm.app/guest-support/macos/#missing-features).
  A Sequoia (15) guest therefore gets clipboard sharing and dynamic resolution — both useful for
  the UX-evaluation use case.
- **Shared Network mode**: "Services running on the guest and the host can see each other" —
  [settings-apple/devices/network/#hardware](https://docs.getutm.app/settings-apple/devices/network/#hardware).
  SSH is reachable; host-side vmnet DHCP is what makes the `dhcpd_leases` approach plausible.
  **Proven 2026-07-11**: a Shared-Network UTM macOS guest does take a vmnet lease that lands in
  `/var/db/dhcpd_leases` — `macos-ci utm ip --vm dotfiles-golden-utm` resolved the bundle's MAC to
  `192.168.64.3` and SSH answered there. Spike B's core premise is settled.
- Hard constraints reconfirmed (settled facts, see [CLAUDE.md](../CLAUDE.md) and
  [05-utm-automation.md](macos-ci/05-utm-automation.md)): no guest agent → no
  `utmctl exec/file/ip-address`; lifecycle + host-side serial only; `utmctl` requires UTM.app
  running in a GUI session — acceptable here because the GUI is the point.

## Relevant Files

Existing files to extend:

- `src/macos_ci/cli.py` — one line: mount the `utm` Typer sub-app.
- `src/macos_ci/_doctor_core.py` — `OPTIONAL_TOOLS`, `DoctorFacts.optional_tool_versions`, optional
  `CheckResult` rows (`ok=True` unconditionally).
- `src/macos_ci/doctor.py` — fill `optional_tool_versions` from a UTM.app `Info.plist` reader.
- `src/macos_ci/harness.py` — add `lane: "tart"` to the `state.json` it writes (the key does not
  exist today), so `vm_state`-consuming tiers can tell lanes apart.
- `src/macos_ci/_harness_core.py` — **reused, not modified**: `chezmoi_argv` (line 27),
  `chezmoi_init_only_argv` (46), `bootstrap_ssh_argv` (125), `steady_state_ssh_argv` (166).
- `Justfile` — new variables + the `utm-*` recipe group (append-only: existing ledger claims pin
  Justfile line numbers).
- `tests/unit/test_doctor_core.py`, `tests/unit/test_doctor.py` — optional-tool tests.
- `docs/tutorials/01-getting-started.md` — new "Optional: the UTM manual lane" section.
- `specs/macos-ci/05-utm-automation.md` — new §4.5 (host-side IP discovery).
- `specs/macos-ci/06-utm-macos-guest.md` — VirtioFS transcript + golden-disk import section.
- `.team/claims.jsonl` — new claims (see Step 10).

### New Files

- `src/macos_ci/_utm_core.py` — pure core (argv builders, parsers; stdlib-only).
- `src/macos_ci/utm.py` — impure shell (subprocess around `utmctl`, file reads) + Typer sub-app.
- `tests/unit/test_utm_core.py` — pure-core unit tests (written first).
- `tests/unit/test_utm.py` — shell unit tests (pytest-subprocess, `tmp_path`).
- `tests/manual/test_utm_ux.py` — the recorded iTerm2 UX checklist.

## Implementation Phases

### Phase 0: Spikes (evidence, no code)

Both spikes are manual, run on the author's host, and produce three outputs: unit-test fixture
strings, dated prose for the spec 05/06 amendments, and the final claims list. Nothing in later
phases may contradict a spike observation.

### Phase 1: Pure core

`tests/unit/test_utm_core.py` → `_utm_core.py`. Gate.

### Phase 2: Shell + CLI + doctor

`tests/unit/test_utm.py` → `utm.py`; Typer wiring; doctor optional row. Gate.

### Phase 3: Surface

Justfile recipes, `tests/manual/test_utm_ux.py`, live smoke of the full session loop.

### Phase 4: Truth deliverables

Tutorial section, spec 05/06 amendments, ledger claims; `just check` green.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom. Gate = `just lint && just typecheck &&
just check-pyrefly && just test` — run it at the end of every step that touches Python. The pyrefly
baseline (`pyrefly-baseline.json`) is empty and stays empty: new code must be clean, never
baselined.

### 1. Spike A — tart golden disk → UTM import

> **RESOLVED 2026-07-11 — Spike A succeeded; the fallback was not needed.** The plain import boots to
> a silent black-screen hang, and the machine-identifier transplant below (the step this plan called
> "best-effort, untried") is exactly what fixes it — plus a second, independent edit the plan did not
> anticipate: the drive's `Nvme` flag must be `false`, because NVMe is illegal on an Apple-backend
> macOS guest. With both applied the golden reaches loginwindow, answers SSH, and survives
> `utmctl clone` with its identity intact. Full observed record: [`06-utm-macos-guest.md`](macos-ci/06-utm-macos-guest.md)
> §11. Scripted procedure: [`prereq-mvp.md`](prereq-mvp.md) §1. The steps below are kept as the
> original spike design.

- Never touch the live golden: `tart clone dotfiles-golden utm-export-scratch`, then inspect
  `~/.tart/vms/utm-export-scratch/` — `file disk.img` and the `config.json` disk-format field.
- If raw → copy `disk.img` aside. If ASIF → attempt conversion
  (`diskutil image convert` <!-- UNVERIFIED --> — untried; no conversion path means fall back
  immediately).
- In the UTM GUI: create a new Apple-backend macOS VM → Drive settings → delete the created disk →
  **Import** the raw image. Set Network = Shared; add a VirtioFS shared directory pointing at the
  zsh-dotfiles checkout; add a serial (PTTY) device.
- **Success criterion**: the guest reaches loginwindow in the UTM window, `admin`/`admin` logs in,
  and SSH answers on the discovered IP.
- **Kill criteria**: boot failure after (a) a plain import and (b) one machine-identifier
  transplant attempt (tart `config.json` hardwareModel/ECID → UTM `config.plist` `MacPlatform`).
  Two dead attempts → **fallback**: build a one-time golden UTM VM from IPSW, provision by hand to
  golden parity (Homebrew, chezmoi, sshd on, admin/admin), keep it as `dotfiles-golden-utm`, clone
  per session. *(Outcome: (a) failed as predicted, (b) succeeded — the transplant is the fix, not a
  best-effort guess. The fallback was never reached.)*
- Record the outcome as dated prose in spec 06 (boot success is not machine-checkable); the
  raw-only doc sentence becomes ledger claim `utm-drive-import-raw-only`.

### 2. Spike B — IP discovery (MAC → /var/db/dhcpd_leases)

- `ls -l /var/db/dhcpd_leases` — confirm it is readable unprivileged (verify, don't assume).
- `plutil -p "~/Library/Containers/com.utmapp.UTM/Data/Documents/<vm>.utm/config.plist" | grep -i mac`
  — confirm the bundle path, the plist format (XML vs binary), and the key path to `MacAddress`.
  Capture a redacted plist as a unit-test fixture. **Confirmed 2026-07-11 on this host** (dmg
  install): the bundle lives at exactly that path, `config.plist` is XML, and the MAC is at
  `Network[0].MacAddress`. Caveat: `utmctl clone` copies the MAC, so a clone and its golden are
  indistinguishable to a MAC→lease lookup — never run both at once.
- Boot the VM (Shared Network); grep the normalized MAC in `/var/db/dhcpd_leases`; capture one full
  lease block verbatim as the `parse_dhcpd_leases` fixture.
- Cross-check three ways: `ssh admin@<ip> true` succeeds; `ifconfig en0` typed in the guest window
  matches; `arp -an | grep <mac>` matches (validates the arp fallback parser too).
- mDNS fallback probe: `hostname` in guest → `dscacheutil -q host -a name <hostname>.local` on
  host. Note whether the hostname survives cloning — two clones with one hostname collide, which is
  why leases-by-MAC is primary and mDNS is fallback-only.
- Capture `utmctl --help`, `utmctl clone --help`, `utmctl start --help`, and `utmctl list` output
  as fixtures. First check with `pgrep UTM` whether `--help` alone launches UTM.app.
- **Kill criteria**: if Shared-Network leases never appear in `/var/db/dhcpd_leases`, promote
  `arp -an` matching to primary; if neither works, the lane still functions via serial
  (`utm-serial`, log in, `ifconfig`) — document that as the degraded path and make `utm ip` report
  a clear error naming it.

### 3. Pure core tests, then `_utm_core.py`

- Write `tests/unit/test_utm_core.py` first (style of `test_tart_core.py`: bare asserts on exact
  argv lists; Spike fixtures verbatim):
  `test_normalize_mac_lowercases_and_strips_octet_zero_padding`,
  `test_parse_dhcpd_leases_single_block`, `test_find_ip_for_mac_prefers_newest_lease`,
  `test_find_ip_for_mac_returns_none_when_absent`, `test_find_ip_for_mac_arp`,
  `test_extract_macs_from_config_plist_xml` and `_binary` (built in-test via
  `plistlib.dumps(..., fmt=...)`), `test_bundle_config_path`,
  `test_start_argv_shows_window_by_default`, `test_start_argv_recovery`, `test_stop_argv_modes`,
  `test_clone_argv_shape` (pinned to Spike B's help capture), `test_attach_argv_index`,
  `test_parse_utmctl_list_name_with_spaces`, `test_virtiofs_mount_commands`,
  `test_manual_apply_script_embeds_chezmoi_argv`.
- Implement `src/macos_ci/_utm_core.py` (pure, stdlib-only; `plistlib` is stdlib and pure over
  bytes). Docstrings cite spec sections the way `_tart_core.py` does.
  - Constants: `UTMCTL_DEFAULT_PATH = "/Applications/UTM.app/Contents/MacOS/utmctl"`,
    `DHCPD_LEASES_PATH = "/var/db/dhcpd_leases"`,
    `UTM_DOCUMENTS_DIR = "~/Library/Containers/com.utmapp.UTM/Data/Documents"` (Spike B pins it),
    `VIRTIOFS_SHARE_TAG = "share"` (Spike A/B pins it),
    `UTM_GUEST_MOUNT_POINT = "/Volumes/dotfiles"` (our convention).
  - Dataclasses: `DhcpLease(name, ip_address, hw_address, lease)` — `hw_address` normalized,
    `lease` is the hex expiry used for newest-wins dedup; `UtmVm(uuid, status, name)` — name may
    contain spaces, parse with `split(maxsplit=2)`.
  - `normalize_mac(mac) -> str` — lowercase, per-octet `f"{int(x,16):x}"`; `dhcpd_leases` drops
    leading zeros (`1e:2:33:…`).
  - `parse_dhcpd_leases(text) -> list[DhcpLease]` — `{…}` blocks of `key=value` lines;
    `hw_address` value carries a `"1,"` hardware-type prefix.
  - `find_ip_for_mac(leases_text, mac) -> str | None` — normalize both sides; newest lease wins.
  - `find_ip_for_mac_arp(arp_output, mac) -> str | None` — fallback over `arp -an`.
  - `extract_macs_from_config_plist(data: bytes) -> list[str]` — `plistlib.loads`, recursive walk
    collecting every `MacAddress` string value (defensive against UTM config drift), normalized.
  - `bundle_config_path(documents_dir, vm_name) -> str`.
  - utmctl argv builders, all with `*, utmctl: str = UTMCTL_DEFAULT_PATH`: `list_argv`,
    `status_argv`, `start_argv(name, *, recovery=False, hide=False)` — **no `--hide` by default;
    the window is the product** — `stop_argv(name, *, mode: Literal["request","force","kill"] =
    "request")`, `clone_argv(source, *, name=None)`, `delete_argv`, `attach_argv(name, *,
    index=None)`.
  - `parse_utmctl_list(text) -> list[UtmVm]`.
  - `virtiofs_mount_commands(mount_point=UTM_GUEST_MOUNT_POINT, tag=VIRTIOFS_SHARE_TAG) ->
    list[str]` — `["mkdir -m 777 -p '<mnt>'", "mount_virtiofs <tag> '<mnt>'"]`.
  - `manual_apply_script(*, source, version_manager="mise") -> str` — `shlex.join` over
    `_harness_core.chezmoi_argv(...)` plus the `~/.local/share/chezmoi` symlink line (same
    rationale as `harness.py`'s `_bootstrap_chezmoi_source_symlink`) — the paste-into-iTerm2 block.
  - **Deliberately not reused**: `_tart_core.DirMount` — UTM sharing is bundle config, not
    per-launch argv (ledger claim `utmctl-start-help-has-no-dir-flag` + its positive control).
- Gate.

### 4. Shell tests, then `utm.py` functions

- Write `tests/unit/test_utm.py` (pytest-subprocess `FakeProcess` + `tmp_path`, style of
  `test_harness.py`): `test_list_vms_invokes_no_real_utmctl`,
  `test_ip_reads_leases_file_not_subprocess`, `test_ip_falls_back_to_arp`,
  `test_mac_for_vm_reads_bundle_plist`, `test_wait_for_ip_times_out` (monkeypatched clock),
  `test_utm_app_version_reads_info_plist`.
- Implement `src/macos_ci/utm.py`: `UtmError(RuntimeError)` mirroring `HarnessError`
  (phase + detail); `utm_app_version()` via `plistlib` over `UTM.app/Contents/Info.plist`
  `CFBundleShortVersionString` — **never `utmctl version`, which launches UTM.app**; `list_vms`,
  `status`, `start`, `stop`, `clone`, `delete`, `read_config_plist_bytes`, `mac_for_vm` (first MAC,
  `UtmError` if none), `ip(name, *, leases_path=DHCPD_LEASES_PATH)` (leases → arp fallback),
  `wait_for_ip(name, *, timeout=180.0)`, `_bootstrap_key_trust(ip)` + `_wait_for_ssh(ip)` — a thin
  ~20-line re-implementation of the harness two-phase SSH bootstrap using the `_harness_core`
  builders and the same `harness/ssh/id_ed25519_harness` key (a shared `sshboot.py` extraction is
  an optional later refactor, out of scope). `_documents_dir()` honors a `MACOS_CI_UTM_DIR` env
  override.
- Gate.

### 5. Typer wiring

- Tests first: `test_cli_mounts_utm_subapp` (Typer `CliRunner` on `--help`),
  `test_utm_bootstrap_dotfiles_prints_mount_and_apply`.
- Typer commands on `utm.app`: `doctor`, `ip`, `mac`, `up`, `status`, `stop`, `destroy`, `clone`,
  `bootstrap-dotfiles`, `import-golden`.
  - `up` = clone-if-missing → windowed start → `wait_for_ip` → two-phase SSH bootstrap → write
    `artifacts/<run-id>/state.json` with the harness's key shape **plus `lane: "utm"`**; also add
    `lane: "tart"` to `harness.py`'s writer in the same commit.
  - `import-golden` stages the raw disk copy and prints the one-time manual GUI checklist — it does
    not pretend to automate what only the GUI can do.
- `cli.py`: `app.add_typer(utm.app, name="utm")`.
- Gate.

### 6. Doctor optional row

- Tests first in `tests/unit/test_doctor_core.py`: `test_optional_tool_missing_is_still_ok`,
  `test_optional_tool_reports_version`, `test_overall_ok_unaffected_by_optional_rows`; in
  `tests/unit/test_doctor.py`: Info.plist reader against a tmp fake bundle.
- `_doctor_core`: `OPTIONAL_TOOLS: tuple[str, ...] = ("utm",)`; `DoctorFacts` gains
  `optional_tool_versions: dict[str, str | None]`; `check()` appends
  `CheckResult(tool="utm", required="optional", found=<version or None>, ok=True)` — `ok=True`
  unconditionally, so tart-only users never fail.
- `doctor.py::collect_facts()` fills it from the Info.plist reader (no Apple Events, no app
  launch).
- Gate.

### 7. Justfile recipes

- New variables next to the existing block:
  `utm_vm := env_var_or_default("MACOS_CI_UTM_VM", "dotfiles-utm")`,
  `utm_golden := env_var_or_default("MACOS_CI_UTM_GOLDEN", "dotfiles-golden-utm")`,
  `utmctl := "/Applications/UTM.app/Contents/MacOS/utmctl"`.
- New group `# ===== UTM (manual GUI lane — spec 10: human escape hatch, not CI) =====`, appended
  (never inserted — ledger claims pin existing line numbers):

| Recipe | Semantics |
|---|---|
| `utm-doctor` | UTM.app version via Info.plist, golden bundle exists, leases file readable; exit 2 on miss |
| `utm-import-golden` | one-time: stage tart golden disk as raw + print the manual GUI import checklist (Spike A outcome) |
| `utm-clone` | `utmctl clone` golden → session VM; no-op if it exists |
| `utm-up` | clone-if-missing → windowed start → MAC→leases IP → two-phase SSH → state.json (`lane: utm`) |
| `utm-gui` | `open -a UTM` |
| `utm-bootstrap-dotfiles` | print guest-side VirtioFS mount + chezmoi apply block to paste into iTerm2; `--over-ssh` may run only the *mount* remotely — the apply stays human |
| `utm-ip` | the `tart ip` equivalent |
| `utm-ssh` | `ip=$(… utm ip) && ssh {{ssh_opts}} -i harness/ssh/id_ed25519_harness {{vm_user}}@"$ip"` |
| `utm-exec CMD` | one-shot remote command over the same SSH |
| `utm-serial` | `{{utmctl}} attach {{utm_vm}}` — the only guest channel utmctl offers |
| `utm-status` | `{{utmctl}} list` |
| `utm-stop` | graceful stop (request mode) |
| `utm-destroy` | delete the session clone; golden untouched |
| `utm-verify-manual` | `pytest -m manual tests/manual/test_utm_ux.py --json-report --json-report-file=artifacts/latest/manual-utm.json` |

- Validate with `just --list` and `just utm-doctor`, then a live smoke:
  `utm-up → utm-ip → utm-ssh → utm-destroy` (manual; evidence goes in the PR notes).

### 8. Manual UX checklist

- `tests/manual/test_utm_ux.py`, same contract as `tests/manual/test_visual.py`: every prompt goes
  through the `confirm()` fixture — a non-interactive run degrades to a skip, never hangs an agent.
  Verdicts land in the pytest JSON report (`artifacts/latest/manual-utm.json` via the recipe).
- Local fixture `utm_session(vm_state)` skips unless `vm_state["lane"] == "utm"`
  ("run `just utm-up` first").
- Checklist tests — each is one `confirm()` question about what is on screen in the UTM window's
  iTerm2:
  - `test_iterm2_prompt_renders_with_glyphs` — git-branch glyph, no tofu/replacement boxes
  - `test_sheldon_plugins_active` — syntax highlighting + autosuggestion ghost text
  - `test_keybindings_history_search` — Ctrl-R opens the configured history search
  - `test_tab_completion_menu_renders` — completion menu draws and is navigable
  - `test_colorscheme_and_profile` — colors not washed out; 24-bit test strip smooth
  - `test_no_first_run_warnings` — no compaudit/"insecure directories"/command-not-found noise
  - `test_keyboard_input_fidelity` — Option/arrow word-motion behaves (a GUI-only signal SSH can't
    give)
- Deselected by default via the existing pytest `addopts`; hermetic `just test` stays green
  throughout.

### 9. Docs and spec amendments

- **Tutorial 01**: new section *"Optional: the UTM manual lane"* — what it's for (per the ADR),
  install + `just utm-doctor`, the one-time `utm-import-golden` (import path AND fallback), the
  session loop (`utm-up` → `utm-bootstrap-dotfiles` → paste into iTerm2 → evaluate →
  `utm-verify-manual` → `utm-destroy`), and an explicit "this lane never gates CI".
- **Spec 05**, new §4.5 "IP discovery without a guest agent (host-side)": the MAC→`dhcpd_leases`
  mechanism with date + UTM/host versions, the arp/mDNS/serial fallback chain, scoped to Shared
  Network mode; it names the way §4.2's "the IP must be learned some other way" left open.
- **Spec 06**: the VirtioFS section gains the verified mount transcript and the
  `/Volumes/dotfiles` convention; new section "Importing the tart golden disk" records Spike A's
  outcome — anything untried stays marked `<!-- UNVERIFIED -->`.

### 10. Ledger claims

Append to `.team/claims.jsonl` (grep for duplicates first; no claim's evidence may launch UTM.app —
Info.plist reads only, and `utmctl … --help` only if Spike B's pgrep check confirms it doesn't
launch the app):

| id | kind | expect | notes |
|---|---|---|---|
| `utm-drive-import-raw-only` | doc-contains, site utm, page `/settings-apple/drive/` | `Only raw images are supported` | cited by spec 06 |
| `utm-virtiofs-mount-command` | doc-contains, page `/guest-support/macos/` | `mount_virtiofs` | skip if an equivalent claim already exists |
| `utmctl-help-lists-clone` | cli-help, local_only | `clone` | argv `[utmctl, "--help"]` |
| `utmctl-attach-help-lists-index` | cli-help, local_only | `--index` | |
| `utmctl-start-help-has-no-dir-flag` | cli-help, local_only, must_fail, polarity negative | `--dir` | claim: UTM sharing is bundle config, unlike `tart run --dir`; `control` names the next row |
| `utmctl-start-help-lists-recovery` | cli-help, local_only | `--recovery` | paired positive control proving the help text was captured |
| `utm-golden-bundle-has-mac-address` | file-contains, local_only | `MacAddress` | target: the golden `.utm/config.plist`; drop to spec prose if the plist is binary and non-greppable (Spike B decides) |
| `utm-ip-parser-reads-dhcpd-leases` | file-line, local_only | `dhcpd_leases` | pins spec 05 §4.5's sentence to `src/macos_ci/_utm_core.py:<line>` |

Ledger rules honored: negative probes carry `polarity: "negative"` plus a `control` field naming
their positive twin; `UNREACHABLE:`/`STRUCTURE:` prefixes are never inverted by `must_fail`.

### 11. Final validation

- Run every command in Validation Commands below; all must pass.
- Burn down the `<!-- UNVERIFIED -->` markers this spec introduced: each spike observation either
  converts a marker into cited fact (spec amendment + claim) or deletes the feature it hedged.
  `just unverified-count` falls because claims got verified, never because markers got deleted.

## Testing Strategy

- **Hermetic units** (default `just test`): every parser and argv builder in `_utm_core.py` is pure
  and tested against Spike fixtures captured verbatim; `utm.py` is tested with pytest-subprocess
  (`FakeProcess`) and `tmp_path` — no real `utmctl`, no real leases file, no UTM.app.
- **Type gates**: `just typecheck` (basedpyright) and `just check-pyrefly` (empty baseline — new
  code is clean or it doesn't merge) after every phase.
- **Live smoke** (manual, this host): the `utm-up → utm-ip → utm-ssh → utm-destroy` loop, evidence
  in PR notes.
- **Human verdicts**: `just utm-verify-manual` — the iTerm2 UX checklist, JSON-reported per
  session, skips cleanly off-TTY.
- **Truth gate**: `just check` (link-check + verify-claims + unverified-count) after the docs/spec/
  claims step.

## Acceptance Criteria

- `just utm-doctor` reports UTM.app version (via Info.plist), golden bundle presence, and leases
  readability — and `just doctor` still passes on a host with no UTM installed.
- `just utm-up` boots a **windowed** UTM clone and prints an IP that `ssh admin@<ip> true` accepts.
- `just utm-bootstrap-dotfiles` prints a paste-able block that, run in the guest's iTerm2, mounts
  the dotfiles share and applies chezmoi from it.
- `just utm-verify-manual` walks the seven-item iTerm2 UX checklist and writes
  `artifacts/latest/manual-utm.json`.
- `just utm-destroy` removes only the session clone.
- All gates green: `just test`, `just lint`, `just typecheck`, `just check-pyrefly`, `just check`.
- Spec 05 §4.5 and the spec 06 amendments exist with dated observations; the Step 10 claims verify
  via `just verify-claims`.

## Validation Commands

- `just test && just lint && just typecheck && just check-pyrefly` — gates (after every phase)
- `uv run macos-ci utm --help` — sub-app mounted
- `just utm-doctor && just doctor` — optional row never fails tart-only hosts
- `just utm-up && just utm-ip && just utm-exec "true" && just utm-destroy` — live lane smoke
- `just utm-verify-manual` — checklist prompts on a TTY, skips off-TTY
- `just check` — link-check + verify-claims + unverified-count

## Notes

- **Config stays convention-based.** `macos-versions.toml` declares *buildable* tart image lanes;
  the UTM golden is a one-time hand-made artifact with no build pipeline (no Packer builder for UTM
  — settled), so a config entry would be a lie the validator must special-case. Naming convention:
  `dotfiles-golden-utm` / `dotfiles-utm`, env-overridable via `MACOS_CI_UTM_GOLDEN` /
  `MACOS_CI_UTM_VM`. `_config_core.py` untouched.
- **No new dependencies.** `plistlib` and `shlex` are stdlib; pytest-subprocess and the JSON-report
  plumbing already exist in the dev group.
- **Open risks, each with its verification step** (anything untried keeps its
  `<!-- UNVERIFIED -->` until a spike settles it):
  1. Tart disk may be ASIF, not raw → `file disk.img` + `config.json` (Spike A step 1);
     `diskutil image convert` is untried.
  2. Imported disk may not boot (machine-identifier/NVRAM mismatch) → Spike A kill criteria +
     fallback golden.
  3. Shared Network may not write `/var/db/dhcpd_leases` → Spike B step 3; fallback chain
     arp → mDNS → serial, each verified individually.
  4. Leases file may need sudo → `ls -l /var/db/dhcpd_leases` (Spike B step 1).
  5. `config.plist` MAC key path may vary by UTM version → `plutil -p` capture; the parser walks
     recursively rather than hardcoding a key path.
  6. `utmctl clone` naming semantics (AppleScript verb is `duplicate`; the clone may land as
     "Name Copy") → `clone --help` capture + one live clone; add a rename step if needed.
  7. UTM documents dir varies (App Store vs dmg) → locate on this host; `MACOS_CI_UTM_DIR`
     override exists regardless.
  8. VirtioFS tag literal (`share`) and its GUI configurability → run the mount in-guest.
  9. Cloned VMs may share a MAC (does UTM regenerate it on clone?) → clone twice and compare; if
     not regenerated, `utm clone` must warn about concurrent golden-derived clones.
  10. `utmctl --help` might itself launch UTM.app → pgrep before/after (Spike B); affects only
      which claims stay `cli-help` vs move to prose.
