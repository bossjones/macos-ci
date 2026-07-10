# 🏭 tart-ci — YOUR BRIEF

**You are `tart-ci`.** Surface `258F06DE-B1F1-4C12-90D4-7CF0288EC30C` (`pane:45`).
**Read [`_RULES.md`](_RULES.md) in full first.** Then this.

## You own
- `specs/macos-ci/03-tart-ci-and-orchard.md`
- `specs/macos-ci/04-tart-licensing-risk.md`

## Your job — you hold the highest-risk numbers in the repo

**G4's dollar figures and core thresholds are the numbers a human signs off on.** Re-verify **every
tier number** against `tart.run/licensing` (find the page via the search index — `_RULES.md` §3), and
**propose a ledger claim per threshold**.

The claim as inherited (**attack it, do not assume it**):

> Tart is **Fair Source**, actively enforced as of the **Oct 2025** announcement. Free on personal
> workstations; commercial free **≤ 100 CPU cores** (tart) / **4 Orchard workers**;
> **Gold $12K/yr** (500 / 20), **Platinum $36K/yr** (3000 / 200), **Diamond ~$12/core/yr**.
> **No open-source exemption.**

**Numbers rot.** If any moved:
- **RETRACT loudly** in the backlog under `### 🏭 tart-ci`, and
- **open a `NEEDS-HUMAN` OQ.** A licence-cost change is a decision the human makes, **not one you make.**

Confirm the **Oct-2025 enforcement announcement** still says what `04` claims. The blog post is
`tart.run/blog/2025/10/27/press-release-cirrus-labs-successfully-enforces-its-fair-source-license/`
(it resolved 200 in the lead's baseline `link-check`). Use `doc-contains`, not just `doc-index`:
**a URL that resolves is not a sentence that is true.**

### `03` specifics
- `cirrus` **IS installed**. `cirrus --help` and `cirrus run --help` are **allowed** — use them.
  `cirrus-run-has-artifacts-dir` and `cirrus-cli-artifacts-dir-documented` already pass; extend, don't
  duplicate.
- `03:53` carries `<!-- UNVERIFIED -->` on the **exact CWD-copy mechanism** (rsync vs tart's `--dir`
  mount). Try to settle it from the Cirrus CLI docs; if you cannot, **the marker stays** + an OQ.
- `03:144` carries `<!-- UNVERIFIED -->` on **self-hosted Cirrus CI**. Same rule.
- **G1** — no Terraform provider exists for tart or UTM; tart's orchestration story is **Orchard**.
  `utmapp/UTM#3618` is the open IaC request; the maintainer says *"a long way off"* (tracked in `#3718`).
  Both URLs resolved 200 in the baseline. Verify the **maintainer's sentence**, not just the URL.
- **G2** — the `tonyyo11` blog uses Terraform to manage **JAMF PRO resources, not VMs**. The repo
  README's "Terraform" line is **aspirational**. Read it and confirm, or retract.

## Then: CROSS-AUDIT 🔐 secrets' files
`13-build-secrets.md` — the densest spec in the repo (13 backing claims).
Pay special attention to the **two `must_fail`/CONTROL pairs**. Ask the question secrets is also asked:
**is each control vacuous?** *"The secret is absent from the output"* is equally satisfied by **no output
at all**. Confirm the control asserts a literal that the **same `argv`+`env`** genuinely prints.
**Do not edit `13`** — file CONFLICTs in the backlog under `### 🏭 tart-ci`.

## Warning inherited from the lead
The master brief has been caught with a **false line-number claim** (D5) and a **false CLI claim**
(`rename-tab`). **Re-derive every line number with `sed -n 'Np' <file>`.** The prior lead pass
hallucinated `12-…:607` in a 535-line file.

Propose claims to `.team/proposed/tart-ci.jsonl`, and **dry-run them**:
```bash
uv run tools/verify_claims.py .team/proposed/tart-ci.jsonl
```

End with exactly:
```
TASK-DONE: tart-ci | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
