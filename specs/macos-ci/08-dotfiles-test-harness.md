# 08 — Dotfiles Test Harness Design

Owner: 🧪 harness. **This spec is synthesis, not summary** — no single source URL covers "a
macOS dotfiles-install test harness." It is designed here from primitives documented in
[01-tart-core.md](./01-tart-core.md) (tart `clone`/`run`/`--dir` mounts/`tart ip`/ssh),
[02-packer-tart-builder.md](./02-packer-tart-builder.md) (Packer's shell/Ansible provisioners for
building the golden image), and [05-utm-automation.md](./05-utm-automation.md) §2.2, §2.6, §6 (UTM's
AppleScript *lifecycle* control — create/start/stop/duplicate/snapshot — plus SSH over a VirtioFS
shared mount as the escape-hatch equivalent; UTM's Guest Suite guest-exec/file-I/O primitives require
the QEMU guest agent and do not work on Apple-backend macOS guests). Ground truths G1, G3, G5, G9
govern every design choice below; see [09-dotfiles-under-test.md](./09-dotfiles-under-test.md) for
what is actually being installed and asserted.

Per the [HOUSE STANCE](10-tart-vs-utm-adr.md#decision), **tart is primary** for this harness. UTM only
enters at teardown-comparison time (d) to explain why it is *not* used here.

## (a) Golden image vs. from-scratch per test

**Recommendation: golden image, cloned per run.**

Bootstrapping a bare OS image is expensive: Xcode CLT install, Homebrew bootstrap, and ~25 brew
formulae with compiled C/Ruby deps (openssl@3, readline, libyaml, gmp, autoconf). None of that is what's
under test; it's fixed cost that would otherwise be repeated on every single test invocation.

**What the golden image contains is a scoping decision, not a convenience.** It supplies exactly what
`zsh-dotfiles` assumes but never installs: **Xcode CLT, Homebrew, chezmoi ≥ 2.20.0**
(`zsh-dotfiles/.chezmoiversion:1`), and the brew prereq list from `smoke-test-docker.sh:142-143` — ten
formulae, exactly: `wget curl kadwanev/brew/retry go` (`:142`) and `openssl@3 readline libyaml gmp
autoconf tmux` (`:143`). The remainder of that function (`:144-157`) installs ~50 further formulae and is
deliberately **not** part of the golden image.

`retry` is load-bearing, and the reason is sharper than "the ported apply command uses it": upstream's
apply is *conditionally* wrapped. `smoke-test-docker.sh:360` guards on `command -v retry`, and `:364-365`
is an un-retried `else` arm. Upstream degrades when `retry` is missing; the harness must not, because a
flaky Sheldon or brew-tap fetch would then be indistinguishable from a dotfiles regression. So the golden
image **installs** `retry` (from the `kadwanev/brew` tap, as both `smoke-test-docker.sh:142` and
`zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer:589` do) rather than inheriting it.

**It does not run `zsh-dotfiles-prep/bin/zsh-dotfiles-prereq-installer`.** That installer additionally
provides a git-cloned asdf v0.11.2, a full Rust toolchain via rustup, and two parallel Python installs
(brew + pyenv 3.12.8 built `--enable-shared`) — see
[09-dotfiles-under-test.md](./09-dotfiles-under-test.md#bootstrap-verbatim-g9). Baking that in would
force `asdf` into every image, including `mise` runs, and none of it is required for the default lane.
It is invoked only by the optional `asdf` matrix leg, behind a `--with-prereq-installer` flag. See
[09-dotfiles-under-test.md](./09-dotfiles-under-test.md#what-zsh-dotfiles-cannot-bootstrap-on-macos).

### The base image is `-vanilla`, and it deliberately omits `mise`

**Decided (OQ-18). `-base` is not a clean slate, and using it would silently disarm this harness.**

Three facts, each carrying a passing ledger claim, and it is their *conjunction* that decides the
question — not any one of them:

1. **`-base` ships `mise`.** [`templates/base.pkr.hcl:109`](https://github.com/cirruslabs/macos-image-templates/blob/main/templates/base.pkr.hcl)
   runs `brew install mise` (alongside Homebrew, `rbenv`, and `node@24`). — `base-image-preinstalls-mise`
2. **`zsh-dotfiles` also installs `mise` itself** on macOS, via
   `run_onchange_before_02-macos-install-mise.sh.tmpl`. — `mise-installed-by-dotfiles-on-macos`
3. **…but that installer short-circuits when `mise` is already on `PATH`.** Line 9 of the script reads
   `command -v mise >/dev/null 2>&1 || brew install mise || true`. —
   `dotfiles-mise-script-short-circuits-on-existing-mise`

Put (1) and (3) together and the consequence is not a fidelity nicety, it is a hole:

> On a `-base` image the `brew install mise` arm **never executes**, and the suite reports **green having
> never run it**. A regression in the dotfiles' own `mise` bootstrap would be **invisible to the suite
> whose entire purpose is to catch it.**

Both (1) and (2) are true. The harness uses `-vanilla` **because** they are both true.

**The decision.** The golden image is built **once, on `ghcr.io/cirruslabs/macos-*-vanilla`**, and carries
exactly **Xcode CLT, Homebrew, chezmoi ≥ 2.20.0, and `retry`** — and **not `mise`**. Upstream's README
describes `-vanilla` as *"a vanilla macOS installation with helpful tweaks such as auto-login, but no
additional software preinstalled"*, and `-base` as *"based on `…-vanilla` image, [it] comes with `brew`…
pre-installed"* (`vanilla-image-preinstalls-no-software`, `base-image-is-derived-from-vanilla`). So this
is not a fork off upstream's line — it is one rung down it, re-adding only the prerequisites §(a) already
argued belong in the image.

That is the whole trade, and it resolves the cost objection rather than dodging it: the expensive, stable
bootstrap (CLT + Homebrew, minutes) is amortised into a golden image built once, while **the one path
under test is left cold.** `vanilla-sequoia.pkr.hcl` contains no `mise`
(`vanilla-sequoia-template-installs-no-mise`), so the dotfiles' `brew install mise` runs for real on every
clone.

`macos-versions.toml` ([12](./12-tooling-and-agent-loop.md#macos-versionstoml--declarative-image-selection))
now pins the OCI lane to `-vanilla` accordingly.

Design:

1. **Build once** — a Packer build (per [02](./02-packer-tart-builder.md)'s field reference) whose
   single idempotent `shell` provisioner installs the list above, verified working (`chezmoi --version`
   exits 0). This becomes the base tart VM image, tagged and optionally pushed to an OCI registry
   (ghcr.io, per [01](./01-tart-core.md)'s registry push/pull support) so the golden image itself is
   versioned and reproducible, not a snowflake on one machine. Which base image, and whether it comes
   from an OCI ref or a pinned IPSW, is declared in `macos-versions.toml`
   ([12](./12-tooling-and-agent-loop.md#macos-versionstoml--declarative-image-selection)).
2. **Clone per test run** — `tart clone <golden-image> <ephemeral-name>` gives a byte-identical,
   independent VM in seconds (copy-on-write per [01](./01-tart-core.md)), not minutes. Each test run
   gets its own ephemeral clone name (e.g. `dotfiles-test-<run-id>`) so concurrent runs never collide.
   <!-- UNVERIFIED: exact `tart clone` syntax — cross-check against 01-tart-core.md's verified CLI
   reference rather than this file. -->
3. **What varies per run lives in the clone, not the golden image**: the dotfiles source checkout
   (mounted via `tart --dir`, not baked in — see (b)), the `version_manager` selection, and
   `CM_computer_name`/`CM_hostname` for per-VM identity.

This mirrors the golden-image pattern markkenny's Packer reference implementation already
establishes for Ansible-during-build (`Packer.sh`/`Tarter.sh`, per [02](./02-packer-tart-builder.md))
— the harness reuses that build-once/clone-many shape but runs chezmoi (not Ansible) as the
per-clone payload. See (e) for why chezmoi replaces Ansible here rather than sitting alongside it.

**What NOT to bake into the golden image**: the dotfiles source itself. Baking it in would mean
rebuilding the golden image on every dotfiles commit, defeating the point of separating "expensive,
stable prerequisites" from "cheap, changing payload." The dotfiles tree is injected fresh per test
(b).

## (b) The non-interactive chezmoi run

**This is solved upstream — G11. Nothing here is investigated; it is transcribed and adapted.**

### Mechanism (not a discovery, a fact)

`home/.chezmoi.yaml.tmpl:2` gates every prompt except `version_manager` behind
`{{- if stdinIsATTY -}}`. Any exec path with no TTY attached — which an `ssh <host> '<command>'`
without `-t`, or a scripted non-interactive session, already is — makes `stdinIsATTY` false, so every
`promptString`/`promptBool` in the template resolves to its in-template default instead of blocking
on input. See [09](./09-dotfiles-under-test.md#the-chezmoi-template-contract-g11) for the full
walkthrough and the resulting default-value table. The harness's job is to **run the apply this way
by construction** — connect without a TTY — not to pass some special flag that "enables" non-interactive
mode. There is no such flag; the absence of a TTY *is* the mechanism.

### The run, composed from tart primitives

1. `tart run <clone-name> --no-graphics &` — boot the cloned VM headless (subject to the keychain
   requirement on macOS 15+ hosts noted in [01](./01-tart-core.md), G8).
   <!-- UNVERIFIED: exact headless-run flag spelling — cross-check against 01-tart-core.md's
   verified CLI reference rather than this file. -->
2. `tart ip <clone-name>` — poll until an IP is assigned.
3. Mount the dotfiles source into the guest via `tart --dir` (per [01](./01-tart-core.md)) rather
   than `git clone`-ing inside the guest — this keeps the exact working tree (including any local,
   uncommitted spec changes under test) identical between host and guest, and avoids a network
   round-trip per test run.
   <!-- UNVERIFIED: exact `--dir` mount syntax — cross-check against 01-tart-core.md. -->
4. `ssh admin@<ip> '<command>'` (default creds `admin`/`admin` on the ghcr.io prebuilt images per
   [01](./01-tart-core.md), G8) with **no `-t`** — this is the step that makes `stdinIsATTY` false.
   Two documented alternatives exist for this step, neither of which changes the TTY semantics that
   make it work — see [03](./03-tart-ci-and-orchard.md#running-scripts-in-a-vm-cirrus-run-vs-plain-ssh):
   `cirrus run` is the path Tart's own docs recommend for executing scripts and retrieving artifacts,
   and `sshpass -p admin ssh …` is the password-auth fallback those docs name. This harness stays on
   plain key-based `ssh` so it depends on neither.
   The command is the exact non-TTY invocation upstream already validated:

   ```sh
   retry -t 4 -- chezmoi init -R --debug -v --apply --force \
     --promptString version_manager="$VERSION_MANAGER" --source=<mounted-dotfiles-path>
   ```

   (verbatim shape from `zsh-dotfiles/scripts/smoke-test-docker.sh:361-365`, with `--source` pointed
   at the `tart --dir` mount instead of a local checkout). Keep the `retry -t 4` wrapper — upstream's
   own comment notes the run is network-flaky (Sheldon plugin fetches, brew taps), and there is no
   reason for the harness to be less resilient than the smoke test it's modeled on.

5. **Pre-apply template lint**: before step 4, run `chezmoi diff --source=<mounted-path>` over SSH
   and fail the test on non-empty stderr. **Not** `chezmoi verify` — see
   [09](./09-dotfiles-under-test.md#pre-apply-template-validation-chezmoi-diff-not-chezmoi-verify)
   for why `verify` cannot work pre-apply.
6. **Per-VM identity**: export `CM_computer_name=<run-id>` and `CM_hostname=<run-id>` in the SSH
   command's environment before invoking chezmoi — these are the two fields the template reads from
   env vars unconditionally (`.chezmoi.yaml.tmpl:26-27`), not gated behind `$interactive`, so they're
   the correct lever for making parallel/sequential runs distinguishable in logs and rendered config
   without touching the interactive-only fields.

### The one real limitation: the boolean toggles are unreachable non-TTY

`ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv` all sit inside the `$interactive` guard
(`.chezmoi.yaml.tmpl:58-98`). A non-TTY `--promptBool` flag **does not exist as a lever** — chezmoi's
`--promptBool`/`--promptString` flags only satisfy a `promptBool`/`promptString` call that actually
executes, and these calls never execute when `$interactive` is false. There are exactly two ways to
reach them in a harness, and this spec picks one:

- **Option A (recommended): a pre-seeded chezmoi config file.** Write a `~/.config/chezmoi/chezmoi.yaml`
  (or pass `--config`) into the guest *before* running `chezmoi init`, containing a `data:` block with
  `ruby`/`pyenv`/etc. already set. Every prompt in the template checks `hasKey . "<field>"` first
  (`.chezmoi.yaml.tmpl:58,64,70,...`) and skips straight to using the pre-seeded value if present —
  this path works identically whether interactive or not, because it short-circuits before the
  `promptBool` call. This is a **harness-side change only** (writing a file into the guest before the
  apply step) — it requires no edit to `zsh-dotfiles`.
- **Option B (not recommended): upstream template change.** Lift the seven flags out of the
  `$interactive` guard the same way `version_manager` was (`.chezmoi.yaml.tmpl:102`), so they become
  reachable via `--promptBool ruby=true` etc. This is a real fix but it's an edit to the
  `zsh-dotfiles` repo itself, owned upstream, and out of scope for a docs-only harness spec to just
  assume will land.

**Decision: Option A.** A toggle-matrix test (e.g. "assert Ruby installs correctly when `ruby=true`")
pre-seeds the config file for that one clone rather than blocking on an upstream template change.
Document Option B as the better long-term fix and out of scope here.

## (c) The assertion layer

"The dotfiles installed correctly" is not one check — it decomposes into the layers upstream already
tests for, reused rather than reinvented (see
[09](./09-dotfiles-under-test.md#assertion-vocabulary-already-in-use-upstream-reuse-dont-reinvent)):

| Layer | Check | Source of the check |
|---|---|---|
| Apply succeeded | `chezmoi init --apply` exits 0 | `smoke-test-docker.sh:361-373` |
| Post-install hook | `post-install-chezmoi` exits 0 (with `retry -t 4`) | `smoke-test-docker.sh:376-385` |
| Shell loads | `timeout 10s zsh -c 'source ~/.zshrc; [[ -n "$ZSH_VERSION" ]]'` | `smoke-test-docker.sh:388-404` |
| Prompt configured | same probe, `[[ -n "$PROMPT" \|\| -n "$PS1" ]]` | `smoke-test-docker.sh:396-402` |
| Login shell is zsh | `dscl . -read /Users/<user> UserShell` (macOS-specific — Linux upstream
  has no equivalent, so this check is **new** for this harness, not reused) | — |
| Sheldon plugins resolve | **Run `sheldon lock` in-guest; assert exit 0.** It is a *mutating* command —
  by its own help, *"Install the plugins sources and generate the lock file"* — and that is fine, because
  it runs inside a disposable clone that (d) destroys afterwards. Mutating a VM you are about to delete
  costs nothing; being able to mutate it is the point of using one | `sheldon lock --help`. Ledger:
  `CONTROL-sheldon-lock-help-prints-reinstall` (the verb exists at 0.6.6), `sheldon-lock-is-mutating`,
  `sheldon-lock-has-no-check-flag`, `sheldon-help-has-no-verify-subcommand`. **OQ-17, ANSWERED.** |
  | nvim headless sanity | `nvim --headless '+qa' ` exits 0 (loads config without erroring, does no work) | standard neovim smoke pattern, not upstream-sourced |
| tmux present | `tmux -V` exits 0 and prints the expected version | general tool-presence check |
| PATH ordering | `zsh -lc 'echo $PATH'` contains asdf/mise shims (whichever lane) ahead of system
  paths, consistent with the mutual-exclusion invariant in
  [09](./09-dotfiles-under-test.md#the-version_manager-selector-asdf--mise) | derived from
  `smoke-test-docker.sh:222-283`'s `setup_version_manager` |
| Homebrew health | `brew doctor` — **non-fatal warn only**, matching upstream's own treatment
  (`smoke-test-docker.sh:332-338` logs warnings but does not fail the stage) | `smoke-test-docker.sh` |
| Feature-toggle fields render correctly (lean baseline: all seven `false`) | `chezmoi data` on the
  guest, assert `ruby`/`pyenv`/`nodejs`/`k8s`/`cuda`/`fnm`/`opencv` are all `false` unless a
  pre-seeded config (b, Option A) was used for that run | derived directly from
  [09](./09-dotfiles-under-test.md#non-tty-default-state-what-installed-means-for-a-lean-baseline-run) |

**A note on the one mutating assertion (OQ-17).** Every other row above is read-only. `sheldon lock` is
not, and it cannot be: sheldon `0.6.6` — the exact version pinned at `.chezmoi.yaml.tmpl:131`, and the one
installed on this host, so its `--help` is evidence about the pinned release rather than some other one —
has no `--check` flag and **no `verify` subcommand anywhere** in `init | add | edit | remove | lock |
source | completions | version`. There is no read-only way to ask *"do these plugin sources resolve?"*

The instinct is to reach for the least-invasive probe. That instinct is wrong here, and the reason is
worth stating: **the disposable clone exists precisely so that mutation is free.** Running the real
installer inside a VM that (d) deletes moments later tests strictly *more* than a hypothetical read-only
verb would, because installing the plugin sources **is** the behaviour under test. A check that avoided
the side effect would also avoid the thing it is checking.

What we must not do is run it on the host, or on a clone we intend to reuse. `sheldon lock` writes the
lock file and clones every plugin source; both belong to the VM and die with it.

Recommended tooling: `pytest-testinfra`, matching the framework `zsh-dotfiles-prep/contrib/tests.sh`
already installs (`pip install pytest-testinfra`) — testinfra runs assertions like "package
installed" / "file exists" / "command succeeds" over an SSH backend natively, which is exactly the
transport this harness already uses to reach the tart guest. This avoids inventing a second
assertion DSL alongside the one upstream has already chosen. Do **not** treat
`zsh-dotfiles/test_dotfiles.py`'s alias-content tests as a model for this layer — most of that file
is explicitly `@pytest.mark.skip(reason="...meant to only run locally on laptop...")` and is
developer-local, not CI-grade.

## (d) Teardown

`tart delete <clone-name>` after each test run (success or failure — always clean up, optionally
skip deletion on failure if `--keep-on-failure`-style debugging is wanted for one run). Because (a)
clones from a golden image rather than mutating it, deletion is total and instant: no snapshot
reconciliation, no partial state to reason about, no risk of the next test inheriting leftover state
from this one.

**UTM cannot offer the equivalent.** UTM's disposable mode (run-without-saving, the obvious analog to
"ephemeral test VM, discard on exit") is **QEMU-backend only** — it does not work for macOS guests,
which require the Apple Virtualization.framework backend (G5). There is no UTM-native way to get a
disposable macOS guest; the closest approximation would be scripting create → snapshot → restore →
delete via AppleScript/`utmctl` (per [05](./05-utm-automation.md)) by hand, which is strictly more
moving parts than `tart clone` + `tart delete` for the same outcome. This is a direct, concrete
instance of the [HOUSE STANCE](10-tart-vs-utm-adr.md#decision)'s general "tart primary, UTM escape hatch"
rule, not an abstract preference — G5 forces it specifically here.

## (e) Decision: Ansible — reject it

**Recommendation: no Ansible.** The burden of proof is on adding it, and nothing in this stack meets
that burden.

- Neither dotfiles repo is *provisioned by* Ansible (G9). `zsh-dotfiles-prep` is a bash installer;
  `zsh-dotfiles` is driven end-to-end by `chezmoi init --apply`; neither repo contains a playbook, a
  role, or an inventory. `ansible` does appear — **twice**, both in `zsh-dotfiles-prep/Brewfile`: as one
  of 500+ Homebrew formulae (`:57`, `brew "ansible"`) and as a VS Code extension (`:602`,
  `vscode "redhat.ansible"`). It is an installable tool, not infrastructure the harness would be plugging
  into. Note the phrasing this forces: G9 cannot be proven with a bare `absent` claim over the string,
  because the string is present. The checkable form is *"no `hosts:`/`become:` key in any tracked YAML"*,
  which — being a negative over a command's output — needs a positive control to mean anything
  (ledger: `prep-repo-has-no-ansible-playbook` ↔ `CONTROL-prep-grep-c-emits-colon-when-present`).
- Upstream's own smoke test — the thing this harness is explicitly modeled on
  (`zsh-dotfiles/scripts/smoke-test-docker.sh`) — is a plain shell script that shells out to
  `chezmoi init --apply` directly, with no orchestration layer above it. Introducing Ansible here
  would mean the harness tests a *different* invocation shape than the one upstream actually runs in
  CI, undermining the harness's entire purpose (verifying the real bootstrap path works on macOS).
- Packer/Ansible-during-build is a real, documented pattern (markkenny's reference implementation,
  [02](./02-packer-tart-builder.md)) — but it's Ansible provisioning the **golden image's**
  prerequisites (CLT, Homebrew, base packages) at build time, which this harness's golden-image step
  (a) already covers using the existing `zsh-dotfiles-prep` installer script directly. Swapping that
  installer for an Ansible playbook would mean maintaining two parallel prerequisite-install
  implementations (the real one CI runs, and an Ansible reimplementation the harness runs) that can
  drift from each other — a net reliability loss, not a gain.
- Ansible would add a control-node dependency (Python + `ansible` package on whatever drives the
  harness, plus SSH inventory management) to replace something `tart --dir` + `ssh` + a shell
  one-liner already does in three primitives. There's no idempotency, templating, or
  multi-host-orchestration need here that justifies it — a single ephemeral VM per test run has no
  fleet to coordinate.

If the harness ever grows into fleet-scale provisioning (Orchard workers, per
[03](./03-tart-ci-and-orchard.md)), that is the point where Ansible-vs-shell-vs-Orchard-native
tooling becomes worth re-litigating — not before.

## Cross-references

- What is under test and why: [09-dotfiles-under-test.md](./09-dotfiles-under-test.md)
- Tart primitives this design composes: [01-tart-core.md](./01-tart-core.md)
- Golden-image build pattern: [02-packer-tart-builder.md](./02-packer-tart-builder.md)
- Getting the Homebrew token into that build without baking it into the image:
  [13-build-secrets.md](./13-build-secrets.md)
- UTM disposable-mode limitation (G5) in full: [06-utm-macos-guest.md](./06-utm-macos-guest.md)
- Fleet-scale future (Orchard): [03-tart-ci-and-orchard.md](./03-tart-ci-and-orchard.md)
- ADR recording the tart-primary decision this spec assumes: [10-tart-vs-utm-adr.md](./10-tart-vs-utm-adr.md)
