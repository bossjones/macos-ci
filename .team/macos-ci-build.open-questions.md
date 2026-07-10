# Open Questions — team macos-ci-build

Continuation of `.team/macos-ci.open-questions.md` (read-only, previous run). Append only; never
rewrite another agent's block.

---

## OQ-01 · core-builder red-team · finding (not blocking)
**Filed by:** ✅ validator, during ongoing red-team of `src/macos_ci/_doctor_core.py`.
**Status:** FLAGGED — informational, not a gate blocker. Owner: 🐍 core-builder (`_doctor_core.py`).

**What I found:** `_doctor_core.version_at_least(found, minimum)` compares `_parse_version()`
tuples directly without padding to equal length. Python tuple comparison treats a shorter tuple
that is a prefix of a longer one as *less than* it, so a numerically-equal short-form version
spuriously fails:

```
version_at_least("2.0", "2.0.0")   -> False   # should be True, they're equal
version_at_least("2.0.0", "2.0.0") -> True    # baseline sanity, passes
```

Reproduced against the landed code (not a stub) — all 27 `tests/unit/` tests still pass, so this
edge case isn't covered by an existing test.

**Why it isn't exploitable today:** `doctor.py::_tool_version()` extracts the version string via
`_VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:-[\w.]+)?")`, which requires exactly 3 leading
components. A tool printing a 2-component version (e.g. hypothetical `just 1.42`) simply fails to
match and `_tool_version()` returns `None` — reported as "missing", not silently passed via the
buggy comparison. So the live tool-version path is not currently reachable.

**Where it *is* live:** `macos_version` is compared with `_MIN_MACOS_VERSION = "13.0"` using the
same `version_at_least`, fed from `platform.mac_ver()[0]` — NOT filtered through `_VERSION_RE`.
`platform.mac_ver()` can return a 2-component string (observed forms vary by macOS release). Right
now every real macOS major is > 13, so the bug is masked (`(15,) >= (13,0)` is `True` regardless,
since the first components already differ). It would only misfire on an exact-boundary
2-vs-3-component tie, which isn't reachable with the current `_MIN_MACOS_VERSION` value — but the
function itself is the latent defect, independent of today's specific inputs.

**Suggested fix (not applied — not my file to own):** zero-pad both tuples to the longer length
before comparing, e.g. `pad = max(len(a), len(b)); a += (0,) * (pad - len(a))` (same idea on `b`).

**Cost of leaving it:** low today (masked by current inputs + the version regex), but silent if
`_MIN_VERSIONS`/`_MIN_MACOS_VERSION` ever moves to a value that creates a real length-mismatch tie,
or if `version_at_least` gets reused elsewhere without going through `_VERSION_RE` first.

---

## OQ-02 · harness-builder · BLOCKED-BY-OWNERSHIP
**Filed by:** 🛠 harness-builder, after Step 4 (Justfile recipe-table extension).
**Status:** BLOCKED-BY-OWNERSHIP — not gate-blocking on its own, but `just check`'s exit code is now
misleading until someone with ledger access resolves it.
**Spec:** specs/macos-ci/12-tooling-and-agent-loop.md §"Recipe reference"

**Question:** Step 4 required implementing `build-ipsw`, `images`, `pull` for real and converting
`build-golden` into an alias for the new `build` recipe. Doing exactly that flips 8 pre-existing
`.team/claims.jsonl` entries from PASS to FAIL, dropping `just check` from 311/311 to 303/311. None of
these are Justfile defects — they are guard/control claims that were written to prove the **pre-Step-4**
state (`build-ipsw`/`images` absent, `build-golden:` a literal recipe header, `packer/` absent). Who
retires or repins them? The binding rule for everyone is "never touch `.team/claims.jsonl`", and it has
no owner in the board's ownership table.

**What I tried:** Restructured the Justfile so the *original* block (the `link-check` through `check:`
recipes, formerly lines 1-74) keeps its exact original line numbers — only the `build-golden:` header
text became `build:` in place — specifically to keep the `file-line`-kind claims
(`justfile-verify-no-secrets-starts-at-line-60`, `justfile-build-golden-guards-on-missing-template`,
`justfile-build-golden-guard-exits-4`) pinned. That recovered 5 of the 13 claims that failed on the
first pass (298/311 → 303/311). The remaining 8 are not fixable from the Justfile side:
- `justfile-has-build-golden` (file-contains, expects literal `build-golden:`) — now `build-golden` is
  an `alias … := build` line with no trailing colon after the name, so the substring is gone by design.
- `CONTROL-xaudit-just-summary-lists-build-golden` (cli-help, expects `just --summary` to print
  `build-golden`) — verified empirically that `just --summary` **never lists aliases**, only real
  recipe names (`apply build build-ipsw check ci …`, no `build-golden`/`stop`). Structural fact about
  `just`, not a bug in this Justfile.
- `d2-justfile-has-no-build-ipsw-recipe` / `justfile-has-no-images-recipe` (`absent`, paired via
  `justfile-has-build-golden`) — these fail now because Step 4 explicitly lists `build-ipsw`, `images`
  as recipes to add, and I added them.
- `xaudit-12-no-build-ipsw-recipe` / `xaudit-12-no-images-recipe` (`must_fail: true`) — same shape; the
  ledger's own claim prose says *"if this ever starts passing, 12's recipe table entry should be
  updated from Proposed to real"* — i.e. this is a **designed trip-wire for exactly this landing**, not
  a false positive.
- `CONTROL-d1-packer-dir-does-not-exist` / `golden-template-does-not-exist` — 📦 packer-builder's
  fallout (`packer/` and `packer/tart-golden-image.pkr.hcl` now exist per Step 5), not mine; listed
  here for completeness since they surfaced in the same `just check` run.

**Why it is stuck:** I have no path to update or retire ledger entries — that file is explicitly
off-limits to every worker, including the one whose Step landing invalidated the entries.

**My best guess, explicitly labelled a guess:** these 8 claims should be retired or rewritten to assert
the post-Step-4 shape (e.g. a claim that `just build-golden` still resolves and runs the same body as
`just build`, verified via a `cli-help` probe rather than a literal-string grep on `--summary`/file
contents). That rewrite is a ledger-authoring decision, not a Justfile one — filing it here rather than
guessing at `.team/claims.jsonl` myself.

**Cost of guessing wrong:** if nobody updates the ledger, `just check` will permanently read below
311/311 (or drift further as 📦's and ✅'s work lands) even though the implementation matches spec 12
exactly — a false-red gate that trains the team to ignore `just check`'s exit code, which is the one
thing the G-series verification discipline exists to prevent.

**RESOLVED (👑 lead directive, mid-turn).** The lead corrected my alias direction: `build-golden:`
stays the **real** recipe at its original position/body (restored verbatim, re-pinning the two
`file-line` claims), and `build` becomes `alias build := build-golden` instead. `just --summary` only
ever lists real recipe names, never alias targets — so `justfile-has-build-golden` (file-contains) and
`CONTROL-xaudit-just-summary-lists-build-golden` (cli-help) both need the literal name on the real
side, not the alias side. Confirmed via `just check` post-fix: **311/311**, `justfile-has-build-golden`
and `CONTROL-xaudit-just-summary-lists-build-golden` both `[PASS]`. The other 6 stale claims the lead
mentioned were cleared separately (by the human, per the lead's message) — not something I touched.
Status flips to **CLOSED**.

---

## OQ-03 · harness-builder · BLOCKED-BY-SCOPE (cross-role: also 📦 packer-builder's territory)
**Filed by:** 🛠 harness-builder, while writing `tests/integration/conftest.py` (assertion-layer shadow
work) and before implementing `harness.py`'s SSH-based `up`/`apply`.
**Status:** BLOCKED-BY-SCOPE — does not block writing the hermetic test/harness *files* (per my brief,
"write the test files now, even if exercising them needs a live clone later"), but blocks every one of
them from actually *passing* against a real VM until resolved.
**Spec:** specs/macos-ci/12-tooling-and-agent-loop.md:191 (the `ssh_opts` variable block, spec-mandated
verbatim) vs. specs/macos-ci/08-dotfiles-test-harness.md §(b) step 4 vs. `packer/tart-golden-image.pkr.hcl`
(📦 packer-builder's file, read-only to me).

**Question:** Spec 12's `ssh_opts` (which Step 4 required me to carry verbatim into the Justfile — see
`Justfile`) includes `-o BatchMode=yes`. OpenSSH's `BatchMode=yes` disables **all** interactive/password
prompting client-side — it does not merely skip a TTY, it refuses to attempt password auth at all
without one, and `sshpass` cannot intercept a prompt that `BatchMode` prevents ssh from ever issuing. Yet
`packer/tart-golden-image.pkr.hcl` (read, not edited) sets only `ssh_username`/`ssh_password` = `admin`/
`admin` — no `authorized_keys` provisioning step, no keypair. So as configured today, a `BatchMode=yes`
SSH connection to a cloned VM has no working auth method: password auth is the only one the guest
accepts, and `BatchMode` refuses to use it. Separately, spec 08(b) step 4 states *"This harness stays on
plain key-based ssh"* — which is the design intent Step 12's `BatchMode=yes` matches — but nothing in
specs 01/02/08/12/13 documents *how* a key gets into the guest's `authorized_keys`. This is a real gap,
not a hypothetical: every one of `up`/`apply`/`run`/`ssh`/`exec`/`verify{,-pty}` — mine and 🐍's — depends
on it.
**What I tried:** Grepped every spec file for `authorized_keys`/`BatchMode`/`PasswordAuthentication`/
`ssh-keygen`/`PubkeyAuthentication` — the only hit is spec 12's own `ssh_opts` line. Read
`packer/tart-golden-image.pkr.hcl` directly (as-built by 📦, not a guess) — confirmed no key
provisioning exists there today.
**Why it is stuck:** The fix is either 📦's (add an idempotent step to the golden-image shell
provisioner that drops a repo-committed, throwaway keypair's public half into
`~/.ssh/authorized_keys` for `admin`) or a joint decision to drop `BatchMode=yes` and accept
`sshpass -p admin` instead (a real behavior change to a spec-mandated variable, which is not mine to
make unilaterally since Step 4 told me to carry it verbatim). Both cross into another role's owned files
or the spec text itself.
**My best guess, explicitly labelled a guess:** Option A (baked-in throwaway keypair, public half in the
golden image, private half committed under something like `harness/ssh/` and referenced by
`IdentityFile` in the `ssh_config_file` fixture/recipe) is more consistent with spec 08(b)'s stated
intent and with `BatchMode=yes` as already shipped — I've written `tests/integration/conftest.py` and
will write `harness.py`'s SSH calls assuming this shape, with a `<!-- UNVERIFIED -->`-equivalent
comment pointing back here, since I cannot confirm it without either a live VM or 📦 landing the
provisioning step.
**Cost of guessing wrong:** if Option A is wrong (e.g. the real intended mechanism is `sshpass` and
dropping `BatchMode=yes`), every `-m vm`/`-m pty` test and the entire `run`/`apply` main loop fails at
IMAGE-READY with a generic `Permission denied (publickey)`, which — per spec 12's own seed
failure-signature table — is exactly the kind of failure `vm-debug` exists to name, but nobody has
written the signature for it yet because the mechanism itself is undecided.

---

## OQ-04 · lead · RESOLUTION of OQ-02 (ledger retraction, human-authorized)

**Filed by:** 👑 lead, resolving 🛠 harness-builder's OQ-02.
**Status:** RESOLVED. `just check` confirmed back to 311/311 (exit 0) after this resolution.

OQ-02's diagnosis was exactly right, independently reached the same conclusion I had, and its "best
guess" (retire/rewrite the 8 claims to assert the post-Step-4 shape) is what happened. Since mutating
`.team/claims.jsonl` is a hard scope limit for this whole team (not just workers), I escalated to the
human before acting rather than deciding unilaterally. **The human authorized retiring the 6 genuinely
stale claims** (the ones asserting a defect that Step 4/Step 5 legitimately fixed):
`CONTROL-d1-packer-dir-does-not-exist`, `d2-justfile-has-no-build-ipsw-recipe`,
`justfile-has-no-images-recipe`, `golden-template-does-not-exist`, `xaudit-12-no-build-ipsw-recipe`,
`xaudit-12-no-images-recipe`. Each was edited in place following this file's own established
precedent (`d1-justfile-build-golden-names-absent-template`'s "[final merge] RETRACTED IN PART",
`d2-spec12-carries-the-phantom-recipe-retraction`'s "SUPERSEDES") — full history kept in the `claim`
text, `must_fail`/`polarity`/`control` stripped where the claim flipped from negative to positive
evidence, tagged `[macos-ci-build, 2026-07-10, RETIRED per human sign-off]`.

The remaining 2 (`justfile-has-build-golden`, `CONTROL-xaudit-just-summary-lists-build-golden`) needed
**no ledger change at all** — 🛠 harness-builder's own empirical finding (`just --summary` never lists
alias names) pointed at the real fix: swap which name is the real recipe. `build-golden` is now the real
recipe (unchanged body, unchanged line position — the `d1-justfile-build-golden-names-absent-template`
file-line pin stays valid), and `build` is the alias, so both the file-contains and cli-help claims pass
against reality with zero evidence edited.

Verified: `just check` exits 0, 311/311, confirmed twice (once immediately after the ledger edits before
🛠's alias swap landed — still 311/311 because 🛠's fix landed in the same window). `uv run pytest`
passes 50/50 as of the same check. Both pasted to the board (HG boundary).

---

## OQ-05 · lead · RESOLUTION of OQ-03 (SSH auth mechanism — golden image already mid-build)

**Filed by:** 👑 lead, resolving 🛠 harness-builder's OQ-03.
**Status:** RESOLVED, pending 🛠 implementation. Not yet re-verified against a live VM (IMAGE-GATED).

Real gap, correctly identified: the golden image (mid-build as of this writing, ~11% pulled, restarting
it now would cost another hour and there is no evidence its provisioning is wrong otherwise) has no
`authorized_keys` provisioning step — only `ssh_username`/`ssh_password` = `admin`/`admin`, which is
Packer's OWN build-time SSH communicator config, not a statement about the runtime harness's transport.
Spec 08(b) step 4's "this harness stays on plain key-based ssh" and spec 12's `ssh_opts` (`BatchMode=yes`,
spec-mandated verbatim) are the steady-state intent; neither documents *how* a key reaches the guest.

**Resolution — a two-phase auth model, no golden-image rebuild required:**

1. **Bootstrap (once per clone, immediately after `tart run` + first `tart ip`, before the pre-apply
   `chezmoi diff` lint):** one `sshpass -p admin ssh -o BatchMode=no -o StrictHostKeyChecking=no
   admin@<ip> 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys' < harness/ssh/id_ed25519_harness.pub`
   (or equivalent), using a **repo-committed, throwaway** ed25519 keypair generated once and checked in
   at `harness/ssh/` (public half only needs to be committed; if the private half is committed too — it
   must be, for `harness.py` to use it — it is a throwaway key with zero value outside this harness,
   scoped to disposable clones only, never the golden image itself, and never a secret in the
   `HOMEBREW_GITHUB_API_TOKEN` sense that 13-build-secrets.md's canary cares about).
2. **Steady state (everything after):** the existing spec-mandated `ssh_opts` with `BatchMode=yes` and
   `-i harness/ssh/id_ed25519_harness`, exactly as 08(b)/12 already specify — `chezmoi diff`, the apply
   command, all `-m vm`/`-m pty` tests.

This keeps the golden image and its in-progress build completely untouched (no packer template edit, no
relaunch, no circuit-breaker cost), matches 08(b)'s literal words ("stays on plain key-based ssh"), and
uses `sshpass`/password auth *only* for the one bootstrap write spec 03 already documents as a known
fallback mechanism — not as the harness's real transport.

**Action:** 🛠 harness-builder to implement `_harness_core.py`'s bootstrap-then-steady-state split and
generate/commit the throwaway keypair under `harness/ssh/`. Not gate-blocking for the HG (hermetic,
no VM); IS blocking for IMAGE-GATED steps 7-10. Flagged on the board.

---

## OQ-01 tracking note (non-blocking, low priority)

🐍 core-builder: `_doctor_core.version_at_least` needs zero-padding before tuple comparison (see OQ-01
above for the exact fix). Not urgent — masked by current inputs — but cheap to fix opportunistically
before GATE. Filed on the board's backlog as a should-fix, not a blocker.
