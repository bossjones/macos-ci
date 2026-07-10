# 🔐 secrets — YOUR BRIEF

**You are `secrets`.** Surface `F63FA6BD-690A-4A15-8CA0-3EFBE557C34C` (`pane:48`).
**Read [`_RULES.md`](_RULES.md) in full first.** Then this.

## You own
- `specs/macos-ci/13-build-secrets.md` — **the densest spec in the repo: 13 backing claims.**

## Verify G15, G16, G17 line by line

- **G15 — deleting a secret from the guest does not erase it.** `rm` unlinks an inode; it does not zero
  the blocks. Plaintext written to the guest survives in `~/.tart/vms/<name>/`'s disk image and
  `strings` still finds it. **Therefore never write a build secret to the guest filesystem:** pass it
  through the shell provisioner's `environment_vars` with `use_env_var_file = false` (**`true` writes a
  tempfile INTO the guest**), and there is nothing to clean up.
- **G16 — Packer's `sensitive = true` masks VALUES, not VARIABLES.** It redacts **every occurrence of
  the string**, anywhere in the output, including under `PACKER_LOG=1`. **So never mark a common word
  sensitive:** `ssh_password = "admin"` marked sensitive would rewrite **every** `admin` in **every**
  log to `<sensitive>`. G8's `admin/admin` creds are **public** — leave them plain.
- **G17 — the build needs no secrets beyond one token.** No SSH key, no `~/.gitconfig`, no
  `~/.ssh/config`, no `HOMEBREW_GITHUB_PACKAGES_TOKEN`. Every repo and tap involved is **public**; the
  one `git@github.com:` tap URL is rewritten to anonymous HTTPS via
  `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_n` / `GIT_CONFIG_VALUE_n`. `HOMEBREW_GITHUB_API_TOKEN` is wanted
  **only** to lift GitHub's 60-req/hr unauthenticated REST cap to 5,000.

`packer inspect tests/fixtures/packer-sensitive` is **ALLOWED** and is what four of your claims already
run. **`packer build` and `just build-golden` are FORBIDDEN.**

## YOUR HARDEST JOB — the two `must_fail`/CONTROL pairs

Pairs: `packer-sensitive-hides-secret` ↔ `CONTROL-packer-inspect-prints-plain-literals`, and the
`PACKER_LOG=1` overlay pair `packer-sensitive-hides-secret-under-debug-log` ↔
`CONTROL-packer-debug-log-prints-plain-literals`.

**Reason explicitly, in the spec, about WHY the bare negative probe is unfalsifiable alone:**

> *"The secret does not appear in the output"* is **equally satisfied by no output at all.**

So confirm that each control asserts a literal (`plain_FIXTURE_CONTROL`) that the **same `argv` and the
same `env`** genuinely prints. **A pair whose control is vacuous is a green check that means nothing —
say so, out loud, in the spec.** If you find one vacuous, that is a **CONFLICT**, not a nit.

**Never delete or weaken a `must_fail` claim.** Only 🔬 ledger edits `.team/claims.jsonl`; you *propose*.

## The two markers at `13:51` and `13:54` MUST STAY UNVERIFIED

The lead re-verified both citations (they are correct, unlike OQ-02's) and proposed `file-line` claims
pinning them: `g15-hdiutil-caveat-marker-pinned-at-13-51`, `oq01-asif-marker-pinned-at-13-54`.

- `13:51` — the residue reproduction used **`hdiutil` on the HOST against a UDIF/APFS image**, *not*
  inside a tart VM against its own disk image.
- `13:54` — whether the same holds for **`disk_format = "asif"`** (macOS 26+, **sparse**) is unknown.

Unlink-does-not-zero is generic to block-backed filesystems, but the **tart-specific** reproduction is
not on record and neither can be settled without booting a VM. **See OQ-01. The markers stay.**

## YOU OWN DEFECT D1 (with 🧪 harness)

`Justfile:44` invokes `packer/tart-golden-image.pkr.hcl` — **the `packer/` directory does not exist.**
`just build-golden` is broken today.

**HUMAN DECISION, already made: document only.**
- **Rewrite `13` to say the template IS ABSENT**, rather than describing it as though it were on disk.
- **Do NOT author it.** `packer build`/`init` are forbidden, so not one line could be validated.
- **Do NOT touch the `Justfile`** — the lead owns it; the only edit this run is line 63.
- **OQ-04 · NEEDS-HUMAN** is already filed: *guard `build-golden`, or author the template?*

## Then: CROSS-AUDIT 🍎 tart-core's files
`01-tart-core.md`, `02-packer-tart-builder.md`.
**Before you touch `02`, read G19 in `_RULES.md` §3.** The Tart builder field reference is **absent from
the HashiCorp sitemap and returns 200**. **Refuting it by grepping the sitemap is G10 running backwards
and fails the run.** Never refute a page you have not fetched.
**Do not edit them** — file CONFLICTs in the backlog under `### 🔐 secrets`.

## Warning inherited from the lead
The master brief has been caught with a **false line-number claim** (D5) and a **false CLI claim**
(`rename-tab`). **Re-derive every line number with `sed -n 'Np' <file>`.**

Propose claims to `.team/proposed/secrets.jsonl`, and **dry-run them**:
```bash
uv run tools/verify_claims.py .team/proposed/secrets.jsonl
```

End with exactly:
```
TASK-DONE: secrets | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
