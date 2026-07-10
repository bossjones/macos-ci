# verifier fixtures — the tool verified BY the tool

`tools/verify_claims.py` was, until GAP3/OQ-35, the one artifact in this repo with no verifier.
`verify-claims-missing-file-is-unreachable` grepped its **source** for the string
`UNREACHABLE: missing file:` while its prose asserted a **behaviour**: move that literal into a
comment, delete the `except FileNotFoundError` handler, and the claim stayed green.

Its three trust-bearing behaviours — `must_fail` inversion, `UNREACHABLE:`/`STRUCTURE:`
non-inversion, and `needs_control()` structural rejection — were adversarially tested **by hand**
and recorded **as prose**. That is the evidence class of Defect A, where a previous lead faked the
gate with a bracketed paraphrase. It differs only in the honesty of the transcriber, and honesty is
not an evidence kind.

Each ledger here is executed by a `cli-help` claim in `.team/claims.jsonl` that asserts on the
tool's **real stdout/stderr**. Every negative probe carries its positive control on the SAME argv.
