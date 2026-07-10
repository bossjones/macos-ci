# boss-cmux — macos-ci RESEARCH / SPEC-WRITING run

> **STATUS: SUPERSEDED — do not re-run as-is.**
> This prompt contains a ground truth (**G10**) that is **false**. It is archived verbatim, bug intact,
> because that bug is the evidence for how the successor prompt was designed.
> Use [`macos-ci-verify-team.md`](macos-ci-verify-team.md) instead.

The first run against `~/dev/bossjones/macos-ci`. Six panes: a lead plus five workers, fanning ~40 source
URLs (tart docs, UTM docs, `packer-plugin-tart`, blog walkthroughs) into a spec tree.

Preserved because `prompts/README.md` exists to *"find patterns and figure out easier ways to prompt
claude."* The most instructive pattern in this repo is a failure, and you cannot study it from the
successor prompt alone — the successor only *asserts* the failure. This file is the exhibit.

## What it produced

One run, and it worked: `specs/macos-ci/00-overview.md` through `11-sources.md`, plus the plan-format
entry point `specs/macos-ci.md`. Most of it held up under later audit. The ADR (tart primary, UTM as the
interactive escape hatch), the Fair Source licensing risk write-up, and the chezmoi non-TTY contract are
all still standing.

## What it got wrong — and the mechanism

The prompt asserted, as an unchallengeable ground truth:

> **G10.** These 4 URLs are 404 — prune them, do not fetch, do not cite:
> `docs.getutm.app/settings-apple/devices/`, `docs.getutm.app/settings-qemu/devices/devices/`,
> `docs.getutm.app/settings-qemu/drive/drive/`, `docs.getutm.app/guest-support/sharing/sharing/`

Three of those four return **HTTP 200**. The fourth, `settings-apple/devices/`, was never a dead page —
**it does not exist and never did.** It is absent from UTM's 78-page search index. It was *fabricated*,
then promoted to an axiom.

The clause **"do not fetch"** is what made it undisprovable. An agent forbidden from checking a claim
cannot discover the claim is wrong; it can only propagate it. And it did: `06-utm-macos-guest.md` ended
up citing the wrong source for the Apple-backend device toggles, while the page that actually documents
them — [`settings-apple/virtualization/`](https://docs.getutm.app/settings-apple/virtualization/) — was
never found. A single search-index query for `trackpad` would have surfaced it.

Retracted in commit `7f56031`; see the retraction section of `specs/macos-ci/11-sources.md`.

The general lesson, and the reason the successor prompt exists:

> **A rule that forbids verification does not protect truth. It launders a guess into an axiom.**

There is a second, subtler failure worth naming. The prompt told agents to mark anything they could not
verify with `<!-- UNVERIFIED -->`, and *simultaneously* forbade the verification that would have cleared
the marker. Under those rules the honest move and the lazy move produce identical output. A convention is
only load-bearing if the work it gates is actually possible.

## What it got right — carried forward unchanged

Worth separating from the failure, because most of this prompt was good:

- **The cmux mechanics were verified with `--help` against `cmux 0.64.17`, not recalled from memory** —
  and that check caught two wrong beliefs *before* the run: Claude Code *does* get hooks (auto-injected
  by the cmux Claude wrapper, so `cmux hooks setup` is unnecessary), and `rename-tab` does *not* require
  `--workspace` for a self-rename. Note the irony: the author applied to the tooling exactly the
  discipline that G10 forbade for the sources.
- The **FSM + `cmux notify` on every transition + a `TASK-DONE:` sentinel**, so the lead gets a semantic
  per-transition signal rather than a generic turn-stop.
- **Exclusive file ownership** per agent, with everything else routed through a shared backlog.
- A **barrier on `synth`**, idle until all four researchers finish, so the synthesizer never reads a
  half-written file.
- **"Prefer a shorter spec that is entirely true over a long one padded with plausible-sounding detail."**

## How the successor differs

| This run (research) | [`macos-ci-verify-team.md`](macos-ci-verify-team.md) |
|---|---|
| "DOCS ONLY … write it down rather than running it" | Read-only verification **required**; explicit allowlist |
| Ground truths are commandments | Ground truths are **claims to refute**; G10 retracted in-prompt |
| A citation is a URL | A citation is a **re-executable ledger entry** (`tools/verify_claims.py`) |
| Agents self-review | **Rotated cross-audit**, red-team posture, default-to-refuted |
| DONE = the lead reads it | DONE = **`just check` exits 0**, output pasted |
| 6 panes | 7 panes (adds 🔬 `ledger`) |

---

## The prompt

Archived verbatim from `~/.claude/plans/i-want-you-to-proud-aurora.md` (lines 49–356), whose own header
records that this fenced block was that session's sole deliverable. Confirmed against
`logs/user_prompt_submit.json` as the text actually submitted.

**Read it as a historical artifact. G10 is wrong. Nothing below has been corrected.**

````text
/boss-cmux Boot a 6-pane RESEARCH/SPEC-WRITING team for the repo /Users/bossjones/dev/bossjones/macos-ci.
Reuse the open cmux window; add a NEW workspace named "macos-ci-specs" (cwd = that repo; do NOT pass
--env-file — the Claude panes use the existing login). Launch all 6 panes as
`claude --dangerously-skip-permissions` (I authorize bypass mode). Colour the workspace, label the tabs,
and after launching the 5 workers hand the lead its brief. Drive the LEAD only; the lead drives the other 5.

DO NOT run `cmux hooks setup`. Claude Code is absent from its agent list because it does not need it —
`cmux hooks --help` states "Claude Code hooks are injected automatically by the cmux Claude wrapper."
Hooks are ALREADY active for these panes. Regardless, every agent ALSO fires `cmux notify` EXPLICITLY on
each FSM transition and prints a `TASK-DONE:` sentinel, because a semantic per-transition signal beats a
generic turn-stop. The lead waits on `cmux events --name notification.created --no-heartbeat --no-ack`
(matching workspace_id) and confirms with `cmux read-screen`.

SCOPE — DOCS ONLY. This run writes markdown. NO agent installs tart/packer/UTM, pulls a VM image, boots a
VM, runs `brew install`, or mutates the host in any way. WebFetch + Read + Write only. If a spec needs a
command it cannot verify, write it down and mark it `<!-- UNVERIFIED -->` rather than running it.

ROLES (👑 lead on the left half; the rest in a grid on the right):
  👑 lead      — orchestrator (I talk to this one); owns .team/ + final review
  🍎 tart-core — tart CLI fundamentals + the Packer tart builder
  🏭 tart-ci   — Cirrus CI, Orchard orchestration, and the Fair Source licensing risk
  🖥  utm       — UTM scripting/headless/remote-control + macOS-guest specifics
  🧪 harness   — the dotfiles smoke-test harness (SYNTHESIZED — no source doc covers this)
  📚 synth     — comparison ADR, sources index, and the final specs/macos-ci.md

EXCLUSIVE FILE OWNERSHIP (an agent edits ONLY its files; coordinate everything else via the backlog):
  tart-core → specs/macos-ci/01-tart-core.md
              specs/macos-ci/02-packer-tart-builder.md
  tart-ci   → specs/macos-ci/03-tart-ci-and-orchard.md
              specs/macos-ci/04-tart-licensing-risk.md
  utm       → specs/macos-ci/05-utm-automation.md
              specs/macos-ci/06-utm-macos-guest.md
              specs/macos-ci/07-utm-settings-appendix.md
  harness   → specs/macos-ci/08-dotfiles-test-harness.md
              specs/macos-ci/09-dotfiles-under-test.md
  synth     → specs/macos-ci/00-overview.md
              specs/macos-ci/10-tart-vs-utm-adr.md
              specs/macos-ci/11-sources.md
              specs/macos-ci.md
  lead      → .team/macos-ci.board.md, .team/macos-ci.backlog.md

STATUS BOARD (every agent, always current — I want to glance and know the fleet's state):
- Flags below were verified against cmux 0.64.17. Still trust `--help` over memory; never guess a flag.
- On EVERY state change, rename your OWN tab to a pill. rename-tab resolves its target as
  --tab → --surface → $CMUX_TAB_ID/$CMUX_SURFACE_ID → focused tab, so renaming yourself needs NO target flag:
    cmux rename-tab "<emoji> <role> <n>/<N> [<progressbar>] · <one-line log>"
  emoji = 🔵 working / 🟢 done / 🔴 error, progressbar like [####------].
  e.g. "🔵 utm 4/9 [####------] · reading scripting/cheat-sheet"
  (Only the LEAD, renaming someone ELSE's tab by ref, needs the context flags:
   `cmux rename-tab --workspace <ws> --surface <ref> "<title>"`.)
- Surfaces have NO colour attribute — colour lives on the workspace. LEAD (and only lead) sets the
  workspace pill to the overall FSM state on each transition. Note `set-status --color` takes a #hex:
    cmux set-status state <STATE> --workspace <ws> --icon doc.text.magnifyingglass \
      --color <#1565C0 working | #196F3D done | #C0392B error>
  and mirrors coarse progress with `cmux set-progress <0.0-1.0> --label "<state>" --workspace <ws>`.
  Optionally tint the whole row once at SCAFFOLD:
    cmux workspace-action --action set-color --workspace <ws> --color Indigo
  (workspace-action accepts a named colour: Red, Crimson, Orange, Amber, Olive, Green, Teal, Aqua, Blue,
   Navy, Indigo, Purple, Magenta, Rose, Brown, Charcoal — or #RRGGBB.)
- LEAD keeps a board table (agent | state | n/N | last log) in .team/macos-ci.board.md and a living task
  list in .team/macos-ci.backlog.md.

FSM + NOTIFICATIONS: this run is a finite state machine —
  SCAFFOLD → RESEARCH(tart-core | tart-ci | utm | harness in parallel) → DRAFT → CROSS-CHECK →
  {CLEAN → SYNTH → REVIEW → DONE} | {CONFLICT → RECONCILE → CROSS-CHECK↺} | ERROR(unrecoverable).
  FIRE `cmux notify --title "<role>" --body "<state>: <one-line>"` ON EVERY TRANSITION (each agent on its
  own; lead on the global ones) so I'm pinged through the whole process.

────────────────────────────────────────────────────────────────────────────
LEAD BRIEF — do this:

1) SCAFFOLD. `mkdir -p specs/macos-ci .team`. Write .team/macos-ci.backlog.md and
   .team/macos-ci.board.md. Dispatch all 4 researchers (tart-core, tart-ci, utm, harness) IN PARALLEL —
   they have no ordering dependency. synth STAYS IDLE until all four print TASK-DONE (it is a barrier).

2) Wait on `cmux events --name notification.created --no-heartbeat --no-ack` matching this workspace_id.
   Do NOT busy-poll for agent completion. Once notified, confirm with
   `cmux read-screen --surface <ref> --scrollback --lines 40` and check for `TASK-DONE: <role> | <summary>`.

3) CROSS-CHECK (lead does this personally, before releasing synth). Verify every researcher honoured the
   GROUND TRUTHS below. Any spec asserting the opposite is a CONFLICT → route back to the owning agent →
   re-enter CROSS-CHECK. Do not let a wrong claim reach synth.

4) SYNTH. Release the synth agent. It reads all 9 researcher files, writes 00-overview.md,
   10-tart-vs-utm-adr.md, 11-sources.md, and finally specs/macos-ci.md.

5) REVIEW. Lead reads specs/macos-ci.md end-to-end and checks it against the PLAN-FORMAT CONTRACT below.
   Then set the board all-🟢, `cmux set-status state done --workspace <ws> --color "#196F3D"`, notify DONE,
   and report the roster (pane → role → surface) plus the rendered board.

────────────────────────────────────────────────────────────────────────────
GROUND TRUTHS — established by prior research. Any agent that contradicts one of these is WRONG and must
be corrected. Do not "discover" these again; do not soften them.

  G1. There is NO Terraform provider for tart, and NO Terraform provider for UTM. Tart's orchestration
      story is Orchard (its own controller + kubectl-like CLI + REST API). utmapp/UTM#3618 is the open
      request for UTM IaC; the maintainer says it is "a long way off" (tracked in issue #3718).
  G2. The tonyyo11 blog uses Terraform to manage JAMF PRO RESOURCES, not to manage VMs. Do not cite it as
      evidence of VM-as-code. The repo README's "Terraform" line is aspirational — say so in the ADR.
  G3. packer-plugin-tart is TART-ONLY. No UTM Packer builder exists. UTM automation is AppleScript / JXA
      (`utmctl`) + the `utm://` URL scheme.
  G4. Tart is Fair Source and ACTIVELY ENFORCED as of the Oct 2025 announcement. Free on personal
      workstations; commercial use free up to 100 CPU cores (tart) / 4 Orchard workers; Gold $12K/yr
      (500 cores / 20 workers), Platinum $36K/yr (3000 / 200), Diamond custom ~$12/core/yr.
      THERE IS NO OPEN-SOURCE EXEMPTION. This is an accepted-risk section, not a footnote.
  G5. UTM "disposable mode" (run-without-saving) is QEMU-BACKEND ONLY. It does NOT work for macOS guests,
      which require the Apple Virtualization.framework backend. This kills the obvious "disposable UTM VM
      per dotfiles test" idea — say so explicitly.
  G6. UTM's Apple backend does NOT support multiple graphical displays.
  G7. `advanced/rosetta` is about running x86_64 ELF binaries in LINUX guests. It is NOT about macOS
      guests. Do not file it under macOS-guest support.
  G8. tart headless on macOS 15+ hosts has a keychain requirement; nested virtualisation needs M3/M4 AND a
      Linux guest. Prebuilt ghcr.io images cover macOS 12–26; default creds are admin/admin.
  G9. NEITHER dotfiles repo uses Ansible. `zsh-dotfiles` is chezmoi-driven
      (`sh -c "$(curl -fsLS chezmoi.io/get)" -- init -R --debug -v --apply https://github.com/bossjones/zsh-dotfiles.git`).
      `zsh-dotfiles-prep` is pure shell + Brewfile
      (`curl -fsSL https://raw.githubusercontent.com/bossjones/zsh-dotfiles-prep/main/bin/zsh-dotfiles-prereq-installer | bash -s -- --debug`).
      Ansible is a wrapper we may CHOOSE, not something inherited. The harness spec must justify it or drop it.
  G10. These 4 URLs are 404 — prune them, do not fetch, do not cite:
      docs.getutm.app/settings-apple/devices/, docs.getutm.app/settings-qemu/devices/devices/,
      docs.getutm.app/settings-qemu/drive/drive/, docs.getutm.app/guest-support/sharing/sharing/

  G11. NON-INTERACTIVE CHEZMOI IS ALREADY SOLVED UPSTREAM. Do not re-derive it, do not guess flags, and do
      NOT mark it UNVERIFIED. Both repos are checked out LOCALLY — read them, do not WebFetch them:
        /Users/bossjones/dev/bossjones/zsh-dotfiles
        /Users/bossjones/dev/bossjones/zsh-dotfiles-prep
      Verified facts (read from the working tree, not inferred):
      - `.chezmoiroot` = `home`, so the config template is `home/.chezmoi.yaml.tmpl`.
        `.chezmoiversion` = `2.20.0` (minimum chezmoi the harness must install).
      - Line 2 is `{{- $interactive := stdinIsATTY -}}`. EVERY `promptString`/`promptBool` for
        name/email/computer_name/hostname/ruby/pyenv/nodejs/k8s/cuda/fnm/opencv sits inside
        `{{- if $interactive -}}` … `{{- end -}}`. **In a non-TTY run those prompts never execute and the
        in-template defaults are used.** So piping the bootstrap through ssh with no TTY already yields a
        deterministic, prompt-free install. THIS IS THE MECHANISM. There is no flag to discover.
      - Non-TTY defaults are therefore: name="Malcolm Jones", email="bossjones@theblacktonystark.com",
        and ruby/pyenv/nodejs/k8s/cuda/fnm/opencv ALL `false`. Baseline runs install none of the optional
        toolchains — the harness must state this, because "the dotfiles installed" means the *lean* set.
      - `computer_name` and `hostname` are NOT prompt-only: they read env vars first —
        `default "boss workstation" (env "CM_computer_name")` and `default "bossworkstation" (env "CM_hostname")`.
        So the harness sets `CM_computer_name` / `CM_hostname` per VM to make runs distinguishable.
      - `version_manager` (`asdf` | `mise`) is DELIBERATELY placed OUTSIDE the `if $interactive` block —
        see the comment on line 102 — precisely so a non-TTY run can select it. It defaults to `asdf`.
        Override with `--promptString version_manager=mise`.
      - The repo's own non-TTY invocation, copy it verbatim (`scripts/smoke-test-docker.sh:361-365`):
          chezmoi init -R --debug -v --apply --force --promptString version_manager="$VERSION_MANAGER" --source=.
        and the config-only variant at line 300: `chezmoi init --source=. --force --promptString version_manager=…`
        Note `--force` (skip confirmations) and that upstream wraps it in `retry -t 4` because the run is
        network-flaky. The harness should keep the retry.
      - `chezmoi verify` does NOT work pre-apply (it compares destination to target). Upstream uses
        `chezmoi diff` to validate templates parse — see the comment at `scripts/smoke-test-docker.sh:308`.
      - The three `Dockerfile-{centos-9,debian-12,ubuntu-2204}` in zsh-dotfiles-prep are the EXISTING Linux
        coverage. macOS has no equivalent — that gap is exactly the reason this repo exists. Say so.
      - The `--promptBool` flags CANNOT reach ruby/pyenv/nodejs/k8s/cuda/fnm/opencv in a non-TTY run,
        because those prompts are inside the `$interactive` guard and never fire. If the harness needs a
        matrix over those toggles, the ONLY levers are a pre-seeded chezmoi config file (so `hasKey .`
        is true) or an upstream change lifting them out of the guard the way `version_manager` was.
        RECOMMEND ONE EXPLICITLY and note it is an upstream change, not a harness change.

HOUSE STANCE (the ADR must land here, and every spec must be consistent with it):
  TART IS PRIMARY for CI and automated dotfiles testing (it has a Packer builder, an OCI image registry,
  a CLI, and an orchestrator). UTM IS THE ESCAPE HATCH for interactive/GUI work, recovery-mode fiddling,
  and non-ARM guests. Reasons: G1, G3, G5. The licensing risk (G4) is the price and is documented as an
  explicit accepted-risk section with the core-count threshold we must stay under.

────────────────────────────────────────────────────────────────────────────
PLAN-FORMAT CONTRACT — specs/macos-ci.md is the input to `/agent-harness:plan`. synth MUST use these
EXACT headings, in this EXACT order (verified against the plan command's template — note "Step by Step
Tasks" has no hyphens, and Acceptance Criteria comes BEFORE Validation Commands):

  # Plan: <task name>
  ## Task Description
  ## Objective
  ## Problem Statement
  ## Solution Approach
  ## Relevant Files          (### New Files subsection allowed)
  ## Implementation Phases   (### Phase 1: Foundation / ### Phase 2: Core Implementation / ### Phase 3: Integration & Polish)
  ## Step by Step Tasks      (### 1. <Task>, ### 2. <Task>, …)
  ## Testing Strategy
  ## Acceptance Criteria
  ## Validation Commands
  ## Notes

  Treat this as task_type=feature, complexity=complex (so every conditional section above is REQUIRED).
  specs/macos-ci.md must be self-contained enough to hand to `/agent-harness:build` but must LINK OUT to
  specs/macos-ci/NN-*.md for depth. Target 200-350 lines; the depth lives in the sub-files.

────────────────────────────────────────────────────────────────────────────
WORKER BRIEFS

🍎 tart-core → 01-tart-core.md, 02-packer-tart-builder.md
  Sources: tart.run/quick-start/, tart.run/faq/, github.com/cirruslabs/packer-plugin-tart,
    developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart,
    github.com/markkenny/macos-virtualisation
  01: tart install; clone/run/create/set/list/delete; ghcr.io prebuilt images (macOS 12–26 + Linux);
      admin/admin; `--dir` shared mounts; OCI push/pull; NAT vs bridged; disk resize via recovery;
      ~/.tart layout + cache pruning; headless keychain requirement (G8); nested virt limits (G8).
  02: the FULL builder field reference — vm_name, from_ipsw, from_iso, vm_base_name, disk_size_gb,
      cpu_count, memory_gb, recovery-partition handling, boot_command, boot_wait, SSH communicator,
      headless, run_extra_args, registry pull opts. Then markkenny's reference implementation:
      Packer.sh/Tarter.sh, the IPSW→build(~15-20min)→`tart clone` workflow, Ansible-during-build (needs
      CLT + Python), and the passwordless-sudo / auto-login / clipboard toggles. Note the
      packer-plugin-tart README is a THIN stub (install + macOS 15 requirement + local-network-permission
      workaround) — the HashiCorp page is canonical.

🏭 tart-ci → 03-tart-ci-and-orchard.md, 04-tart-licensing-risk.md
  Sources: tart.run/integrations/cirrus-cli/, tart.run/orchard/quick-start/, tart.run/licensing/, tart.run/blog/
  03: `.cirrus.yml` macOS tasks; `cirrus run` local == cloud; `--artifacts-dir` extraction. Then Orchard:
      controller/worker multi-host model, `orchard create|list|delete vm`, SSH/VNC proxy, `orchard dev`,
      worker license tiers. Frame BOTH as "how this repo would eventually run dotfiles tests on a fleet."
  04: G4 in full — the tier table, the exact thresholds, the Oct-2025 enforcement announcement, and a
      concrete "what keeps us under 100 cores" recommendation for this repo's scale. Write it as an
      ACCEPTED-RISK section a human can sign off on, with the trigger condition that forces a re-decision.

🖥 utm → 05-utm-automation.md, 06-utm-macos-guest.md, 07-utm-settings-appendix.md
  Sources: docs.getutm.app scripting/{reference,cheat-sheet}, advanced/{headless,remote-control,disposable,
    rosetta,recovery,multiple-displays,serial,version}, settings-apple/{boot,drive,system,information,sharing},
    settings-qemu/{system,qemu,sharing,input,information}, preferences/macos, guest-support/{macos,
    dynamic-resolution}, installation/macos, basics/{actions,controls}, guides/{guides,classic-macos},
    mac.getutm.app, github.com/utmapp/UTM/discussions/3618
  05: OPEN with G1+G3 — UTM has no IaC; automation is AppleScript/JXA + `utm://`. Then the AppleScript
      suite (make/start/stop/suspend/duplicate; backend enum apple|qemu; status/stop-method/serial enums),
      the cheat-sheet snippets (list/find VMs, disposable start, create VM, read/write guest files,
      EXECUTE GUEST COMMANDS, USB, input automation), headless (delete display + built-in-terminal serial
      device; UTM.app must stay open; can hide dock icon), and the `utm://` URL scheme incl. its
      improper-shutdown warnings. Cite discussion #3618 for the IaC gap.
      docs.getutm.app 403s WebFetch — retrieve via `curl -fsSL`.
  06: macOS 12+ guests via IPSW (auto-download or ipsw.me); VirtioFS shared dirs (`mount_virtiofs`,
      macOS 13+ host AND guest); network sharing; clipboard (macOS 15+); missing features; the Apple
      Virtualization backend settings (balloon/entropy, sound/keyboard/pointer/trackpad, Rosetta toggle,
      clipboard) and their per-macOS-version gating; recovery/1TR + SIP. MUST state G5 (disposable is
      QEMU-only → no disposable macOS guest) and G6 (no multi-display on Apple backend) prominently.
      Rosetta goes under LINUX guests, not here (G7).
  07: a THIN appendix — one table row per settings page. Do not pad. Prune the 4 dead URLs (G10).

🧪 harness → 08-dotfiles-test-harness.md, 09-dotfiles-under-test.md
  THIS IS THE GAP. No source URL covers a dotfiles-install test harness. You are SYNTHESIZING, not
  summarising. Design the harness from primitives the other agents are documenting: tart `--dir` mounts +
  `tart ip` + ssh (spec 01), Packer shell/Ansible provisioners (02), UTM guest-exec + read/write files (05).

  READ THE LOCAL CLONES — do NOT WebFetch GitHub for these, the working trees are on disk and are the
  authority:
      /Users/bossjones/dev/bossjones/zsh-dotfiles
      /Users/bossjones/dev/bossjones/zsh-dotfiles-prep
  Start with, at minimum: `home/.chezmoi.yaml.tmpl`, `.chezmoiroot`, `.chezmoiversion`,
  `scripts/smoke-test-docker.sh`, `Dockerfile`, `CLAUDE.md`, and (in -prep) `install.sh`, `Brewfile`,
  `Makefile`, `TESTING.md`, `DEBUG.md`, `bin/zsh-dotfiles-prereq-installer`, and the three
  `Dockerfile-{centos-9,debian-12,ubuntu-2204}`. G11 already records what `home/.chezmoi.yaml.tmpl` and
  `scripts/smoke-test-docker.sh` say — CONFIRM it against the tree, then build on it. Mine
  `TESTING.md`/`DEBUG.md` and the Makefile for the assertions and smoke targets upstream ALREADY uses;
  reuse them rather than inventing a parallel assertion vocabulary.

  09: what is actually under test — the chezmoi `stdinIsATTY` prompt model per G11 (and the exact
      non-TTY default set), the Sheldon/tmux/nvim/fzf/rg payload, the optional Ruby/pyenv/Node/k8s/CUDA/
      fnm/OpenCV toggles and the fact that a non-TTY run leaves them ALL false, the `version_manager`
      asdf|mise selector, `.chezmoi.os`/`.chezmoi.arch` branching, the pinned tool versions in the
      template's `data:` block, and the two bootstrap one-liners verbatim (G9). Call out that the prep
      installer's Dockerfiles cover CentOS/Debian/Ubuntu and NOTHING covers macOS — that is this repo's
      whole reason to exist.

  08: the harness design. Cover at minimum:
      (a) golden-image vs from-scratch per test — recommend a Packer golden image with CLT + Homebrew +
          chezmoi >= 2.20.0 preinstalled, then `tart clone` per test run so each test starts from a
          byte-identical VM in seconds;
      (b) the non-interactive chezmoi run. This is SOLVED — see G11. Do not investigate, do not mark it
          UNVERIFIED. Write it up as settled: ssh without a TTY ⇒ `stdinIsATTY` is false ⇒ prompts are
          skipped ⇒ deterministic defaults. Reuse upstream's exact command incl. `--force`, the
          `--promptString version_manager=…` lever, the `retry -t 4` wrapper, `CM_computer_name`/
          `CM_hostname` for per-VM identity, and `chezmoi diff` (NOT `chezmoi verify`) for pre-apply
          template validation. Explicitly note the one real limitation: the boolean feature toggles are
          unreachable non-TTY, so a toggle matrix needs a pre-seeded config file or an upstream change —
          pick one and say which;
      (c) the assertion layer — what "the dotfiles installed correctly" means as a checkable list (zsh is
          login shell, sheldon lock resolves, nvim headless `+qa` exits 0, `tmux -V`, PATH ordering, brew
          doctor clean-ish). Prefer assertions upstream's TESTING.md/Makefile already defines;
      (d) teardown via `tart delete` and why UTM cannot offer the equivalent (G5);
      (e) a decision on Ansible: justify it against plain shell + chezmoi (G9) and RECOMMEND ONE. Given
          that the upstream smoke test is a plain shell script driving `chezmoi init --apply`, the burden
          of proof is on Ansible. Do not hedge.

📚 synth → 00-overview.md, 10-tart-vs-utm-adr.md, 11-sources.md, specs/macos-ci.md   [BARRIER — idle until
  all four researchers print TASK-DONE. Do not start early; you need their files.]
  10: the ADR. Context / Decision / Consequences. Decision = HOUSE STANCE above. Consequences must name
      the licensing exposure (G4) and the loss of disposable-mode (G5) as the costs we accept.
  11: every URL, grouped by bucket, each with a one-line "what it gave us", each marked
      [meaty | thin | 404-pruned]. This is the audit trail — a reader must be able to tell what was
      actually read vs. skimmed.
  00: a 1-page orientation — the problem, the stack, the file map, the reading order.
  macos-ci.md: the PLAN-FORMAT CONTRACT above, verbatim headings, feature/complex.

────────────────────────────────────────────────────────────────────────────
RULES EVERY AGENT OBEYS:
- Edit ONLY your owned files. Everything else goes through .team/macos-ci.backlog.md.
- DOCS ONLY. No installs, no VM pulls, no host mutation. WebFetch/Read/Write only.
- docs.getutm.app 403s WebFetch → use `curl -fsSL <url>`.
- Cite the source URL inline for every non-obvious claim. Anything you assert but could not verify from a
  source gets an explicit `<!-- UNVERIFIED -->` marker on the line. Never present inference as fact.
- Prefer a shorter spec that is entirely true over a long one padded with plausible-sounding detail.
- If a GROUND TRUTH conflicts with what you read, STOP and report to the lead in the backlog — do not
  silently pick a side.
- Keep your tab pill current on every state change. Fire `cmux notify` on every FSM transition.
- End with exactly: `TASK-DONE: <role> | <one-line summary>`
- The pre_tool_use hook blocks the substrings `rm `, `.env`, and `--rm`: use `mv` into the scratchpad
  instead of `rm`, and avoid the literal `.env` token.
- Lint any Python with `uvx ruff check <file>` (ruff/ty are not on PATH). Bash is auto-rewritten through
  rtk. zsh does not word-split unquoted vars — inline lists or use `${=var}`.

Report back when the team is up with the roster (pane → role → surface) and the board rendered. When the
FSM reaches DONE, tell me and I will run `/agent-harness:plan specs/macos-ci.md` in a separate terminal.
````

---

## Provenance

- **Source**: `~/.claude/plans/i-want-you-to-proud-aurora.md`, fenced block, lines 49–356.
- **Run**: produced `specs/macos-ci/00-…11-*.md` and `specs/macos-ci.md` on branch `inital-spec`.
- **Retraction**: commit `7f56031`, *"docs: retract false G10 claim and fix documentation sources."*
- **Successor**: [`macos-ci-verify-team.md`](macos-ci-verify-team.md).

If you re-run anything from this file, re-run the parts under *"What it got right."* Not G10.
