#!/usr/bin/env python3
"""integrity_check.py — post-QC gates 1 & 2 as enforcement (added 2026-07-02).

Gate 1 (write-integrity): every machine/*.json parses; JSON string values and
markdown views are scanned for truncation tells (mid-word endings, unclosed
quotes/parens, dangling articles). Gate 2 (banner consistency): every views/*.md
coverage banner must agree with machine/coverage_status.json.

Usage:  python integrity_check.py --set-dir "<.../drawing-db/<set>>"
Exit 0 = all gates pass. Exit 2 = failures found (printed, machine-readable
lines prefixed FAIL/WARN). A FAIL blocks promotion to query-ready.

Motivation (from a QA audit): rfi_candidates.json shipped values ending
'...gallery basemen' and "...('FALL PROTECTION DETA"; views/rfi_candidates.md
shipped a 'PARTIAL - 0/0 sheets' banner over a 54/54-complete set.
"""
import argparse, json, re, sys
from pathlib import Path

DANGLING = {"the", "a", "an", "of", "to", "and", "or", "for", "with", "per",
            "at", "on", "in", "is", "are", "shall", "be", "by", "from"}

def truncation_tells(s, strict=False):
    """Return (level, reason) if a text value looks cut off, else None.

    Structural tells (unclosed delimiter, dangling function word, hyphen end)
    are FAIL everywhere. The softer 'no sentence terminator' tell is FAIL only
    for strict files (RFI/coordination/open-question records, whose prose
    fields are written as sentences) and WARN elsewhere (classification
    evidence is legitimately note-style). Heuristic by nature: a truncation
    landing on a real word ('...gallery basemen') is only catchable in strict
    files; the blind re-read remains the semantic backstop.
    """
    t = s.rstrip()
    if not t:
        return None
    fails, warns = [], []
    if t.count("(") > t.count(")") or t.count("[") > t.count("]"):
        fails.append("unclosed delimiter")
    if t.endswith("-"):
        fails.append("ends on hyphen")
    last = re.split(r"\s+", t)[-1].strip("*_`\"'")
    if last.lower() in DANGLING:
        fails.append(f"ends on dangling word '{last}'")
    if len(t) > 40 and re.search(r"[A-Za-z]$", t) and not re.search(
            r"[.!?:;)\]\|\"']$", t) and not re.fullmatch(r"[A-Z0-9 \-/&.']{1,80}", t):
        (fails if strict else warns).append("no sentence terminator (possible mid-word cut)")
    if fails:
        return ("FAIL", "; ".join(fails + warns))
    if warns:
        return ("WARN", "; ".join(warns))
    return None

def walk_strings(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set-dir", required=True)
    a = ap.parse_args()
    set_dir = Path(a.set_dir)
    machine, views = set_dir / "machine", set_dir / "views"
    fails, warns = [], []

    # --- Gate 1a: every machine JSON parses ---
    cov = None
    for jf in sorted(machine.glob("*.json")) if machine.is_dir() else []:
        try:
            data = json.loads(jf.read_text(errors="replace"))
        except Exception as e:
            fails.append(f"FAIL json-parse {jf.name}: {e}")
            continue
        if jf.name == "coverage_status.json":
            cov = data
        # --- Gate 1b: truncation tells inside prose-bearing fields ---
        for path, s in walk_strings(data):
            key = path.rsplit(".", 1)[-1].split("[")[0]
            if key in {"evidence", "description", "suggested_action", "summary",
                       "issue", "question", "notes", "action", "impact", "title"}:
                strict = jf.name in {"rfi_candidates.json", "coordination_issues.json",
                                     "open_questions.json"}
                # sheet titles are verbatim all-caps labels — skip the soft tell there
                if key == "title" and not strict:
                    continue
                r = truncation_tells(s, strict=strict)
                if r:
                    level, reason = r
                    line = f"{level} truncated-string {jf.name} {path}: {reason} :: ...{s[-60:]!r}"
                    (fails if level == "FAIL" else warns).append(line)

    # --- Gate 1c: markdown views end on a complete line ---
    for md in sorted(views.glob("*.md")) if views.is_dir() else []:
        txt = md.read_text(errors="replace").rstrip()
        if not txt:
            fails.append(f"FAIL empty-view {md.name}")
            continue
        last = txt.splitlines()[-1].strip()
        if re.search(r"[A-Za-z]$", last) and not re.search(r"[.!?:)\]\|`]$", last) \
           and not last.startswith("#") and len(last.split()) > 3:
            fails.append(f"FAIL md-tail {md.name}: last line looks cut off :: {last[-70:]!r}")

    # --- Gate 2: banner vs machine coverage ---
    if cov is None:
        warns.append("WARN no coverage_status.json — banner check skipped (run build_coverage.py)")
    else:
        want_proc, want_tot = cov.get("processed", 0), cov.get("total_sheets", 0)
        pat = re.compile(r"COVERAGE:\s*(\w+)[^0-9]*?(\d+)\s*/\s*(\d+)\s+sheets", re.I)
        for md in sorted(views.glob("*.md")) if views.is_dir() else []:
            head = "\n".join(md.read_text(errors="replace").splitlines()[:8])
            m = pat.search(head)
            if not m:
                warns.append(f"WARN no-banner {md.name}: no parsable coverage banner in header")
                continue
            state, proc, tot = m.group(1).lower(), int(m.group(2)), int(m.group(3))
            if (proc, tot) != (want_proc, want_tot):
                fails.append(f"FAIL banner-mismatch {md.name}: banner {proc}/{tot} vs machine {want_proc}/{want_tot}")
            if cov.get("current") and state != "complete":
                fails.append(f"FAIL banner-state {md.name}: machine says complete, banner says {state}")

    for w in warns: print(w)
    for f in fails: print(f)
    if fails:
        print(f"\nINTEGRITY: FAIL — {len(fails)} failure(s), {len(warns)} warning(s). Do not promote this set.")
        sys.exit(2)
    print(f"INTEGRITY: PASS — {len(warns)} warning(s).")

if __name__ == "__main__":
    main()
