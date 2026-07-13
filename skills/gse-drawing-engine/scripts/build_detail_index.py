"""
build_detail_index.py — Phase 2, the detail catalogue (no AI)

Ported from read-drawing-beta, repointed at the drawing-engine namespace.
Assembles <set>/machine/detail_index.json (+ a readable <set>/views/detail_index.md)
cataloguing the individual details defined across the set and where each is
referenced. Deterministic.

Inputs (in <set>/machine/, from earlier steps):
  - sheet_classification.json : each sheet's `details_defined` [{number, title}]
  - cross_references.json     : used to find where each detail is referenced

A detail's reference is inferred when a cross-reference points to the defining
sheet (`to_sheet`) and the detail number appears in the callout label.

Usage:
    python build_detail_index.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"


def _num_key(s):
    m = re.match(r"\d+", str(s))
    return (int(m.group()) if m else 9999, str(s))


def main():
    p = argparse.ArgumentParser(description="Assemble the detail index (Phase 2).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    cls_path = machine / "sheet_classification.json"
    if not cls_path.exists():
        sys.exit(f"sheet_classification.json not found in {machine} (run build_sheet_index.py first).")
    cls = json.loads(cls_path.read_text(encoding="utf-8"))

    refs = []
    xref_path = machine / "cross_references.json"
    if xref_path.exists():
        refs = json.loads(xref_path.read_text(encoding="utf-8")).get("references", [])

    details = []
    for sheet in cls.get("sheets", []):
        sn = sheet.get("sheet_number")
        for d in sheet.get("details_defined", []) or []:
            number = str(d.get("number", "")).strip()
            title = d.get("title", "")
            if not number:
                continue
            referenced_by = []
            for r in refs:
                if r.get("to_sheet") != sn:
                    continue
                label = r.get("label", "") or ""
                if re.search(r"(?<!\d)" + re.escape(number) + r"(?!\d)", label):
                    fs = r.get("from_sheet")
                    if fs and fs not in referenced_by:
                        referenced_by.append(fs)
            details.append({
                "detail_id": f"{sn}/{number}",
                "sheet_number": sn,
                "number": number,
                "title": title,
                "referenced_by": referenced_by,
            })

    details.sort(key=lambda d: (d["sheet_number"], _num_key(d["number"])))

    machine.mkdir(parents=True, exist_ok=True)
    (machine / "detail_index.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "detail_count": len(details),
        "details": details,
    }, indent=2), encoding="utf-8")

    views = set_dir / "views"
    views.mkdir(parents=True, exist_ok=True)
    lines = [f"# Detail Index — {set_dir.name}", "",
             f"_Generated {args.date or '(no date)'} · {len(details)} details_", ""]
    if not details:
        lines.append("_No details catalogued (no `details_defined` captured during classification)._")
    else:
        lines += ["| Detail | Title | Defined on | Referenced by |", "|---|---|---|---|"]
        for d in details:
            ref = ", ".join(d["referenced_by"]) if d["referenced_by"] else "—"
            lines.append(f"| {d['number']} | {d['title']} | {d['sheet_number']} | {ref} |")
    (views / "detail_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote detail_index.json ({len(details)} details) -> {machine}")
    print(f"Wrote detail_index.md -> {views}")


if __name__ == "__main__":
    main()
