I want to keep artifacts of boss-cmux commands in this folder so that we can find patterns and figure out easier ways to prompt claude to create them.

| Prompt | What it's for |
|---|---|
| [`macos-ci-research-team.md`](macos-ci-research-team.md) | **Superseded.** The 6-pane run that wrote the spec tree. Archived verbatim with its false `G10` ground truth intact — it is the evidence for why the verify run exists. |
| [`macos-ci-verify-team.md`](macos-ci-verify-team.md) | **Done.** The 8-pane run that *proves* the specs. Read-only verification is mandatory, ground truths are claims to refute, and `just check` is the only definition of done. |
| [`macos-ci-build-team.md`](macos-ci-build-team.md) | **Current.** The 7-pane run that *builds* what the specs describe — `specs/macos-ci.md` steps 1–14, TDD red-first, the real golden-image Packer build, a 📡 log-watcher with a transient-vs-fatal triage table, and an orchestrator heartbeat (60s polls, 2-min reports, 3-min stall probes). |

Read them in that order. The pair is a before/after on prompt design: the first forbade verification and
shipped a fabricated URL; the second makes truth executable via `tools/verify_claims.py` and `just check`.
