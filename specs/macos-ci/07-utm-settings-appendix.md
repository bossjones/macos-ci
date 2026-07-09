# UTM Settings Pages — Thin Appendix

Owner: 🖥 utm · One row per settings page actually fetched. Depth for anything automation-relevant lives
in `05-utm-automation.md` (AppleScript config fields) and `06-utm-macos-guest.md` (macOS-guest-specific
behavior) — this file is an index, not a restatement.

## Apple backend (`settings-apple/*`) — the backend macOS guests use

| Page | What it covers | Relevant elsewhere |
|---|---|---|
| [boot](https://docs.getutm.app/settings-apple/boot/) | OS selection (macOS 12+ / Linux only); bootloader; Linux-only kernel/ramdisk/boot-args fields; macOS-only IPSW install image field | `06` §1 (IPSW) |
| [drive](https://docs.getutm.app/settings-apple/drive/) | Create/removable/NVMe-interface/import/delete/boot-order/size for drives; macOS 26+ adds Apple Sparse Image format | `06` §5 (`apple drive configuration`) |
| [system](https://docs.getutm.app/settings-apple/system/) | Just CPU core count (0 = host default) and memory size | `06` §5 |
| [information](https://docs.getutm.app/settings-apple/information/) | Name / notes / icon — cosmetic only, identical content to the QEMU equivalent below | — |
| [sharing](https://docs.getutm.app/settings-apple/sharing/) | One or more shared directories, editable from the VM's home-screen details panel too | `06` §3 (VirtioFS/network-share mounting) |

## QEMU backend (`settings-qemu/*`) — not this repo's guest backend, kept for contrast

| Page | What it covers | Relevant elsewhere |
|---|---|---|
| [system](https://docs.getutm.app/settings-qemu/system/) | Architecture, target system, memory, CPU model/cores, JIT cache size | Contrast with `06` §5 — QEMU has no `apple configuration` equivalent constraints |
| [qemu](https://docs.getutm.app/settings-qemu/qemu/) | Logging, UEFI boot, RNG ("entropy") device, balloon device, TPM 2.0, hypervisor/TSO toggles, PS/2 fallback, UEFI variable reset, raw QEMU machine properties/arguments | Notably: "Use TSO... not supported on macOS however when using the Apple virtualization backend, a similar option is available" — that Apple-backend equivalent is undocumented (lives on the 404'd `settings-apple/devices/` page, G10) |
| [sharing](https://docs.getutm.app/settings-qemu/sharing/) | Clipboard sync + shared directories via SPICE WebDAV or VirtFS (QEMU-only mechanisms) | `05` §2.2 contrast — QEMU has richer built-in sharing than Apple backend |
| [input](https://docs.getutm.app/settings-qemu/input/) | USB bus version (2.0 vs 3.0) and USB device-sharing limits | `06` §2 — none of this applies to Apple-backend macOS guests (no USB sharing) |
| [information](https://docs.getutm.app/settings-qemu/information/) | Name / notes / icon — byte-identical content to `settings-apple/information` | — |

## App-level preferences (not a per-VM settings page)

| Page | What it covers | Relevant elsewhere |
|---|---|---|
| [preferences/macos](https://docs.getutm.app/preferences/macos/) | UTM.app-wide preferences: keep-running/dock-icon/menu-bar-icon behavior, screenshot privacy, renderer/sound backend, input-capture behavior (QEMU-only sections marked as such in the source), host-network management, drive-image locking, and the **UTM server** remote-access settings (auto-start, WAN access, listen port, password) | `05` §4 (dock-icon hiding for headless) |

## Pruned — do not fetch, do not cite (G10, confirmed 404 during this research pass)

- `docs.getutm.app/settings-apple/devices/`
- `docs.getutm.app/settings-qemu/devices/devices/`
- `docs.getutm.app/settings-qemu/drive/drive/`
- `docs.getutm.app/guest-support/sharing/sharing/`

The first of these would have documented the Apple-backend per-device toggles (balloon, entropy/RNG,
sound, keyboard/pointer/trackpad, Rosetta, clipboard) referenced obliquely by `settings-qemu/qemu`'s TSO
note above and by `06` §9. That gap is real and is called out at the point of use rather than guessed at
here.
