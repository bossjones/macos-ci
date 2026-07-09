#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""verify_claims — re-execute the evidence behind every spec claim.

A spec is only as good as its citations. This tool reads a claims ledger
(`.team/claims.jsonl`) and, for each claim, re-runs the evidence that is supposed
to support it. A claim whose evidence no longer reproduces is a FAIL, whether it
was wrong when written or drifted since.

This exists because a prior research run shipped ground truth "G10: these four
docs.getutm.app URLs are 404 — do not fetch, do not cite". Three were live, and
one (`settings-apple/devices/`) had never existed at all: it was fabricated. The
"do not fetch" rule is precisely what prevented its disproof. A rule that forbids
verification manufactures confidence instead of truth.

Evidence kinds, cheapest first:

  file-contains  target file contains the `expect` substring.
                 Proves a claim about a local working tree.

  file-line      line `line` of `target` contains `expect`.
                 Catches hallucinated line:number citations — the single most
                 common way a plausible spec turns out to be fiction.

  cli-help       `argv` (a read-only --help/--version probe) emits `expect`.
                 Proves a CLI flag exists rather than being remembered.

  doc-index      `expect` (a doc path) appears in the site's own search index.
                 The index IS the authoritative page list: if a path is absent,
                 that page does not exist. This is the anti-G10 check.

  absent         target does NOT contain `expect`. For negative claims, e.g.
                 "zsh-dotfiles has no macOS asdf installer".

Any claim may set `"must_fail": true`. Its evidence is then required NOT to
verify. This is how the ledger tests its own oracle: one control claim asserts
the fabricated `settings-apple/devices/` URL, and if that ever starts passing,
the doc-index check has silently broken and every other doc-index claim is
worthless. A verifier nobody verifies is just a second thing to trust.

Exit codes:  0 all claims verified  ·  2 one or more failed
             ·  3 evidence unreachable (network/binary missing)  ·  4 usage error

Deliberately stdlib-only and side-effect-free: it reads files, runs --help, and
GETs two static JSON indexes. It mutates nothing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

DOC_INDEXES = {
    "tart": "https://tart.run/search/search_index.json",
    "utm": "https://docs.getutm.app/assets/js/search-data.json",
}

OK, FAILED, UNREACHABLE, USAGE = 0, 2, 3, 4


@dataclass
class Result:
    id: str
    kind: str
    ok: bool
    detail: str
    file: str = ""


# ---------------------------------------------------------------- pure helpers
# These take already-fetched text. No I/O. Unit-testable without a network.


def check_contains(haystack: str, expect: str) -> bool:
    return expect in haystack


def check_absent(haystack: str, expect: str) -> bool:
    return expect not in haystack


def check_line(text: str, line_no: int, expect: str) -> tuple[bool, str]:
    lines = text.splitlines()
    if not 1 <= line_no <= len(lines):
        return False, f"line {line_no} out of range (file has {len(lines)})"
    actual = lines[line_no - 1]
    if expect in actual:
        return True, f"line {line_no}: {actual.strip()[:70]}"
    return False, f"line {line_no} is {actual.strip()[:70]!r}, expected to contain {expect!r}"


def index_paths(payload: object) -> set[str]:
    """Extract every documented path from a MkDocs or Just-the-Docs search index."""
    paths: set[str] = set()
    if isinstance(payload, dict) and "docs" in payload:  # MkDocs Material (tart.run)
        for entry in payload["docs"]:
            paths.add("/" + str(entry.get("location", "")).split("#")[0].strip("/"))
    elif isinstance(payload, dict):  # Just the Docs (docs.getutm.app)
        for entry in payload.values():
            if isinstance(entry, dict) and "relUrl" in entry:
                paths.add(str(entry["relUrl"]).split("#")[0].rstrip("/"))
    return {p.rstrip("/") or "/" for p in paths}


# ------------------------------------------------------------------ I/O shell


def _read(target: str) -> str:
    p = Path(target)
    if not p.is_absolute():
        p = REPO / p
    return p.read_text(encoding="utf-8", errors="replace")


def _fetch_index(site: str) -> set[str]:
    url = DOC_INDEXES[site]
    req = urllib.request.Request(url, headers={"User-Agent": "verify-claims/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - fixed https allowlist
        return index_paths(json.loads(r.read().decode()))


def evaluate(claim: dict[str, Any], index_cache: dict[str, set[str]]) -> Result:
    kind = claim.get("kind", "")
    cid = claim.get("id", "<unnamed>")
    expect = claim.get("expect", "")
    src = claim.get("file", "")

    try:
        if kind == "file-contains":
            ok = check_contains(_read(claim["target"]), expect)
            return Result(cid, kind, ok, "" if ok else f"{claim['target']} lacks {expect!r}", src)

        if kind == "absent":
            ok = check_absent(_read(claim["target"]), expect)
            return Result(cid, kind, ok, "" if ok else f"{claim['target']} unexpectedly contains {expect!r}", src)

        if kind == "file-line":
            ok, detail = check_line(_read(claim["target"]), int(claim["line"]), expect)
            return Result(cid, kind, ok, detail, src)

        if kind == "cli-help":
            argv = claim["argv"]
            if isinstance(argv, str):
                argv = argv.split()
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=30)  # noqa: S603
            ok = check_contains(proc.stdout + proc.stderr, expect)
            return Result(cid, kind, ok, "" if ok else f"{' '.join(argv)} did not emit {expect!r}", src)

        if kind == "doc-index":
            site = claim["site"]
            if site not in index_cache:
                index_cache[site] = _fetch_index(site)
            want = "/" + expect.strip("/")
            ok = want.rstrip("/") in index_cache[site]
            hint = "" if ok else f"{want!r} is not in the {site} search index ({len(index_cache[site])} pages) — fabricated or moved"
            return Result(cid, kind, ok, hint, src)

        return Result(cid, kind or "?", False, f"unknown evidence kind {kind!r}", src)

    except FileNotFoundError as e:
        return Result(cid, kind, False, f"missing: {e}", src)
    except (urllib.error.URLError, TimeoutError, subprocess.TimeoutExpired) as e:
        return Result(cid, kind, False, f"UNREACHABLE: {e}", src)
    except (KeyError, ValueError) as e:
        return Result(cid, kind, False, f"malformed claim: {e}", src)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("ledger", nargs="?", default=str(REPO / ".team" / "claims.jsonl"))
    ap.add_argument("--json", action="store_true", help="machine-readable output for agents")
    args = ap.parse_args()

    ledger = Path(args.ledger)
    if not ledger.exists():
        print(f"no ledger at {ledger}", file=sys.stderr)
        return USAGE

    claims = [json.loads(ln) for ln in ledger.read_text().splitlines() if ln.strip() and not ln.startswith("//")]
    if not claims:
        print("ledger is empty — a spec with no checkable claims is a spec nobody verified", file=sys.stderr)
        return USAGE

    cache: dict[str, set[str]] = {}
    results: list[Result] = []
    for c in claims:
        r = evaluate(c, cache)
        if c.get("must_fail"):
            # A control claim: its evidence is required NOT to verify.
            # Never invert an UNREACHABLE — that would mask a broken oracle as a pass.
            if r.detail.startswith("UNREACHABLE"):
                pass
            else:
                r = Result(
                    r.id,
                    r.kind,
                    not r.ok,
                    "" if not r.ok else "CONTROL PASSED — the oracle is broken; every other claim of this kind is now unreliable",
                    r.file,
                )
        results.append(r)

    failed = [r for r in results if not r.ok]
    unreachable = [r for r in failed if r.detail.startswith("UNREACHABLE")]

    if args.json:
        print(json.dumps({"total": len(results), "failed": len(failed), "claims": [asdict(r) for r in results]}, indent=2))
    else:
        for r in results:
            mark = "PASS" if r.ok else "FAIL"
            line = f"[{mark}] {r.id}  ({r.kind})"
            if r.detail:
                line += f"\n         {r.detail}"
            print(line)
        print(f"\n{len(results) - len(failed)}/{len(results)} claims verified")

    if unreachable and len(unreachable) == len(failed):
        return UNREACHABLE
    return FAILED if failed else OK


if __name__ == "__main__":
    sys.exit(main())
