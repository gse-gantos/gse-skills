#!/usr/bin/env python3
"""tag_sweep.py — post-QC gate 3 as enforcement (added 2026-07-02).

Sweeps every sheets/page_NNNN/page_NNNN.txt for tag-shaped strings and compares
against machine/tag_index.json. Tags present in a sheet's text layer but absent
from the index are coverage gaps.

Usage:  python tag_sweep.py --set-dir "<.../drawing-db/<set>>" [--extra-prefix W1 ...]
Exit 0 = index covers everything found. Exit 2 = gaps found (listed).

Motivation (from a QA audit): the W1-CLF-* family on sheet I-4's text layer
(including two probable source typos worth an RFI) was entirely missing from
tag_index.json.
"""
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path

# Core instrument/equipment tag shapes seen on GSE water/wastewater sets:
#   01-CLF-0301B, W1-ILCP-14001, FIT-0301D, LSHH-0301, MCC-2M, P-101, C-011
BASE_PATTERNS = [
    r"\b[0-9]{2}-[A-Z]{2,5}-[0-9]{3,6}[A-Z]?\b",       # 01-CLF-0301B
    r"\b[A-Z][0-9]?-[A-Z]{2,5}-[0-9]{3,6}[A-Z]?\b",     # W1-ILCP-14001
    r"\b[A-Z]{2,5}-[0-9]{3,6}[A-Z]{0,2}\b",              # FIT-0301D, LSHH-0301
    r"\b[A-Z]{1,3}-[0-9]{2,4}\b",                        # P-101, C-011, S-001
]
# Sheet numbers / detail refs / spec sections we must NOT count as equipment tags:
NOISE = re.compile(
    r"^(?:[A-Z]{1,2}-\d{1,3})$"      # bare sheet numbers like D-1, E-16, S-919
)
SPECISH = re.compile(r"^\d{2}-\d{2}-\d{2}$")

def normalize(t):
    return t.strip().upper()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set-dir", required=True)
    ap.add_argument("--extra-prefix", nargs="*", default=[],
                    help="extra tag prefixes to force-match, e.g. W1")
    ap.add_argument("--min-len", type=int, default=8,
                    help="ignore matches shorter than this unless prefix-forced (filters sheet refs)")
    a = ap.parse_args()
    set_dir = Path(a.set_dir)

    idx_file = set_dir / "machine" / "tag_index.json"
    if not idx_file.exists():
        print("FAIL no tag_index.json — run build_tag_index.py first"); sys.exit(2)
    idx = json.loads(idx_file.read_text(errors="replace"))
    tags_obj = idx.get("tags", idx)
    if isinstance(tags_obj, dict):            # schema: {"TAG": {...}}
        indexed = {normalize(t) for t in tags_obj.keys()}
    elif isinstance(tags_obj, list):          # schema: [{"tag": "TAG", ...}]
        indexed = {normalize(r.get("tag", "")) for r in tags_obj if isinstance(r, dict)}
    else:
        print("FAIL unrecognized tag_index.json schema"); sys.exit(2)
    indexed.discard("")

    # one alternation, longest/most-specific first, so "W1-ILCP-14001" wins and
    # its "ILCP-14001" substring is not double-counted
    combined = re.compile("|".join(f"(?:{p})" for p in BASE_PATTERNS))
    found = defaultdict(set)   # tag -> {sheet folders}
    for txt in sorted(set_dir.glob("sheets/page_*/page_*.txt")):
        text = txt.read_text(errors="replace")
        page = txt.parent.name
        taken = []              # claimed spans, longest matches claim first
        cands = sorted(combined.finditer(text), key=lambda m: -(m.end() - m.start()))
        for m in cands:
            if any(m.start() < e and m.end() > s0 for s0, e in taken):
                continue        # inside/overlapping a longer match already taken
            taken.append((m.start(), m.end()))
            t = normalize(m.group(0))
            if SPECISH.match(t) or NOISE.match(t):
                continue
            forced = any(t.startswith(px.upper() + "-") for px in a.extra_prefix)
            if len(t) < a.min_len and not forced:
                continue
            found[t].add(page)

    missing = {t: sorted(ps) for t, ps in found.items() if t not in indexed}
    # group by family (prefix up to last numeric block) for readable output
    fams = defaultdict(list)
    for t in sorted(missing):
        fam = re.sub(r"[0-9]+[A-Z]?$", "*", t)
        fams[fam].append(t)

    print(f"text-layer tags found: {len(found)} | indexed: {len(indexed)} | missing from index: {len(missing)}")
    for fam, ts in sorted(fams.items()):
        pages = sorted({p for t in ts for p in missing[t]})
        print(f"GAP family {fam}: {', '.join(ts)}  (sheets: {', '.join(pages)})")
    if missing:
        print("\nTAG SWEEP: FAIL — add these to the index (re-classify the sheets) or log an open question.")
        sys.exit(2)
    print("TAG SWEEP: PASS")

if __name__ == "__main__":
    main()
