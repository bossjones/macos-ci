# Contributor

How this repo's own build was orchestrated, and the concrete coordination scaffolding used to run it —
for anyone contributing to `macos-ci` itself, especially via a multi-agent ("boss-cmux") workflow.

| Doc | What it covers |
|---|---|
| [boss-cmux-workflow.md](boss-cmux-workflow.md) | The general, reusable three-stage pattern (research → verify → build) for kicking off large agent-driven work, illustrated with this repo's own `prompts/` lineage. Start here if you've never used this pattern before. |
| [team-coordination-mechanics.md](team-coordination-mechanics.md) | The concrete, current `.team/` scaffolding this repo uses: dispatch briefs, the board state machine, and the `claims.jsonl` ledger. Read this before running or extending a boss-cmux team against this repo. |
| [cost-and-token-report.md](cost-and-token-report.md) | Token/cost accounting from the 7-pane build run that implemented `specs/macos-ci.md` steps 1–14 — useful for tuning future runs, not an invoice. |

This repo's own [`CLAUDE.md`](../../CLAUDE.md) documents the verification philosophy behind the claims
ledger (evidence kinds, the `must_fail` self-check pattern, `<!-- UNVERIFIED -->` markers) in full —
`team-coordination-mechanics.md` links there rather than repeating it.

See also: [../architecture/](../architecture/) for what actually got built, and [../tutorials/](../tutorials/) for how to use it.
