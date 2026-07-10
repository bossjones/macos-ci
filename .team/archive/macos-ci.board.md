# macos-ci-specs — Status Board

Workspace: `workspace:9` (B3512F3A-19C3-4EC9-BEE3-E3964F187C57) · Window: `window:1`

| Agent | Surface | State | n/N | Last log |
|---|---|---|---|---|
| 👑 lead | surface:37 | 🟢 DONE | 6/6 | review passed, plan-format contract verified, board green |
| 🍎 tart-core | surface:42 | 🟢 DONE | 2/2 | TASK-DONE: wrote 01-tart-core.md + 02-packer-tart-builder.md, no conflicts |
| 🏭 tart-ci | surface:39 | 🟢 DONE | 2/2 | TASK-DONE: wrote 03-tart-ci-and-orchard.md + 04-tart-licensing-risk.md |
| 🖥 utm | surface:40 | 🟢 DONE | 3/3 | wrote 05/06/07, G1/G3/G5/G6/G7/G10 confirmed, flagged+resolved harness conflict |
| 🧪 harness | surface:38 | 🟢 DONE | 2/2 | RECONCILE-DONE: fixed 08 intro citation to AppleScript lifecycle + SSH/VirtioFS, verified on disk |
| 📚 synth | surface:41 | 🟢 DONE | 4/4 | TASK-DONE: wrote 00/10/11/specs/macos-ci.md (277 lines), all links resolve, no new conflicts |

## FSM

```
SCAFFOLD → RESEARCH(tart-core ∥ tart-ci ∥ utm ∥ harness) → DRAFT → CROSS-CHECK
        → { CLEAN → SYNTH → REVIEW → DONE }
        | { CONFLICT → RECONCILE → CROSS-CHECK ↺ }
        | ERROR (unrecoverable)
```

Current global state: **DONE** — all 6 agents green, `specs/macos-ci.md` reviewed and passed.

## Cross-check ledger (G1–G11)

| Ground truth | Owning spec(s) | Verified? |
|---|---|---|
| G1 — no Terraform provider tart/UTM; Orchard is tart's IaC story | 01, 03, 05, 10 | ✅ verified |
| G2 — tonyyo11 blog = Terraform for Jamf Pro, not VMs | 10 (ADR) | ✅ verified |
| G3 — packer-plugin-tart is tart-only; UTM = AppleScript/JXA + utm:// | 02, 05, 10 | ✅ verified |
| G4 — Tart Fair Source, enforced Oct 2025, tier table | 04, 10 | ✅ verified |
| G5 — UTM disposable mode is QEMU-only, not macOS guests | 06, 08(d), 10 | ✅ verified |
| G6 — UTM Apple backend: no multi-display | 06, 10 | ✅ verified |
| G7 — advanced/rosetta is Linux guests only, not macOS | 06, 10 | ✅ verified |
| G8 — tart headless keychain req; nested virt M3/M4+Linux only | 01 | ✅ verified |
| G9 — neither dotfiles repo uses Ansible (chezmoi / shell+Brewfile) | 09, 08(e) | ✅ verified |
| G10 — 4 dead docs.getutm.app URLs pruned, not cited | 07, 11 | ❌ **RETRACTED** — 3 of the 4 are live (HTTP 200). The ground truth was false and self-sealing: "do not fetch" meant no agent could disprove it, so this ✅ only ever recorded that nobody looked. See [11-sources.md](../specs/macos-ci/11-sources.md#retraction--the-g10-prune-list-was-wrong) |
| G11 — non-interactive chezmoi already solved upstream (stdinIsATTY) | 09, 08(b) | ✅ verified |

## Conflicts resolved during this run

1. **harness's `08-dotfiles-test-harness.md` intro citation** — originally cited "UTM AppleScript
   guest-exec" as the escape-hatch equivalent; utm's research found guest-exec/file-I/O requires the
   QEMU guest agent and does not work on Apple-backend macOS guests. Routed back to harness; fixed to
   cite "AppleScript lifecycle control + SSH/VirtioFS" instead, verified on disk.

## Plan-format contract check (`specs/macos-ci.md`)

- Heading order verified verbatim against the contract (Task Description → Objective → Problem
  Statement → Solution Approach → Relevant Files [+ New Files] → Implementation Phases [Phase 1/2/3] →
  Step by Step Tasks [1..10] → Testing Strategy → Acceptance Criteria → Validation Commands → Notes).
- 277 lines (target 200–350). Links out to all `specs/macos-ci/NN-*.md` files for depth.
- `task_type=feature`, `complexity=complex` — every conditional section present, none skipped.
