# UTM Settings Pages — Thin Appendix

Owner: 🖥 utm · One row per settings page actually fetched. Depth for anything automation-relevant lives
in `05-utm-automation.md` (AppleScript config fields) and `06-utm-macos-guest.md` (macOS-guest-specific
behavior) — this file is an index, not a restatement.

## Apple backend (`settings-apple/*`) — the backend macOS guests use

| Page | What it covers | Relevant elsewhere |
|---|---|---|
| [settings-apple (index)](https://docs.getutm.app/settings-apple/settings-apple/) | Section index. States the backend's own positioning: "supports only virtualization and is less mature than QEMU… the only way to run macOS virtualized on Apple Silicon" | [10](10-tart-vs-utm-adr.md) |
| [boot](https://docs.getutm.app/settings-apple/boot/) | OS selection (macOS 12+ / Linux only); bootloader; Linux-only kernel/ramdisk/boot-args fields; macOS-only IPSW install image field | `06` §1 (IPSW) |
| [drive](https://docs.getutm.app/settings-apple/drive/) | Create/removable/NVMe-interface/import/delete/boot-order/size for drives; macOS 26+ adds Apple Sparse Image format | `06` §5 (`apple drive configuration`) |
| [system](https://docs.getutm.app/settings-apple/system/) | Just CPU core count (0 = host default) and memory size | `06` §5 |
| [information](https://docs.getutm.app/settings-apple/information/) | Name / notes / icon — cosmetic only, identical content to the QEMU equivalent below | — |
| [sharing](https://docs.getutm.app/settings-apple/sharing/) | One or more shared directories, editable from the VM's home-screen details panel too | `06` §3 (VirtioFS/network-share mounting) |
| [virtualization](https://docs.getutm.app/settings-apple/virtualization/) | The per-device toggles: balloon, entropy, sound/keyboard/pointer (macOS 12+), trackpad (13+), Rosetta (13+), clipboard sharing — each with its guest-version gate | `06` §9 (full table). Rosetta here is **Linux-guest only**, G7 |
| [devices/devices](https://docs.getutm.app/settings-apple/devices/devices/) | Thin index: how to add/remove a device. TOC only — Display, Network, Serial | `06` §9a |

## QEMU backend (`settings-qemu/*`) — not this repo's guest backend, kept for contrast

| Page | What it covers | Relevant elsewhere |
|---|---|---|
| [system](https://docs.getutm.app/settings-qemu/system/) | Architecture, target system, memory, CPU model/cores, JIT cache size | Contrast with `06` §5 — QEMU has no `apple configuration` equivalent constraints |
| [qemu](https://docs.getutm.app/settings-qemu/qemu/) | Logging, UEFI boot, RNG ("entropy") device, balloon device, TPM 2.0, hypervisor/TSO toggles, PS/2 fallback, UEFI variable reset, raw QEMU machine properties/arguments | Inside the `Use TSO` bullet, verbatim: "This option is not supported on macOS however when using the Apple virtualization backend, **a similar option is available**." UTM thus asserts the Apple-backend equivalent **exists**, then never names it. No page in the 78-page index documents it: [settings-apple/virtualization](https://docs.getutm.app/settings-apple/virtualization/) publishes its own complete section list (8 toggles: balloon, entropy, sound, keyboard, pointer, trackpad, Rosetta, clipboard) and TSO is not among them <!-- UNVERIFIED: the page's silence is proven (ledger: utm-no-tso-toggle-on-apple-virtualization, a must_fail probe with a positive control). Inferring from that silence that no such toggle EXISTS is inference from absence, and stays unverified. See OQ-10 --> |
| [sharing](https://docs.getutm.app/settings-qemu/sharing/) | Clipboard sync + shared directories via SPICE WebDAV or VirtFS (QEMU-only mechanisms) | `05` §2.2 contrast — QEMU has richer built-in sharing than Apple backend |
| [input](https://docs.getutm.app/settings-qemu/input/) | USB bus version (2.0 vs 3.0) and USB device-sharing limits | `06` §2 — none of this applies to Apple-backend macOS guests (no USB sharing) |
| [information](https://docs.getutm.app/settings-qemu/information/) | Name / notes / icon — byte-identical content to `settings-apple/information` | — |

## App-level preferences (not a per-VM settings page)

| Page | What it covers | Relevant elsewhere |
|---|---|---|
| [preferences/macos](https://docs.getutm.app/preferences/macos/) | UTM.app-wide preferences: keep-running/dock-icon/menu-bar-icon behavior, screenshot privacy, renderer/sound backend, input-capture behavior (QEMU-only sections marked as such in the source), host-network management, drive-image locking, and the **UTM server** remote-access settings (auto-start, WAN access, listen port, password) | `05` §5 (dock-icon hiding for headless) |

## Dead links — none

Every UTM docs URL used by `05`, `06` and `07` returns HTTP 200 — all 32 of them, re-checked this run with
`curl -sS -o /dev/null -w '%{http_code}'`, and all 20 distinct page paths are present in UTM's own
78-page search index.

The path `docs.getutm.app/settings-apple/devices/` does 404, but it was never a published page — it is a
malformed URL. The real Devices page is
[settings-apple/devices/devices/](https://docs.getutm.app/settings-apple/devices/devices/), under the
[settings-apple/settings-apple/](https://docs.getutm.app/settings-apple/settings-apple/) index.

**The rendered nav is not a page list; the search index is.** UTM's sidebar shows a `Port Forwarding` entry
beneath *Settings (Apple) → Devices*, which invites a citation to a nonexistent Apple-backend page. Its
`href` in fact points at the **QEMU** page
[settings-qemu/devices/network/port-forwarding/](https://docs.getutm.app/settings-qemu/devices/network/port-forwarding/);
both plausible Apple-side URLs (`/settings-apple/devices/network/port-forwarding/` and
`/settings-apple/devices/port-forwarding/`) return **404** and appear nowhere in the index. This was checked
precisely because it *looked* like a hole in the index oracle. It is not one — it is an upstream nav bug,
and the index held. Confirming that mattered: the `doc-index` evidence kind, and the control that guards it,
both rest on "absence from the index is proof of fabrication."

The research brief's **G10** listed three further URLs as 404 and forbade fetching them. All three are
live. They were pruned on a false premise and are now indexed above and in `11-sources.md`:

| URL | Claimed | Actual |
|---|---|---|
| [settings-qemu/devices/devices/](https://docs.getutm.app/settings-qemu/devices/devices/) | 404 | 200 — thin index (Display, Network, Serial, Sound) |
| [settings-qemu/drive/drive/](https://docs.getutm.app/settings-qemu/drive/drive/) | 404 | 200 — meaty: creation, import, boot order, interface, image type, raw images |
| [guest-support/sharing/sharing/](https://docs.getutm.app/guest-support/sharing/sharing/) | 404 | 200 — index over Clipboard / Directory / USB sharing |

Full retraction, with the content that was recoverable, is in
[11-sources.md](11-sources.md#retraction--the-g10-prune-list-was-wrong).
