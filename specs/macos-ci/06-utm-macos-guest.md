# UTM macOS Guest Support

Owner: 🖥 utm · Sources cited inline; full list in [`11-sources.md`](11-sources.md).

macOS guests in UTM run **only** under the **Apple Virtualization.framework backend** ("Apple backend"),
never under QEMU. That single fact drives every limitation in this file — the Apple backend is a much
thinner virtualization surface than QEMU, and several of UTM's flagship features (disposable mode,
guest-exec scripting, multi-display, USB passthrough) are QEMU-only and therefore **do not exist for a
macOS guest, full stop.**

## 1. Requirements and installation

Source: [guest-support/macos](https://docs.getutm.app/guest-support/macos/).

- **macOS 12+** guests are supported, and **only on Apple Silicon hosts** — there is no Intel-host path
  for a macOS guest.
- In the New VM wizard: choose **Virtualization** → **macOS 12+**. ("If either option is not available,
  your system does not support macOS guests.")
- **IPSW**: Apple ships macOS as an IPSW image. UTM can auto-download the latest compatible IPSW, or you
  can supply one from a third-party mirror like [ipsw.me]. UTM's own docs are explicit that they "do not
  attest to the safety, validity, or compatibility of IPSWs downloaded from third party sites" and
  recommend the automatic download path.
- Recovery mode boots from the same IPSW-provisioned system (§4).

## 2. What the Apple backend does *not* support

Source: [guest-support/macos](https://docs.getutm.app/guest-support/macos/) §"Missing features", plus
the dedicated pages below. This is the master gap list for macOS guests:

| Missing feature | Since when is it fixed (if ever) | Citation |
|---|---|---|
| USB sharing | Never (as of this doc) | guest-support/macos |
| Clipboard sharing | Fixed in macOS 15+ (both host and guest) | guest-support/macos §"Clipboard Sharing" |
| Dynamic display resolution | Fixed in macOS 14+ | guest-support/macos; [guest-support/dynamic-resolution](https://docs.getutm.app/guest-support/dynamic-resolution/) |
| Save states (suspend-to-disk) | Fixed in macOS 14+ | guest-support/macos |
| **Disposable ("run without saving") mode** | **Never — QEMU backend only (G5)** | [advanced/disposable](https://docs.getutm.app/advanced/disposable/): "Disposable mode is only supported on QEMU backend." |
| **Multiple graphical displays** | **Never** on Apple backend | [advanced/multiple-displays](https://docs.getutm.app/advanced/multiple-displays/): "macOS Apple backend (macOS guests) does not support multiple graphical displays." |
| Scripted guest file I/O / command exec | Never documented | `05-utm-automation.md` §2.2 — requires QEMU guest agent. **`utmctl exec` / `file` / `ip-address` are these same primitives under a CLI skin (`05` §4.2); finding them in `--help` is not a counterexample.** |
| Scripted keystrokes / mouse (AppleScript Input Automation Suite) | Never — QEMU backend only | `05-utm-automation.md` §2.6 |

Two of these are GROUND TRUTHS worth restating plainly because they kill obvious-seeming designs for this
repo:

- **G5 — no disposable mode for a macOS guest.** The "spin up a throw-away VM per dotfiles test run"
  pattern that disposable mode would give you for free on QEMU **does not exist** for macOS. The harness
  (`08`) must use `tart clone`-per-run (Tart lane) or manual `duplicate`/`delete` around a golden UTM
  image (UTM lane) instead — see `08` for the actual design.
- **G6 — no multi-display for a macOS guest.** Any plan involving multiple screens/heads for a macOS
  guest is a non-starter on the Apple backend.

Also note (not a ground truth, but adjacent and easy to conflate): **Rosetta (`advanced/rosetta`) is
about running x86_64 ELF binaries inside a *Linux* guest on Apple Silicon** (G7) — it is unrelated to
macOS-guest support and is not covered further in this file.

## 3. Shared directories — the real automation channel

Since UTM's own AppleScript guest-exec doesn't reach a macOS guest (`05` §2.2) — and neither does
`utmctl exec`, which is a wrapper around it (`05` §4.1) — shared directories + network access are what a
macOS-guest automation harness actually has to work with.

### 3.1 VirtioFS (macOS 13+ host *and* guest)

Source: [guest-support/macos](https://docs.getutm.app/guest-support/macos/) §"VirtioFS".

When **both** host and guest are macOS 13+, a shared directory is mounted as a network volume from
inside the guest's Terminal:

```
$ mkdir -m 777 -p [mount point]
$ mount_virtiofs share [mount point]
```

(`[mount point]` can be any path, e.g. `/Volumes/Share`.) Unmount with `umount [mount point]` or via
Finder. The docs show this as a manual, per-boot Terminal command — **no fstab/launchd example is given
for auto-mounting on a macOS guest.** The contrast is exact: [advanced/rosetta](https://docs.getutm.app/advanced/rosetta/)
*does* publish a persistent recipe (`rosetta /media/rosetta virtiofs ro,nofail 0 0` in `/etc/fstab`) — but
for a **Linux** guest (G7). Treat persistent auto-mount on the macOS guest side as
<!-- UNVERIFIED: undocumented, not impossible; proving persistence needs a guest reboot. See OQ-11 --> and,
if needed, solve it with a login item or LaunchAgent the harness provisions itself, not something UTM
documents.

### 3.2 Network file sharing (works down to macOS 12)

Source: same page, §"Network sharing". For a macOS 12 guest (VirtioFS above requires 13+ on both ends),
the fallback is host-side **macOS file sharing** (System Settings → Sharing), which the guest can mount
like any other network Mac. Slower to script than VirtioFS, but works across the wider macOS 12+ guest
range.

### 3.3 The practical harness pattern

Combine §3 with an SSH server enabled on the guest (via the same shared-directory bootstrap, or manually
provisioned into the golden image): **shared directory in, SSH command out.** This replaces the
non-existent UTM guest-exec primitive. Full harness design in `08-dotfiles-test-harness.md`.

## 4. Recovery mode (1TR)

Source: [advanced/recovery](https://docs.getutm.app/advanced/recovery/).

- **macOS 13+ only**, and **Apple-backend only**.
- Action menu → **"Run Recovery"** (equivalent to AppleScript `start vm with recovery` — `05` §2.1) boots
  into **1TR (One True Recovery)** mode.
- Used for advanced settings changes such as **disabling System Integrity Protection (SIP)**.
- Distinct from the missing-features list in §2 — recovery mode is a supported, documented capability of
  the Apple backend.

## 5. `apple configuration` — the full field reference

Source: [scripting/reference](https://docs.getutm.app/scripting/reference/), `apple configuration`
record and its sub-records (this is the backend-specific detail promised in `05` §2.3).

| Field | Type | Notes |
|---|---|---|
| `name` | text | VM name |
| `icon` | text | VM icon |
| `notes` | text | User notes |
| `memory` | integer | RAM in MiB |
| `cpu cores` | integer | `0` = host default (performance cores on Apple Silicon) |
| `directory shares` | list of `apple directory share configuration` | See below |
| `drives` | list of `apple drive configuration` | See below |
| `network interfaces` | list of `apple network configuration` | See below |
| `serial ports` | list of `apple serial configuration` | See below |
| `displays` | list of `apple display configuration` | See below |

**`apple directory share configuration`**: `index` (position; empty = create new), `read only` (r/o
boolean).

**`apple drive configuration`**: `id` (r/o, empty = new drive), `removable` (r/o, fixed at creation),
`host size` (r/o, MiB as seen by host), `guest size` (MiB as seen by guest), `source` (file).

**`apple network configuration`**: `index`, `mode` (`shared` | `bridged` — **note: no `emulated`/`host`
modes here, unlike QEMU**), `address` (MAC, random if empty), `host interface` (bridged mode only).

**`apple serial configuration`**: `index`, `interface` (`ptty` / `tcp` / `unavailable` — but **"only PTTY
is supported"** per the doc's own parenthetical, unlike QEMU which supports both).

**`apple display configuration`**: `id` (r/o, empty = new display), `dynamic resolution` (boolean — this
is the macOS 14+ feature from §2).

Compare against the `qemu configuration` record (documented in `05` §2.3) if a future Linux-guest lane is
added — the two configuration shapes are **not** interchangeable, and `update configuration` cannot
change a VM's backend.

## 6. Serial console access

Source: [advanced/serial](https://docs.getutm.app/advanced/serial/).

Serial device emulation works via **pseudo-TTY (both backends)** or **network socket (QEMU backend
only)**. For a macOS guest (Apple backend, PTTY-only per §5), connect from the host with:

```
$ screen /dev/ttys006
```

(device path is whatever `get address of first serial port of vm` returns — `05` §3, "Status /
information" snippet). This is the same serial device that headless mode (`05` §5) requires you to keep
configured in a non-"Built-in Terminal" mode so you retain a way to talk to a display-less macOS guest.

`utmctl attach <vm> [--index N]` is the CLI path to this same serial console (`05` §4.2). It reads the
*host* end of the port, so — unlike `utmctl exec` / `file` / `ip-address` — it needs no guest agent, and
is the **only** guest-facing channel `utmctl` offers an Apple-backend macOS guest.

## 7. Dynamic resolution (macOS 14+ guest)

Source: [guest-support/dynamic-resolution](https://docs.getutm.app/guest-support/dynamic-resolution/).

- Supported on **QEMU backend with guest tools installed**, or on **Apple backend running macOS 14+**.
- For the Apple-backend macOS case specifically: "When you resize the virtual machine window, it should
  automatically request to the guest agent to change the resolution to match that size" — no manual
  guest-side step is documented (unlike the Linux `xrandr` workaround the same page describes for a
  QEMU guest bug).
- Toggle lives on the `apple display configuration` record's `dynamic resolution` boolean (§5), or in the
  GUI as "Auto resolution" per the same source.

## 8. Clipboard sharing (macOS 15+ guest and host)

Source: [guest-support/macos](https://docs.getutm.app/guest-support/macos/) §"Clipboard Sharing".

1. Both host and guest must be macOS 15+.
2. Enable in VM settings: **Virtualization → Enable Clipboard Sharing**.
3. Start the VM, then mount and run **"Install Guest Tools"** from the CD button in the toolbar.
4. Approve the two macOS prompts to allow **`spice-vdagent`** and **`spice-vdagentd`** to run.

Note this "Install Guest Tools" package is **not** the QEMU guest agent from `05` §2.2 — it is a
SPICE-clipboard-only agent, scoped to clipboard sync, and does not unlock AppleScript guest-exec or file
I/O. Don't conflate the two when reading "guest tools" elsewhere in the docs.

## 9. Apple-backend virtualization device toggles

Source: [settings-apple/virtualization](https://docs.getutm.app/settings-apple/virtualization/). Each
toggle is gated on a **guest** macOS version; the label in the source page is the minimum guest release.

| Toggle | Gate | What the source says |
|---|---|---|
| Balloon Device | — | Lets a guest with supported drivers request RAM from the host more intelligently. "Highly recommended." |
| Entropy Device | — | Used by supported guests for cryptographic tasks. |
| Sound | macOS 12+ | Sound for macOS guests, or macOS 13+ Linux guests booting from UEFI. |
| Keyboard | macOS 12+ | Keyboard for macOS guests, or macOS 13+ Linux guests booting from UEFI. |
| Pointer | macOS 12+ | Pointer for macOS guests, or macOS 13+ Linux guests booting from UEFI. |
| Trackpad | macOS 13+ | Emulates a trackpad; **requires a Ventura or higher guest**. Enables trackpad gestures. |
| Rosetta | macOS 13+ | Defers to [advanced/rosetta](https://docs.getutm.app/advanced/rosetta/) — **Linux guests only (G7)**, see below. |
| Clipboard Sharing | — | The source's own note is about **Linux** guests: install `spice-vdagent` on a UEFI-booting Linux guest. |

Two traps on this page, both of which invite a misreading:

- **Rosetta appears in the Apple-backend settings list but is not a macOS-guest feature.** The page
  itself only links out to `advanced/rosetta`, which scopes Rosetta to running x86_64 ELF binaries in
  **Linux** guests (**G7**). Its presence here means "the Apple backend exposes this toggle," not "macOS
  guests can use it."
- **The "Clipboard Sharing" toggle on this page and macOS-guest clipboard sharing are different
  things.** The page's prose covers the Linux/`spice-vdagent` path. The macOS-guest clipboard procedure
  (macOS 15+ host *and* guest, Install Guest Tools) is in §8 above, sourced from `guest-support/macos`.

This section supersedes an earlier claim that these toggles were undocumented. They were documented all
along, at a URL absent from the research brief — see the retraction note in
[11-sources.md](11-sources.md#retraction--the-g10-prune-list-was-wrong).

## 9a. Settings pages not covered here

`settings-apple/boot`, `settings-apple/drive`, `settings-apple/system`, `settings-apple/information`, and
`settings-apple/sharing` are summarized in the thin appendix, `07-utm-settings-appendix.md`, rather than
duplicated in this file. Everything this spec states about Apple-backend device behavior (clipboard in
§8, dynamic resolution in §7, serial in §6, device toggles in §9) is sourced from a live page. The whole
section is indexed at
[settings-apple/settings-apple/](https://docs.getutm.app/settings-apple/settings-apple/), whose own
summary is worth quoting: *"Apple Virtualization backend supports only virtualization and is less mature
than QEMU. It is the only way to run macOS virtualized on Apple Silicon."*

The path `docs.getutm.app/settings-apple/devices/` 404s, but it is a **malformed URL that was never
published** — not a dead page. The Devices page lives at
[settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/), a thin index
covering only how to add/remove Display, Network, and Serial devices.

## 10. Out of scope

[guides/classic-macos](https://docs.getutm.app/guides/classic-macos/) documents emulating **classic Mac
OS on 68k (Quadra 800) / PPC (Power Macintosh G4) hardware** — a completely different, QEMU-emulated
target unrelated to the macOS 12+ Apple-backend guest this repo cares about. Noted only to explain why it
is excluded.
