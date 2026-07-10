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

  cli-help       `argv` (a read-only probe) emits `expect`. Runs from the repo
                 root, so `argv` may name a repo-relative path. An optional
                 `env` dict is layered over the environment for that one call.
                 Proves a CLI flag exists rather than being remembered.

                 A probe that only shows a flag *parses* is weak evidence — see
                 doc-contains. A probe that observes behaviour (`packer inspect`
                 printing `<sensitive>` instead of a secret) is strong evidence,
                 provided it is paired with a control proving the probe would
                 have shown the secret had masking been off.

  doc-index      `expect` (a doc path) appears in the site's own search index.
                 The index IS the authoritative page list: if a path is absent,
                 that page does not exist. This is the anti-G10 check.

  doc-contains   page `page`'s indexed text contains the `expect` sentence.
                 doc-index proves a page exists; this proves the page *says it*.
                 Needed because `cli-help` is unsound for backend questions: it
                 proves a flag parses, not that it works. `utmctl start --help`
                 advertises `--disposable` on a host that can only run
                 Apple-backend macOS guests, while /advanced/disposable/ states
                 "Disposable mode is only supported on QEMU backend."

  absent         target does NOT contain `expect`. For negative claims, e.g.
                 "zsh-dotfiles has no macOS asdf installer".

                 Like every negative, it is unfalsifiable alone: an EMPTY or
                 GUTTED file satisfies it just as well as an honest one. So an
                 `absent` record MUST carry a `control` naming a positive claim
                 over the same target. The master brief stated this requirement
                 for `cli-help` only (must_fail JOB 2); that was too narrow. It
                 is a property of ALL negative evidence — including a must_fail
                 `doc-contains` probe, which a page with EMPTY indexed text
                 satisfies just as well as an honest one. `check_structure`
                 enforces it, because a rule the tool does not enforce is a rule
                 that will be forgotten — including an exemption clause.

Any claim may set `"must_fail": true`. Its evidence is then required NOT to
verify. This is how the ledger tests its own oracle: one control claim asserts
the fabricated `settings-apple/devices/` URL, and if that ever starts passing,
the doc-index check has silently broken and every other doc-index claim is
worthless. A verifier nobody verifies is just a second thing to trust.

Two failure prefixes are never inverted by `must_fail`, because neither is
evidence about the claim itself:

  UNREACHABLE:   network down, binary absent, or the target file does not exist.
                 Says nothing about the world — and in particular, deleting a
                 control's target must never turn that control green.
  STRUCTURE:     a doc-contains page is missing from the index. Distinguishes
                 "the page vanished" from "the sentence vanished" — an upstream
                 reword must not read as a fabricated URL, and a control must
                 never "pass" merely because its page 404'd.

Exit codes:  0 all claims verified  ·  2 one or more failed
             ·  3 evidence unreachable (network/binary missing)  ·  4 usage error

Deliberately stdlib-only and side-effect-free: it reads files, runs --help, and
GETs two static JSON indexes. It mutates nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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


def norm_path(loc: str) -> str:
    """Normalize a doc path. Used for BOTH indexing and lookup — never inline this.

    The index stores `/advanced/disposable`; a claim naturally writes
    `/advanced/disposable/`. If store and lookup disagree by one slash, every
    lookup silently misses.
    """
    return ("/" + str(loc).split("#")[0].strip("/")).rstrip("/") or "/"


def norm_text(s: str) -> str:
    """Collapse whitespace and casefold. Indexed content carries ` . | ` separators."""
    return re.sub(r"\s+", " ", s).strip().casefold()


def index_texts(payload: object) -> dict[str, str]:
    """Map every documented path to its indexed text, folding #anchors into the parent page."""
    texts: dict[str, str] = {}

    def add(loc: object, title: object, body: object) -> None:
        path = norm_path(str(loc))
        texts[path] = f"{texts.get(path, '')} {title} {body}"

    if isinstance(payload, dict) and "docs" in payload:  # MkDocs Material (tart.run)
        for entry in payload["docs"]:
            if isinstance(entry, dict):
                add(entry.get("location", ""), entry.get("title", ""), entry.get("text", ""))
    elif isinstance(payload, dict):  # Just the Docs (docs.getutm.app)
        for entry in payload.values():
            if isinstance(entry, dict) and "relUrl" in entry:
                add(entry["relUrl"], entry.get("title", ""), entry.get("content", ""))

    return {p: norm_text(t) for p, t in texts.items()}


def index_paths(payload: object) -> set[str]:
    """Extract every documented path from a MkDocs or Just-the-Docs search index."""
    return set(index_texts(payload))


# ------------------------------------------------------------------ I/O shell


def _read(target: str) -> str:
    p = Path(target)
    if not p.is_absolute():
        p = REPO / p
    return p.read_text(encoding="utf-8", errors="replace")


def _fetch_index(site: str) -> dict[str, str]:
    url = DOC_INDEXES[site]
    req = urllib.request.Request(url, headers={"User-Agent": "verify-claims/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - fixed https allowlist
        return index_texts(json.loads(r.read().decode()))


def evaluate(claim: dict[str, Any], index_cache: dict[str, dict[str, str]]) -> Result:
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
            env = {**os.environ, **claim.get("env", {})}
            try:
                # cwd=REPO so argv may reference a repo-relative fixture path.
                proc = subprocess.run(  # noqa: S603
                    argv, capture_output=True, text=True, timeout=30, env=env, cwd=REPO
                )
            except FileNotFoundError:
                # The binary is absent. That is not evidence about the claim, so it must
                # carry the UNREACHABLE prefix — otherwise `must_fail` would invert
                # "packer isn't installed" into a silent pass.
                detail = f"UNREACHABLE: {argv[0]!r} not on PATH"
                return Result(cid, kind, False, detail, src)
            ok = check_contains(proc.stdout + proc.stderr, expect)
            return Result(cid, kind, ok, "" if ok else f"{' '.join(argv)} did not emit {expect!r}", src)

        if kind == "doc-index":
            site = claim["site"]
            if site not in index_cache:
                index_cache[site] = _fetch_index(site)
            want = norm_path(expect)
            ok = want in index_cache[site]
            hint = "" if ok else f"{want!r} is not in the {site} search index ({len(index_cache[site])} pages) — fabricated or moved"
            return Result(cid, kind, ok, hint, src)

        if kind == "doc-contains":
            site = claim["site"]
            if site not in index_cache:
                index_cache[site] = _fetch_index(site)
            page = norm_path(claim["page"])
            if page not in index_cache[site]:
                # Not a verdict on the sentence: the page itself is gone. Never inverted by must_fail.
                return Result(cid, kind, False, f"STRUCTURE: page {page!r} is not in the {site} index — fabricated or moved", src)
            ok = norm_text(expect) in index_cache[site][page]
            hint = "" if ok else f"page {page} exists but does not contain {expect!r} — upstream may have reworded; re-read it"
            return Result(cid, kind, ok, hint, src)

        return Result(cid, kind or "?", False, f"unknown evidence kind {kind!r}", src)

    except FileNotFoundError as e:
        # An absent target is not evidence about the claim, so it carries the
        # UNREACHABLE prefix and `must_fail` must never invert it. Without this,
        # DELETING a control's target file turns the control green: a must_fail
        # file-line claim on a missing file would "pass" for the wrong reason.
        # CONTROL-12-line-607-does-not-exist is exactly such a claim.
        return Result(cid, kind, False, f"UNREACHABLE: missing file: {e}", src)
    except (urllib.error.URLError, TimeoutError, subprocess.TimeoutExpired) as e:
        return Result(cid, kind, False, f"UNREACHABLE: {e}", src)
    except (KeyError, ValueError) as e:
        return Result(cid, kind, False, f"malformed claim: {e}", src)


def needs_control(claim: dict[str, Any]) -> bool:
    """Does this claim rest on NEGATIVE evidence, and therefore require a positive control?

    Negative evidence is unfalsifiable on its own. "The secret is absent from the
    output" is equally satisfied by no output at all; "the string is absent from the
    file" is equally satisfied by an EMPTY or GUTTED file. Either needs a control
    proving the same probe, over the same substrate, DOES surface something.

    Three shapes qualify:
      absent                       -- a negative over a file
      cli-help     + must_fail     -- a negative over a command's output
      doc-contains + must_fail     -- a negative over an indexed page: a page whose
                                      indexed text is EMPTY satisfies "the page does
                                      not say X" just as well as an honest one
      doc-index    + must_fail     -- a negative over a site's page list

    EXEMPT: the oracle controls. Those are `CONTROL-*` records of a doc kind. They
    ARE the controls -- they guard the doc oracles themselves -- and have no partner
    by construction.

    The exemption is on the ORACLE RECORD, not on the KIND. Exempting the whole
    `doc-contains` kind would have exempted `utm-no-tso-toggle-on-apple-virtualization`,
    a must_fail NEGATIVE PROBE whose pairing was stated in prose and enforced nowhere
    (GB5 / OQ-19). Nor is the exemption a bare `CONTROL-` name check: two genuine
    negatives are named `CONTROL-*` by history (`CONTROL-d1-packer-dir-does-not-exist`,
    a cli-help probe, and `CONTROL-tart-builder-clone-step-ignores-disk-format`, an
    absent probe). A name is not a warrant.
    """
    kind = claim.get("kind", "")
    is_oracle_control = str(claim.get("id", "")).startswith("CONTROL-") and kind in ("doc-index", "doc-contains")
    if is_oracle_control:
        return False
    if kind == "absent":
        return True
    return bool(claim.get("must_fail")) and kind in ("cli-help", "doc-contains", "doc-index")


def check_structure(claims: list[dict[str, Any]]) -> list[str]:
    """Reject a ledger whose negative claims lack a resolvable positive control.

    A rule the tool does not enforce is a rule that will be forgotten. The master
    brief stated the positive-control requirement for `cli-help` only; it is a
    property of all negative evidence. This is where that is made structural.
    """
    ids = {c.get("id") for c in claims}
    problems: list[str] = []
    for c in claims:
        cid = c.get("id", "<unnamed>")
        ctl = c.get("control")
        # A `control` is VALIDATED whenever it is present, even on a claim that does not
        # require one. Otherwise a claim could name a control that does not exist — or a
        # control that is itself a negative — and the pairing would be decoration.
        if not needs_control(c) and not ctl:
            continue
        if needs_control(c) and not ctl:
            problems.append(
                f"{cid}: kind={c.get('kind')!r}"
                f"{' must_fail' if c.get('must_fail') else ''} carries NEGATIVE evidence "
                f"but no `control` field. A negative claim without a positive control is "
                f"unfalsifiable — an empty file, an empty indexed page, or no output at "
                f"all, satisfies it."
            )
            continue
        names: list[str] = [ctl] if isinstance(ctl, str) else list(ctl or [])
        for name in names:
            if name not in ids:
                problems.append(f"{cid}: `control` names {name!r}, which is not a claim id in this ledger")
            elif name == cid:
                problems.append(f"{cid}: `control` names itself; a claim cannot be its own control")
            else:
                partner = next(c2 for c2 in claims if c2.get("id") == name)
                if partner.get("must_fail"):
                    problems.append(
                        f"{cid}: `control` names {name!r}, which is itself a must_fail claim. "
                        f"A control must be a POSITIVE claim that verifies."
                    )
    return problems


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

    structural = check_structure(claims)
    if structural:
        print("STRUCTURAL REJECTION — negative evidence without a positive control:", file=sys.stderr)
        for p in structural:
            print(f"  {p}", file=sys.stderr)
        print(
            f"\n{len(structural)} offending claim(s). Every `absent` record, and every must_fail "
            f"`cli-help` / `doc-contains` / `doc-index` probe, must carry a `control` naming a "
            f"positive claim id in this ledger. Only `CONTROL-*` records of a doc kind — the "
            f"oracle guards, which have no partner by construction — are exempt.",
            file=sys.stderr,
        )
        return USAGE

    cache: dict[str, dict[str, str]] = {}
    results: list[Result] = []
    for c in claims:
        r = evaluate(c, cache)
        if c.get("must_fail"):
            # A control claim: its evidence is required NOT to verify.
            # Never invert an UNREACHABLE (network down) or a STRUCTURE (page gone) —
            # neither is evidence about the claim, and inverting either would mask a
            # broken oracle as a pass.
            if r.detail.startswith(("UNREACHABLE", "STRUCTURE")):
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
