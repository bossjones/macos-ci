# 🍎 tart-core — YOUR BRIEF

**You are `tart-core`.** Surface `C74E75F0-FC92-422A-9985-7C65019C8FA1` (`pane:44`).
**Read [`_RULES.md`](_RULES.md) in full first.** Then this.

## You own
- `specs/macos-ci/01-tart-core.md`
- `specs/macos-ci/02-packer-tart-builder.md`

## Your job

**Re-verify every CLI verb and every Packer field against a source.** `tart` 2.32.1 **is installed**.
`tart --help` and `tart <verb> --help` are allowed — **USE THEM. A flag you remember is not a flag that
exists.** For `tart.run` pages, query the search index first (`_RULES.md` §3).

Propose `cli-help` claims for **every flag the specs depend on**: `--no-graphics`, `--vnc`,
`--vnc-experimental`, `--dir`, and the verbs `clone`, `ip`, `delete`, `run`, `pull`.
Two already exist (`tart-has-vnc-experimental`, `tart-has-no-graphics`, `tart-ip-has-agent-resolver`) —
don't duplicate; **extend**.

### ⚠️ READ G19 BEFORE YOU TOUCH `02`

The Tart builder field reference lives at
`https://developer.hashicorp.com/packer/integrations/cirruslabs/tart/latest/components/builder/tart`.
It is **ABSENT FROM THE HASHICORP SITEMAP** (0 of 337 `/packer/*` entries) **and it RETURNS 200.**

> **If you "refute" it by grepping the sitemap, you have reproduced G10 in reverse and the run has
> failed.** Verify with `curl -sS -o /dev/null -w '%{http_code}' <url>`, or by reading
> `cirruslabs/packer-plugin-tart`'s `.web-docs/` — a clone is at
> `/Users/bossjones/dev/cirruslabs/packer-plugin-tart`. **Never refute a page you have not fetched.**

`packer` **IS** installed (v1.15.4 — G14 was retracted; the brief that said otherwise was wrong).
`packer inspect <dir>` is **ALLOWED**. `packer build` / `packer init` are **FORBIDDEN**.

Fields the docs page is silent on stay `<!-- UNVERIFIED -->` **+ an OQ**. Note `02:73` already flags
`pull_concurrency` as documented `boolean` where a concurrency **count** is implied — **do not silently
"correct" it**; either verify it against `.web-docs/` or leave the marker and cite an OQ.

### Also yours
- **G8** — headless on macOS 15+ has a keychain requirement; nested virt needs M3/M4 **and a Linux
  guest**; prebuilt `ghcr.io` images cover macOS 12–26; default creds `admin`/`admin`.
  **Those creds are PUBLIC and MUST NEVER be marked `sensitive`** (see G16 — `sensitive` masks *values*,
  so marking `"admin"` sensitive would rewrite every `admin` in every log).
- `01:68` carries an `<!-- UNVERIFIED -->` on the exact `ghcr.io` image path/tag syntax. Try to settle it
  from the quick-start page via the index; if you cannot, **the marker stays** and you open an OQ.
- **G1 / G3** (with 🏭 tart-ci): no Terraform provider for tart; `packer-plugin-tart` is tart-only.

## Then: CROSS-AUDIT 🖥 utm's files
`05-utm-automation.md`, `06-utm-macos-guest.md`, `07-utm-settings-appendix.md`.
**Do not edit them** — file CONFLICTs in the backlog under `### 🍎 tart-core`.

## Warning inherited from the lead
The master brief has already been caught with a **false line-number claim** (D5) and a **false CLI
claim** (`rename-tab`). **Re-derive every line number with `sed -n 'Np' <file>` before citing it.**
The prior lead pass hallucinated `12-…:607` in a file of 535 lines. Do not be the second.

Propose claims to `.team/proposed/tart-core.jsonl`, and **dry-run them**:
```bash
uv run tools/verify_claims.py .team/proposed/tart-core.jsonl
```

End with exactly:
```
TASK-DONE: tart-core | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
