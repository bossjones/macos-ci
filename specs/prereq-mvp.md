# Plan: MVP prerequisites — recover the UTM golden VM and fix the from-IPSW Packer lane

Owner: 🖥 utm + 📦 packer-builder · Status: ready to execute (Step 1 is ~15 min and unblocks
everything; Step 3 is human-in-the-loop only if Step 1 fails) · Created 2026-07-11.

## Task Description

[`mvp.md`](mvp.md) (the iTerm2-in-UTM hero screenshot) is blocked at Phase B: there was no
`dotfiles-golden-utm` VM, and the attempt to create one on 2026-07-11 — importing the Tart golden's
raw disk into a fresh UTM bundle per [`06-utm-macos-guest.md`](macos-ci/06-utm-macos-guest.md)
§"Importing the tart golden disk" — produced a VM that hangs at a black screen on every boot.
The same session also audited the repo's two Packer templates against the canonical upstream
templates and found the from-IPSW lane's `boot_command` materially broken.

This spec fixes both. It is written so a less-experienced executor (human or model) can run it:
**every step ends with a feedback loop** — a command, the observable that means success, and a
decision table for the other outcomes. No step relies on judgment where a command can answer.

## Objective

1. A `dotfiles-golden-utm` VM that boots to a usable desktop, machine-verified by
   `uv run macos-ci utm ip --vm dotfiles-golden-utm` returning an address.
2. [`packer/ipsw/sequoia-15.6.1.pkr.hcl`](../packer/ipsw/sequoia-15.6.1.pkr.hcl) rewritten to the
   canonical Sequoia `boot_command` + system provisioners, guarded by ledger claims.
3. Docs made honest: the now-settled `<!-- UNVERIFIED -->` at
   [`06-utm-macos-guest.md`](macos-ci/06-utm-macos-guest.md) §"Importing the tart golden disk"
   updated with the observed failure signature and its resolution; the `utm import-golden`
   checklist warns about identity personalization.
4. `just check` green throughout. Then [`mvp.md`](mvp.md) Phase B can run.

## Problem Statement

### P1 — The imported Tart disk hangs in UTM (cause confirmed at three levels, 2026-07-11)

1. **Observed twice** (with and without the NVMe-interface toggle): black screen, UTM process at
   0.0% CPU with 5 threads across repeated samples, and in the unified log the
   `com.apple.Virtualization.VirtualMachine` XPC connection activates and then goes completely
   silent — no error, no progress. The disk itself attaches fine (DiskImages2 log: "assuming RAW
   format").
2. **Byte-compare proof.** Tart stores a VM's Virtualization.framework identity in
   `~/.tart/vms/dotfiles-golden/config.json` as base64 `dataRepresentation` blobs; UTM stores the
   same objects in the bundle's `config.plist` under `System.MacPlatform`. Comparing them:

   | Artifact | tart (`dotfiles-golden`) | UTM bundle (wizard-created) | Equal? |
   |---|---|---|---|
   | hardware model | `hardwareModel`, 132 B decoded | `HardwareModel`, 132 B | **No** |
   | machine identifier (ECID) | `ecid`, 68 B decoded | `MachineIdentifier`, 60 B | **No** |
   | auxiliary storage (NVRAM) | `nvram.bin`, 32 MB | `Data/AuxiliaryStorage`, 32 MB | **No** (freshly generated) |

   The OS on the disk was installed/personalized under tart's (hardwareModel, ECID,
   AuxiliaryStorage) triple; UTM booted it under a freshly generated triple. Result: silent boot
   hang.
3. **External confirmation, verified first-hand** (fetched during the session, not trusted from a
   summary): [utmapp/UTM#3526](https://github.com/utmapp/UTM/issues/3526), comment
   `issuecomment-1150351643` by kFYatek (2022-06-08; the fragment is spelled out because GitHub
   renders comment anchors client-side, where lychee cannot verify them)
   — when the disk image and AuxiliaryStorage are shared between two Virtualization.framework
   frontends **and** `hardwareModel`/`machineIdentifier` are set to the same values in both
   configs, the same VM boots under either tool. The
   [akemin-dayo `virtualapple-utm-link` gist](https://gist.github.com/akemin-dayo/8337d8274deddfefae5d1543420ca0b1)
   demonstrates the same technique (and documents that Virtualization.framework refuses
   **symlinked** disks — hard-links only). Background on UTM's Apple-backend `config.plist`
   structure: [vkhitrin — Creating a UTM VM from CLI](https://blog.vkhitrin.com/creating-a-utm-virtual-machine-from-cli/)
   and [Modifying UTM configuration via CLI](https://blog.vkhitrin.com/modifying-utm-configuration-via-cli/).

   (A Perplexity deep-research report supplied by the owner reached the same conclusion; its
   citations were validated before use here — its one unpinned reference, "a UTM GitHub issue
   from 2022", is the #3526 comment linked above. Its hard-link suggestion is **rejected** for
   this repo: a hard-linked disk means UTM boots would mutate the shared copy.)

### P2 — The from-IPSW Packer lane cannot work as written

[`packer/ipsw/sequoia-15.6.1.pkr.hcl`](../packer/ipsw/sequoia-15.6.1.pkr.hcl)'s `boot_command`
was cribbed from a **Tahoe 26.1** donor but targets **Sequoia 15.6.1**. The canonical donor is
already on this machine: `~/dev/cirruslabs/macos-image-templates/templates/vanilla-sequoia.pkr.hcl`
— the template that builds the very `macos-sequoia-vanilla` image the golden lane clones, pinning
**the exact same 15.6.1 IPSW** (donor line 16). Divergences:

| # | Defect | Severity |
|---|---|---|
| 1 | No post-Setup-Assistant tail: keyboard-nav enable, Sharing → Screen Sharing → **Remote Login**, Gatekeeper disable (donor lines 77-105). A `from_ipsw` guest boots with SSH **off**; Packer's SSH communicator can never connect — every build dies at `ssh_timeout`. | Fatal |
| 2 | Account-creation keystrokes use the Tahoe layout (6 leading `<tab>`s); Sequoia types full-name first, no leading tabs (donor line 46). | Fatal |
| 3 | Country step lacks `<click 'Select Your Country or Region'>` (donor line 36). `<click>` requires plugin ≥ **1.16.0** (verified: `git tag --contains` on the introducing commit); our pin is `>= 1.11.1`. | High |
| 4 | Post-account wait 60s vs donor **120s**; tab-count drifts in Time Zone / Screen Time / Siri / Choose Your Look. | High |
| 5 | `ssh_timeout` 120s vs 180s; `create_grace_time` 23s vs 30s; several waits shortened. | Medium |
| 6 | `recovery_partition = "delete"` vs donor `"keep"` ("otherwise it's not possible to softwareupdate"). | Medium |
| 7 | Stub provisioner: none of the donor's system provisioners (passwordless sudo, auto-login, screensaver/sleep/screen-lock off, safaridriver, Gatekeeper assert, Xcode CLT — donor lines 119-164). | High |

[`packer/tart-golden-image.pkr.hcl`](../packer/tart-golden-image.pkr.hcl) was audited too and is
**correct as-is**: it clones the `-vanilla` base, whose own build already did Setup Assistant,
SSH, and Gatekeeper; its provisioner guards match exactly what vanilla ships (CLT present → skip,
brew absent → install). No change.

Safety check done: no ledger claim or spec pins line numbers inside either Packer file — the
rewrite shifts nothing. Owner decisions already taken: full-parity tail, `recovery_partition = "keep"`.

## Solution Approach

Two independent workstreams, then the MVP resumes:

- **WS-B (golden recovery, blocks the MVP)**: Step 1 transplants tart's identity triple into the
  existing UTM bundle in place (~15 min, scripted, reversible). Step 2 probes whether
  `utmctl clone` preserves the transplanted identity (byte-compare **before** booting). Step 3 —
  only if Step 1 fails — falls back to a fresh macOS install inside UTM (identity native to UTM
  by construction).
- **WS-A (Packer lane fix, pure code, parallel-safe)**: adopt the donor's `boot_command` and
  system provisioners with variable substitutions; bump the plugin pin; fix the timing/settings
  drift; guard with ledger claims.

## Relevant Files

- [`packer/ipsw/sequoia-15.6.1.pkr.hcl`](../packer/ipsw/sequoia-15.6.1.pkr.hcl) — WS-A rewrite target
- [`packer/tart-golden-image.pkr.hcl`](../packer/tart-golden-image.pkr.hcl) — audited, unchanged; reference for the CLT/brew provisioner style
- `~/dev/cirruslabs/macos-image-templates/templates/vanilla-sequoia.pkr.hcl` — the donor (read-only ground truth; lines 24-106 boot_command, 119-164 system provisioners, line 16 the IPSW URL)
- `~/dev/cirruslabs/macos-image-templates/templates/base.pkr.hcl` — proves brew/mise belong to `-base`, not `-vanilla` (keeps software OUT of the ipsw lane)
- [`specs/macos-ci/06-utm-macos-guest.md`](macos-ci/06-utm-macos-guest.md) — §"Importing the tart golden disk": the settled `<!-- UNVERIFIED -->` marker
- [`src/macos_ci/utm.py`](../src/macos_ci/utm.py) — `_IMPORT_CHECKLIST_TEMPLATE` gains the personalization warning
- [`.team/claims.jsonl`](../.team/claims.jsonl) — three new claims (Step 5)
- [`specs/mvp.md`](mvp.md) — gains a one-line cross-link to this spec
- `~/.tart/vms/dotfiles-golden/{config.json,nvram.bin}` — identity donors (read-only)
- `~/Library/Containers/com.utmapp.UTM/Data/Documents/dotfiles-golden-utm.utm/` — transplant target

### New Files

- `specs/prereq-mvp.md` — this spec.

## Implementation Phases

### Phase 1: Foundation (WS-B Steps 1-2 — unblock the MVP fastest)
Identity transplant + clone-identity probe. Scripted, reversible, ~30 min total.

### Phase 2: Fallback (WS-B Step 3 — only if Phase 1's boot oracle fails)
Fresh install inside UTM, human-in-the-loop, ~1-2 h mostly unattended.

### Phase 3: Core code (WS-A Steps 4-5)
Packer ipsw-lane rewrite + ledger claims. Independent of Phases 1-2; can run any time.

### Phase 4: Integration & honesty (Steps 6-7)
Docs updates, cross-link, full `just check`.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom (Step 3 only on Step 1 failure).

### 1. WS-B: transplant tart's identity into the UTM bundle

Run as one block (each guard is a feedback loop; any non-zero exit means STOP at that line):

```bash
set -euo pipefail
BUNDLE="$HOME/Library/Containers/com.utmapp.UTM/Data/Documents/dotfiles-golden-utm.utm"
TARTVM="$HOME/.tart/vms/dotfiles-golden"
UTMCTL="/Applications/UTM.app/Contents/MacOS/utmctl"

# 1a. UTM must be fully quit — editing a bundle UTM has open gets overwritten from its cache.
osascript -e 'quit app "UTM"' 2>/dev/null || true; sleep 3
pgrep -x UTM && { echo "FAIL: UTM still running"; exit 1; } || echo "OK: UTM not running"

# 1b. The tart golden must not be running either (we are about to share its identity).
tart list | grep dotfiles-golden   # expect State: stopped

# 1c. Backups, refuse-to-overwrite (idempotent re-runs keep the ORIGINAL backup).
test -f "$BUNDLE/config.plist.bak" || cp "$BUNDLE/config.plist" "$BUNDLE/config.plist.bak"
test -f "$BUNDLE/Data/AuxiliaryStorage.bak" || cp -c "$BUNDLE/Data/AuxiliaryStorage" "$BUNDLE/Data/AuxiliaryStorage.bak"
test -f "$BUNDLE/config.plist.bak" && test -f "$BUNDLE/Data/AuxiliaryStorage.bak" && echo "OK: backups exist"

# 1d. Transplant HardwareModel + MachineIdentifier, with read-back assertion.
python3 - "$BUNDLE" "$TARTVM" <<'EOF'
import base64, json, plistlib, sys
bundle, tartvm = sys.argv[1], sys.argv[2]
tart = json.load(open(f"{tartvm}/config.json"))
hw, ecid = base64.b64decode(tart["hardwareModel"]), base64.b64decode(tart["ecid"])
path = f"{bundle}/config.plist"
with open(path, "rb") as f: d = plistlib.load(f)
d["System"]["MacPlatform"]["HardwareModel"] = hw
d["System"]["MacPlatform"]["MachineIdentifier"] = ecid
with open(path, "wb") as f: plistlib.dump(d, f)
with open(path, "rb") as f: d2 = plistlib.load(f)     # assert-what-you-wrote
assert d2["System"]["MacPlatform"]["HardwareModel"] == hw, "read-back mismatch: HardwareModel"
assert d2["System"]["MacPlatform"]["MachineIdentifier"] == ecid, "read-back mismatch: MachineIdentifier"
print("OK: identity transplanted and read-back verified")
EOF

# 1e. plist still parses.
plutil -lint "$BUNDLE/config.plist"    # expect: OK

# 1f. AuxiliaryStorage: replace with tart's nvram.bin, byte-verify.
rm -f "$BUNDLE/Data/AuxiliaryStorage"
cp -c "$TARTVM/nvram.bin" "$BUNDLE/Data/AuxiliaryStorage"
cmp "$TARTVM/nvram.bin" "$BUNDLE/Data/AuxiliaryStorage" && echo "OK: AuxiliaryStorage byte-identical"

# 1g. Boot oracle — no GUI eyeballing needed.
open -a UTM; sleep 5
"$UTMCTL" start dotfiles-golden-utm
for i in $(seq 1 36); do
  ip=$(uv run macos-ci utm ip --vm dotfiles-golden-utm 2>/dev/null) && break || sleep 5
done
echo "guest ip: ${ip:-NONE}"
test -n "${ip:-}" && nc -z "$ip" 22 && echo "B1 SUCCESS: booted, DHCP lease present, SSH listening"
```

**Feedback loop / decision table (1g):**

| Observation within 180s | Meaning | Next action |
|---|---|---|
| IP printed, `nc -z` succeeds | B1 confirmed | Step 2 |
| No IP, `top -pid $(pgrep -x UTM) -l 3` shows ~0.0% CPU, and `log show --last 5m --predicate 'process == "UTM"' --debug` shows the VZ XPC connection then silence | The hang signature persists | Roll back (below), go Step 3 |
| No IP, CPU busy / log active | Slow first boot, not a hang | Wait 5 more minutes, re-poll once; then decide by the same table |

**Rollback** (only on failure): quit UTM, `cp "$BUNDLE/config.plist.bak" "$BUNDLE/config.plist"`,
`rm -f "$BUNDLE/Data/AuxiliaryStorage" && cp -c "$BUNDLE/Data/AuxiliaryStorage.bak" "$BUNDLE/Data/AuxiliaryStorage"`,
then `cmp` each against its `.bak` to confirm restoration.

**Standing caveat (record in 06 §import, Step 6):** the transplanted UTM golden and the tart
golden now share a machine identifier. Never boot both simultaneously.

### 2. WS-B: probe whether `utmctl clone` preserves the transplanted identity

`just utm-up` clones the golden before booting, so the lane only works if clones keep the
identity. Cheap probe — compare bytes **before** wasting a boot:

```bash
"$UTMCTL" stop dotfiles-golden-utm --request || true
"$UTMCTL" clone dotfiles-golden-utm --name utm-clone-probe
python3 - <<'EOF'
import plistlib, os, glob
docs = os.path.expanduser("~/Library/Containers/com.utmapp.UTM/Data/Documents")
g = plistlib.load(open(f"{docs}/dotfiles-golden-utm.utm/config.plist", "rb"))
c = plistlib.load(open(f"{docs}/utm-clone-probe.utm/config.plist", "rb"))
gm, cm = g["System"]["MacPlatform"], c["System"]["MacPlatform"]
print("MachineIdentifier preserved:", gm["MachineIdentifier"] == cm["MachineIdentifier"])
print("HardwareModel preserved:", gm["HardwareModel"] == cm["HardwareModel"])
EOF
```

| Byte-compare | Boot-check the clone (same oracle as 1g, `--vm utm-clone-probe`) | Conclusion / action |
|---|---|---|
| Both preserved | boots | `just utm-up` lane works as designed — done |
| Identifier regenerated | (predicted hang — confirm with one boot attempt) | Document in 06; MVP workaround: boot the golden directly for the screenshot session, or re-run Step 1d/1f against the clone bundle after each `utm clone`; optional follow-up: a `utm transplant-identity` helper in `utm.py` (own spec, TDD) |
| Preserved but clone hangs anyway | — | New unknown: capture `log show` signature, record in 06, stop |

Cleanup either way: `"$UTMCTL" delete utm-clone-probe`.

### 3. WS-B fallback (ONLY if Step 1's oracle failed): fresh install inside UTM

No identity juggling — the OS gets personalized under UTM's own triple by construction.

1. Restore backups (Step 1 rollback) or delete and recreate the bundle via UTM's wizard.
   IPSW choice: UTM's cached `~/Library/Containers/com.utmapp.UTM/Data/Library/Caches/UniversalMac_26.5.2_25F84_Restore.ipsw`
   (Tahoe, zero download) — or, for parity with the tart golden's macOS, the Sequoia 15.6.1 IPSW
   the donor template pins (donor line 16; ~13 GB download). **Recommended: Sequoia** — the
   dotfiles are proven on it.
2. Let the install run (~30-45 min unattended). Human drives Setup Assistant **in the UTM
   window** using the donor `boot_command`'s comment lines as the step checklist (create account
   `admin`/`admin`, skip Apple ID / Location / Siri / Screen Time / Analytics).
3. In the guest: System Settings → General → Sharing → enable **Remote Login**.
   *Feedback loop:* `ip=$(uv run macos-ci utm ip --vm dotfiles-golden-utm) && nc -z "$ip" 22`.
4. Over SSH (`ssh admin@$ip`, password `admin`), with an oracle after each block:
   - passwordless sudo (donor provisioner line 122 pattern) → `sudo -n true` exits 0
   - auto-login + screensaver/sleep/screen-lock off (donor lines 126-133, 146) →
     `sudo defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser` prints `admin`
   - Xcode CLT via the golden template's `softwareupdate` pattern
     ([`tart-golden-image.pkr.hcl`](../packer/tart-golden-image.pkr.hcl) lines 91-98) →
     `xcode-select -p` prints a path
   - Homebrew (`NONINTERACTIVE=1`, golden template lines 100-104) → `brew --version`
   - `brew install chezmoi` → `chezmoi --version`
5. Shut down cleanly (`sudo shutdown -h now`), then re-run the Step 1g boot oracle once to prove
   the golden comes back up cold.

### 4. WS-A: rewrite `packer/ipsw/sequoia-15.6.1.pkr.hcl` from the donor

Copy from `~/dev/cirruslabs/macos-image-templates/templates/vanilla-sequoia.pkr.hcl` —
**do not retype from memory**:

- `required_plugins`: `version = ">= 1.16.0"` (comment: `<click>` introduced in v1.16.0).
- `boot_command`: donor lines 24-106 **verbatim**, with exactly these substitutions:

  | Donor text | Replace with |
  |---|---|
  | `Managed via Tart<tab>admin<tab>admin<tab>admin` (line 46) | `${var.ssh_username}<tab>${var.ssh_username}<tab>${var.ssh_password}<tab>${var.ssh_password}` |
  | `admin<enter>` sudo-password lines (95, 102) | `${var.ssh_password}<enter>` |

- Settings: `ssh_timeout = "180s"`, `create_grace_time = "30s"`, `recovery_partition = "keep"`
  (donor's softwareupdate rationale in the comment, noting the deliberate divergence from the
  golden lane's `"delete"`). Keep `disk_format = "raw"` + comment, `disk_size_gb = 120`,
  `headless = true`, `run_extra_args = ["--no-audio"]`, `ipsw_url` with no default.
- Build block: replace the stub with the donor's **system** provisioners (lines 119-164),
  substituting `admin` → `${var.ssh_username}`/`${var.ssh_password}` except the kcpassword hex
  (donor line 126), which stays verbatim **with a comment that the hex encodes the literal
  password `admin`** and is wrong for any other `ssh_password`. Explicitly exclude software
  (brew/mise/agents — that is `base.pkr.hcl` / golden-lane territory, per this file's step-6a
  split).
- Header comment: re-anchor provenance to the local donor path + note it pins the same 15.6.1
  IPSW (line 16); state honestly that the sequence is **adopted from the canonical template but
  not yet observed end-to-end on this host** (a live from_ipsw build is hours and out of scope).

**Feedback loops:** `packer fmt -check packer/ipsw/sequoia-15.6.1.pkr.hcl` (no diff),
`packer init packer/ipsw/sequoia-15.6.1.pkr.hcl`, then
`packer validate -var ipsw_url=/dev/null packer/ipsw/sequoia-15.6.1.pkr.hcl` (exit 0 — validate
resolves the ≥1.16.0 constraint and parses `<click>` without opening the IPSW), and
`grep -c "Remote Login" packer/ipsw/sequoia-15.6.1.pkr.hcl` ≥ 1.

### 5. WS-A: ledger claims

Append to [`.team/claims.jsonl`](../.team/claims.jsonl) (single-line JSONL, matching the file's
existing schema):

```json
{"id": "ipsw-boot-command-enables-remote-login", "kind": "file-contains", "file": "specs/prereq-mvp.md", "target": "packer/ipsw/sequoia-15.6.1.pkr.hcl", "expect": "Remote Login", "claim": "the from_ipsw boot_command carries the canonical Sequoia tail that enables Remote Login -- without it a from_ipsw guest boots with SSH off and Packer's SSH communicator can never connect (the fatal gap found in the 2026-07-11 audit)."}
{"id": "ipsw-boot-command-disables-gatekeeper", "kind": "file-contains", "file": "specs/prereq-mvp.md", "target": "packer/ipsw/sequoia-15.6.1.pkr.hcl", "expect": "spctl --global-disable", "claim": "the from_ipsw boot_command carries the canonical Gatekeeper-disable pass, keeping ipsw-built VMs interchangeable with the cirruslabs vanilla base the golden lane clones."}
{"id": "ipsw-donor-template-pins-same-ipsw", "kind": "file-contains", "local_only": true, "file": "specs/prereq-mvp.md", "target": "/Users/bossjones/dev/cirruslabs/macos-image-templates/templates/vanilla-sequoia.pkr.hcl", "expect": "UniversalMac_15.6.1_24G90_Restore.ipsw", "claim": "the canonical donor template our from_ipsw boot_command is adopted from pins the exact 15.6.1 restore image this lane targets -- the fact that justifies the adoption. File identity is already guarded by CONTROL-vanilla-sequoia-template-is-a-tart-cli-build; reused rather than duplicated."}
```

**Feedback loop:** `just verify-claims` — the three new IDs PASS and the count grows by exactly 3.

### 6. Docs honesty pass

- [`specs/macos-ci/06-utm-macos-guest.md`](macos-ci/06-utm-macos-guest.md), the
  machine-identifier `<!-- UNVERIFIED -->` in §"Importing the tart golden disk": replace with the
  observed record — the 2026-07-11 hang signature (0% CPU; VZ XPC connect-then-silence), the
  byte-compare result, the [utmapp/UTM#3526](https://github.com/utmapp/UTM/issues/3526)
  confirmation (comment `issuecomment-1150351643`), the transplant fix (or Step 3 outcome), and
  the never-boot-both-goldens caveat.
- [`src/macos_ci/utm.py`](../src/macos_ci/utm.py) `_IMPORT_CHECKLIST_TEMPLATE`: add a warning
  line — importing the raw disk alone produces a VM that hangs at boot; the
  hardwareModel/MachineIdentifier/AuxiliaryStorage triple must be transplanted too (cite this
  spec). Code change is a string literal only; `just test` stays green.
- [`specs/mvp.md`](mvp.md): one line under Scope — Phase B requires `dotfiles-golden-utm`;
  its recovery is specified in [`prereq-mvp.md`](prereq-mvp.md).

**Feedback loops:** `just link-check` (every URL above is a markdown link lychee verifies);
`just unverified-count` did not increase; `just lint && just typecheck && just check-pyrefly && just test`.

### 7. Validate everything

Run the full gate; see Validation Commands.

## Testing Strategy

- **WS-B is tested by oracles, not eyeballs**: the boot oracle (`utm ip` + `nc -z 22`), the
  byte-compare probes (identity written, clone identity preserved), and the hang discriminator
  (CPU + unified-log signature). Each step's decision table maps every outcome to an action.
- **WS-A is tested to the limit of what's free**: `packer fmt/init/validate` prove syntax,
  plugin-constraint resolution, and variable interpolation; ledger claims pin the two
  load-bearing boot_command lines forever. The keystroke sequence itself is only provable by a
  live from_ipsw build (hours) — deliberately out of scope, stated in the file header, and
  mitigated by adopting cirruslabs' own monthly-rebuilt template for the identical IPSW.
- **Regression net**: the repo's standing gates (`just lint/typecheck/check-pyrefly/test/check`)
  run after every step that touches the repo.

## Acceptance Criteria

- [x] `uv run macos-ci utm ip --vm dotfiles-golden-utm` prints an address after a cold
      `utmctl start` (via Step 1 or Step 3). *Observed 2026-07-11 via Step 1: resolved to
      `192.168.64.3` and SSH answered — recorded in
      [`utm-improvements.md`](utm-improvements.md) §Context (Spike B resolution).*
- [x] The Step 2 clone-identity outcome is recorded in
      [`06-utm-macos-guest.md`](macos-ci/06-utm-macos-guest.md) whichever way it lands.
      *Recorded in 06 §11: `utmctl clone` preserves the transplanted identity (byte-compared)
      and the clone boots to SSH.*
- [x] `packer/ipsw/sequoia-15.6.1.pkr.hcl` contains the Remote Login and
      `spctl --global-disable` steps, pins plugin ≥ 1.16.0, and passes `packer validate`.
      *Re-run 2026-07-12: `packer fmt -check` clean, `packer validate` exits 0; ledger claims
      pin the two boot_command lines.*
- [x] The three new ledger claims pass; no existing claim regresses. *`just verify-claims`
      green 2026-07-12.*
- [x] The 06 §import `<!-- UNVERIFIED -->` marker about machine identity no longer claims
      ignorance this session disproved. *Replaced by the dated observed record, 06 §11.*
- [x] `just check` exits 0. *Re-run 2026-07-12 after the marker burn-down.*
- [x] [`mvp.md`](mvp.md) Phase B is unblocked (golden exists and boots). *Asserted at
      [`mvp.md`](mvp.md) §Prerequisite; the golden's boot + SSH observation backing it is
      06 §11's dated record.*

## Validation Commands

- `uv run macos-ci utm ip --vm dotfiles-golden-utm` — non-empty ⇒ golden booted + DHCP lease (the WS-B oracle)
- `just utm-up` — end-to-end clone → boot → IP → SSH bootstrap (proves the whole lane, Step 2 permitting)
- `packer fmt -check packer/ipsw/sequoia-15.6.1.pkr.hcl && packer init packer/ipsw/sequoia-15.6.1.pkr.hcl && packer validate -var ipsw_url=/dev/null packer/ipsw/sequoia-15.6.1.pkr.hcl` — WS-A syntax/constraints
- `just lint && just typecheck && just check-pyrefly && just test` — repo gates
- `just check` — link-check + verify-claims (+3 new) + unverified-count, the truth gate

## Notes

- **ECID sharing**: after Step 1 the tart and UTM goldens are the same "machine" to
  Virtualization.framework. Never boot both at once. (Consequences of doing so are unobserved;
  the rule is conservative.)
- **UTM has no CLI config surface** — `utmctl --help` (captured 2026-07-11) offers lifecycle
  verbs only; identity/config edits go through `config.plist` with UTM quit, which is why Step 1
  is a script rather than `utmctl` calls.
- The Tahoe IPSW cached by UTM's wizard
  (`~/Library/Containers/com.utmapp.UTM/Data/Library/Caches/UniversalMac_26.5.2_25F84_Restore.ipsw`)
  survives for Step 3; delete it manually if disk pressure matters and Step 3 was not needed.
- Research provenance: owner-supplied Perplexity report (2026-07-11), validated citation-by-
  citation before incorporation; corrections and rejections noted in P1.
