# UTM Automation Surface

Owner: 🖥 utm · Sources cited inline; full list in [`11-sources.md`](11-sources.md).

## 1. There is no UTM IaC — the automation surface is AppleScript/JXA + a URL scheme

UTM has **no Terraform provider, no Packer builder, and no declarative "machines-as-code" tool**.
The maintainer confirmed this directly. In [utmapp/UTM#3618](https://github.com/utmapp/UTM/discussions/3618),
a user (`lucendio`, Feb 2022) proposed exactly this — a Vagrant/Terraform-style workflow for UTM — and
walked through why neither fits cleanly: Vagrant needs a custom box format and per-provider image
maintenance; Terraform/Pulumi "lack... essential use cases: explicitly start or stop machines — without
creating or destroying them" and can only reach that behavior indirectly by editing config and
re-applying. UTM maintainer `osy` replied (Apr 27, 2022): **"There are plans for this in #3718 but
that's still a long way off."** ([issue #3718](https://github.com/utmapp/UTM/issues/3718) is the tracked
IaC-support request; still open as of this writing.)

So today, UTM automation means one of two things:

1. **AppleScript/JXA**, via `osascript`/`utmctl`-style scripting against the `UTM` scripting dictionary
   ([scripting/reference](https://docs.getutm.app/scripting/reference/)), or
2. The **`utm://` URL scheme** ([advanced/remote-control](https://docs.getutm.app/advanced/remote-control/)),
   which is coarser (start/stop/pause/resume/sendText/click/downloadVM) but scriptable from Shortcuts,
   Automator, or a plain `open "utm://..."` shell call.

There is **no Packer builder for UTM** — `packer-plugin-tart` (covered in `01`/`02`) is Tart-only. This
repo's UTM lane therefore cannot use the golden-image-via-Packer pattern the Tart lane uses; UTM VMs are
built and configured by hand or by AppleScript, not from a repeatable build pipeline.

## 2. The AppleScript scripting dictionary

Source: [scripting/reference](https://docs.getutm.app/scripting/reference/) (the "UTM.sdef" dictionary,
rendered as HTML). Five suites:

### 2.1 UTM Suite — application + VM lifecycle

Top-level `application` object contains `virtual machines`. Key verbs:

| Verb | Signature | Notes |
|---|---|---|
| `make` | `make new «virtual machine» with properties {...}` | Must specify `backend` (`apple`/`qemu`); QEMU VMs must also specify `architecture` in the configuration. |
| `start` | `start vm [saving boolean] [recovery boolean]` | `saving` defaults `true`; `recovery` defaults `false` (macOS 1TR — see `06`). |
| `suspend` | `suspend vm [saving boolean]` | Suspend-to-memory; `saving` (persist to disk) defaults `false`. |
| `stop` | `stop vm [by force/kill/request]` | `force` = ask backend to stop; `kill` = terminate backend process; `request` = guest-OS power-down request (may be ignored). |
| `delete` | `delete vm` | **No confirmation dialog** — irreversible. |
| `duplicate` | `duplicate vm [with properties record]` | Copies VM + all data; only the configuration can be changed on duplicate. |
| `import` / `export` | `import new «virtual machine» from file` / `export vm to file` | Round-trips a `.utm` package. |

Backend enum: `apple` (Virtualization.framework) / `qemu` / `unavailable`. Status enum: `stopped` /
`starting` / `started` / `pausing` / `paused` / `resuming` / `stopping`. Stop-method enum: `force` /
`kill` / `request`. A `virtual machine` also contains `serial ports` (interface enum `ptty` / `tcp` /
`unavailable`).

### 2.2 UTM Guest Suite — file I/O and command execution

> **"In order to use these commands, QEMU guest agent must be running."**
> — [scripting/reference](https://docs.getutm.app/scripting/reference/), verbatim, at the top of the
> UTM Guest Suite section.

This is the single most consequential fact in this file. The Guest Suite is what provides `open file`
(read/write/pull/push on a guest path), `execute` (run a command, optionally capturing stdout/stderr),
and `query ip` (list guest network interfaces). **All of it is gated on the QEMU guest agent** — a
component that ships for QEMU-backend Linux/Windows guests, not for Apple-backend macOS guests. The
cheat-sheet's own example commands for this suite (`--- QEMU guest agent must be installed` /
`set vm to virtual machine named "Ubuntu"`) target a QEMU Linux VM, not a macOS one
([scripting/cheat-sheet](https://docs.getutm.app/scripting/cheat-sheet/)).

**Consequence for this repo: AppleScript-driven "push dotfiles repo into the VM, run chezmoi, pull back
results" does not work against a macOS (Apple-backend) guest.** The doc never states an Apple-backend
equivalent guest agent for exec/file-I/O exists. This is a real gap, not an oversight in this spec —
`08-dotfiles-test-harness.md` (harness's file) must route guest interaction through **SSH + a VirtioFS
shared mount** instead (see `06`), not through UTM's own scripting guest-exec.

Guest Suite verb reference (for completeness, and for any future QEMU-backend Linux/Windows lane):

- `open file at <path> [for reading/writing/appending] [updating] → guest file` (48 MB read limit; base64
  option for binary data).
- `execute at <path/cmd> [with arguments] [with environment] [using input] [output capturing] → guest process`.
- `query ip → list of text` (IPv4 before IPv6).
- `guest file` responds to `read`/`pull`/`write`/`push`/`close`; `guest process` responds to `get result`
  (`exited`, `exit code`, `signal code`, `output text`/`error text`, `output data`/`error data`).

### 2.3 UTM Configuration Suite — read/write VM config

`configuration of vm` returns either a `qemu configuration` or an `apple configuration` record;
`update configuration of vm with <config>` writes it back (**VM must be stopped**; backend cannot be
changed this way). The two configuration shapes diverge meaningfully — see `06` for the full
`apple configuration` field list (this repo's guest type). The `qemu configuration` additionally exposes
`hypervisor`, `uefi`, `directory share mode` (`none`/`WebDAV`/`VirtFS`), and per-drive `interface`
(IDE/SCSI/SD/MTD/Floppy/PFlash/VirtIO/NVMe/USB) — none of which apply to the Apple backend.

### 2.4 UTM USB Devices Suite

`connect`/`disconnect` a host USB device to/from a running VM. **Not all backends support USB sharing** —
and per `06` (citing [guest-support/macos](https://docs.getutm.app/guest-support/macos/)), the Apple
backend used for macOS guests is one of the backends that does not.

### 2.5 UTM Registry Suite

`registry of vm` (list of files) / `update registry of vm with <list>` — "Currently you can only change
the shared directory with this!" per the reference doc. Thin surface, but it's the scriptable way to
change a running VM's shared-directory registry entry without going through Configuration Suite.

### 2.6 UTM Input Automation Suite — QEMU backend only

`input scan code` / `input keystroke` / `input mouse click` — the suite header states plainly:
**"Only supported on QEMU backend."** Same consequence as 2.2: this cannot be used to drive a macOS
Apple-backend guest's UI programmatically. (The `utm://sendText` and `utm://click` URL-scheme actions —
§4 below — carry no equivalent written restriction in
[advanced/remote-control](https://docs.getutm.app/advanced/remote-control/); whether they work against
an Apple-backend macOS guest is <!-- UNVERIFIED --> from the docs alone.)

## 3. Cheat-sheet snippets

Source: [scripting/cheat-sheet](https://docs.getutm.app/scripting/cheat-sheet/). Reproduced (and
corrected for backend applicability) below.

**List / find VMs** (backend-agnostic):
```applescript
tell application "UTM"
    -- listing virtual machines
    set vms to virtual machines
    -- get vm by name
    set vm to virtual machine named "Ubuntu"
    -- get vm by id
    set vm to virtual machine id "5D419106-2824-4FED-BFE1-24A7F7E253D8"
end tell
```

**Control VMs** (backend-agnostic, except "start without saving" — see G5):
```applescript
tell application "UTM"
    set vm to virtual machine named "Ubuntu"
    start vm                     -- start a vm
    start vm without saving      -- disposable mode: QEMU BACKEND ONLY (G5) — will not work for a macOS guest
    suspend vm                   -- pause a vm
    suspend vm with saving       -- pause + persist state (when supported)
    stop vm                      -- stop a vm
    stop vm by force             -- force shutdown
    stop vm by kill              -- kill the vm process
end tell
```

**Creating a VM** (shows both backends; Apple example is the macOS-relevant one for `06`):
```applescript
tell application "UTM"
    set iso to POSIX file "/path/to/ubuntu.iso"
    -- QEMU ARM64 VM with a single 64GiB drive
    set vm to make new virtual machine with properties {backend:qemu, configuration:{name:"QEMU ARM64", architecture:"aarch64", drives:{{removable:true, source:iso}, {guestsize:65536}}}}
    -- default options for a new VM: no display, one PTTY serial port, one shared network
    -- Apple backend VM for booting Linux (macOS 13+ only per this example's own comment)
    make new virtual machine with properties {backend:apple, configuration:{name:"Apple Linux", drives:{{removable:true, source:iso}, {guestsize:65536}}}}
end tell
```

**Deleting a VM** (no confirmation):
```applescript
tell application "UTM"
    delete virtual machine named "Ubuntu"
end tell
```

**Status / information** (backend-agnostic):
```applescript
tell application "UTM"
    set vm to virtual machine named "Ubuntu"
    start vm
    repeat
        if status of vm is started then exit repeat
    end repeat
    get status of vm                              -- e.g. "started"
    get address of first serial port of vm         -- e.g. "/dev/ttys011"
    get item 1 of (query ip of vm)                 -- QEMU guest agent required — see 2.2
end tell
```

**Configuration** (backend-agnostic mechanism; field names differ apple vs qemu, see `06` §5):
```applescript
tell application "UTM"
    set vm to virtual machine named "Ubuntu"
    set config to configuration of vm
    get architecture of config                     -- qemu configuration only
    set hypervisor of config to false               -- qemu configuration only
    set i to id of item 1 of drives of config
    set item 1 of drives of config to {id:i, source:iso}
    update configuration of vm with config          -- VM must be stopped
end tell
```

**Read/write files & Execute commands** — **QEMU guest agent required (2.2); not applicable to a
macOS Apple-backend guest.** Reproduced for the QEMU-Linux lane only:
```applescript
tell application "UTM"
    set vm to virtual machine named "Ubuntu"
    tell (open file of vm at "/tmp/hello" for reading)
        read for length 2 without closing
        read at offset -2 from end position for length 2 without closing
        close
    end tell
    tell (open file of vm at "/tmp/hello" for writing)
        write data "njq81XwLTBF2eOzTuMZfrg==" with base64 encoding without closing
        close
    end tell
    set output to POSIX file "/path/to/output"
    pull of (open file of vm at "/tmp/hello") to output
    set input to POSIX file "/path/to/input"
    push of (open file of vm at "/tmp/hello" for writing) from input
end tell

tell application "UTM"
    set vm to virtual machine named "Ubuntu"
    execute of vm at "wget" with arguments {"http://example.com"}
    tell (execute of vm at "ls" with arguments {"-l", "/"} with output capturing)
        set res to get result
        -- poll res's `exited` until true, then read outputTextOf res
    end tell
end tell
```

**USB devices** (not supported on Apple backend — 2.4):
```applescript
tell application "UTM"
    set device to first usb device
    set vm to virtual machine named "Ubuntu"
    connect device to vm
    disconnect device
end tell
```

**Input automation** — **QEMU backend only (2.6)**:
```applescript
tell application "UTM"
    set vm to virtual machine named "Ubuntu"
    input scan code of vm codes {35, 163, 18, 146, 38, 166, 38, 166, 24, 152}   -- 'hello' as raw scan codes
    input keystroke of vm text "hello" with modifiers shift
    input mouse click of vm at {50, 50} with mouse button left
end tell
```

## 4. Headless operation

Source: [advanced/headless](https://docs.getutm.app/advanced/headless/).

- Headless mode runs a VM in the background; **UTM.app itself must stay open** while it runs.
- Setup: open the VM configuration, **delete any display device**, and delete any serial device set to
  "Built-in Terminal" mode. It is "highly recommended" to keep at least one serial device in a
  non-terminal mode so you still have a way to talk to the guest (see `06` §6 for serial on macOS
  guests).
- Control a headless VM through the AppleScript interface (§2) or the `utm://` scheme (§5).
- macOS 13+: you can additionally hide the Dock icon for a headless-only workflow
  ([preferences/macos](https://docs.getutm.app/preferences/macos/): "Show dock icon" — disabling it
  requires the menu-bar icon to stay enabled so UTM keeps running with all windows closed).

## 5. The `utm://` URL scheme

Source: [advanced/remote-control](https://docs.getutm.app/advanced/remote-control/).

Opening a `utm://` URL (Safari, Shortcuts "Open URL", Automator, or a shell `open` call) launches/
foregrounds UTM and dispatches the command. All parameters must be URL-encoded (spaces → `%20`, etc.).

| Command | Params | Effect | ⚠️ improper shutdown risk |
|---|---|---|---|
| `start` | `name` | Start VM if not already running | — |
| `stop` | `name` | Stop VM **immediately** | ⚠️ yes |
| `restart` | `name` | Stop then start | ⚠️ yes |
| `pause` | `name` | Pause (not all VMs support it) | — |
| `resume` | `name` | Un-pause | — |
| `sendText` | `name`, `text` | Type `text` as keyboard input into the VM | — |
| `click` | `name`, `x`, `y`, optional `button` (`left`/`middle`/`right`, default left) | Mouse click at pixel coords | — |
| `downloadVM` | `url` (must be a `.zip` of a `.utm` package) | Download + extract + import | — |

Example: `utm://start?name=Ubuntu%2020.04`. `sendText` supports ASCII control codes, e.g. Esc = `%1b`,
Backspace = `%08`, Tab = `%09`, Enter = `%0D`.

Two documented automation recipes build on this scheme:

- **Shortcuts** (macOS 12+ / iOS): a Shortcut with a "URL" action (`utm://start?name=...`) + "Open URLs"
  action; add the Shortcut to the Dock, then to Login Items, to auto-start a VM at login.
- **Automator** (macOS 11): a workflow of "Get Specified Text" (the `utm://` URL) → "Extract URLs from
  Text" → "Display Webpages"; add to Login Items the same way.

Both are GUI-login-session automations, not headless/CI-friendly — they assume an interactive user
session, which is consistent with the House Stance (`10`) that UTM is the interactive escape hatch, not
the CI driver.

## 6. Summary: what UTM automation can and cannot do for a macOS guest

| Capability | Works for Apple-backend macOS guest? | Mechanism |
|---|---|---|
| Start/stop/suspend/resume/delete/duplicate | Yes | AppleScript UTM Suite (§2.1) or `utm://` (§5) |
| Read/write config (CPU/memory/drives/network/serial/display) | Yes | AppleScript UTM Configuration Suite, `apple configuration` record (§2.3, detailed in `06` §5) |
| Recovery-mode boot (1TR) | Yes (macOS 13+) | `start vm with recovery` or GUI action menu — see `06` §4 |
| File push/pull, remote command exec, guest IP query | **No** | Guest Suite requires QEMU guest agent (§2.2) — use SSH + VirtioFS instead (`06` §3) |
| Scripted keystrokes / mouse clicks | **No** (AppleScript path) / <!-- UNVERIFIED --> (`utm://` path) | Input Automation Suite is QEMU-only (§2.6) |
| USB device passthrough | **No** | Apple backend doesn't support USB sharing (§2.4, `06` §2) |
| Disposable ("run without saving") mode | **No** — G5 | QEMU backend only |
| Declarative create/destroy (Terraform-style) | **No** — G1 | No IaC exists; tracked in #3718, "a long way off" |
