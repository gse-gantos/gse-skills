"""
build_tag_index.py — Phase 1, the inverted tag index (no AI)

read-drawing-beta had no tag index — a tag question meant scanning every sheet's
equipment_tags array at query time. This builds the precomputed inverted lookup
(tag → the sheets it appears on) once, so a tag query is a single dict lookup
(the low-token win, PRD §5.5).

Reads  <set>/machine/sheet_classification.json  and, if present,
<set>/machine/cross_references.json  to stamp `referenced_by`. Writes
<set>/machine/tag_index.json  and a readable  <set>/views/tag_index.md.

Each tag entry carries the FS-3 provenance contract in aggregate:
  - `sheets`           : every sheet whose classification lists the tag
  - `disciplines`      : disciplines of those sheets
  - `confidence`       : the MINIMUM extraction_confidence across its sheets — the
                         confidence ceiling, so a tag is never more trusted than
                         the least-trusted sheet it was read from
  - `attributes`       : cheap type/size/service captured in tag_details (PRD Q2);
                         {} when none were captured
  - `evidence`         : [{sheet, source_type}] per sheet
  - `referenced_by`    : sheets that cross-reference a sheet defining the tag
                         (filled only when cross_references.json exists; Phase 2)

Usage:
    python build_tag_index.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
_ORDER = {"low": 0, "medium": 1, "high": 2}
_REV = {0: "low", 1: "medium", 2: "high"}


def min_conf(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return _REV[min(_ORDER.get(a, 0), _ORDER.get(b, 0))]


def main():
    p = argparse.ArgumentParser(description="Build the inverted tag index (Phase 1).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    cls_path = machine / "sheet_classification.json"
    if not cls_path.exists():
        sys.exit(f"sheet_classification.json not found in {machine} (run build_sheet_index.py first).")
    cls = json.loads(cls_path.read_text(encoding="utf-8"))

    xrefs = []
    xref_path = machine / "cross_references.json"
    if xref_path.exists():
        xrefs = json.loads(xref_path.read_text(encoding="utf-8")).get("references", [])

    # tag -> aggregate record
    tags = {}
    for sheet in cls.get("sheets", []):
        sn = sheet.get("sheet_number")
        disc = sheet.get("discipline")
        ec = sheet.get("extraction_confidence")
        stype = sheet.get("source_type")
        details = {d.get("tag"): d for d in sheet.get("tag_details", []) if d.get("tag")}

        for tag in sheet.get("equipment_tags", []) or []:
            tag = str(tag).strip()
            if not tag:
                continue
            t = tags.setdefault(tag, {
                "tag": tag, "sheets": [], "disciplines": [], "confidence": None,
                "attributes": {}, "evidence": [], "referenced_by": [],
            })
            if sn and sn not in t["sheets"]:
                t["sheets"].append(sn)
            if disc and disc not in t["disciplines"]:
                t["disciplines"].append(disc)
            t["confidence"] = min_conf(t["confidence"], ec)
            t["evidence"].append({"sheet": sn, "source_type": stype})
            # cheap attributes (first non-empty wins; conflicts noted)
            d = details.get(tag)
            if d:
                for k in ("type", "size", "service"):
                    v = (d.get(k) or "").strip()
                    if v and not t["attributes"].get(k):
                        t["attributes"][k] = v

    # referenced_by: a sheet that cross-references a sheet on which the tag appears
    if xrefs:
        for t in tags.values():
            defining = set(t["sheets"])
            for r in xrefs:
                if r.get("to_sheet") in defining:
                    fs = r.get("from_sheet")
                    if fs and fs not in defining and fs not in t["referenced_by"]:
                        t["referenced_by"].append(fs)

    tag_list = sorted(tags.values(), key=lambda x: x["tag"])
    out = {
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "tag_count": len(tag_list),
        "tags": tag_list,
    }
    machine.mkdir(parents=True, exist_ok=True)
    (machine / "tag_index.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # readable projection
    views = set_dir / "views"
    views.mkdir(parents=True, exist_ok=True)
    lines = [f"# Tag Index — {set_dir.name}", "",
             f"_Generated {args.date or '(no date)'} · {len(tag_list)} tags_", ""]
    if not tag_list:
        lines.append("_No equipment tags captured during classification._")
    else:
        lines += ["| Tag | Sheets | Discipline(s) | Type | Size | Confidence |",
                  "|---|---|---|---|---|---|"]
        for t in tag_list:
            a = t["attributes"]
            lines.append(
                f"| {t['tag']} | {', '.join(t['sheets']) or '—'} | "
                f"{', '.join(t['disciplines']) or '—'} | {a.get('type','—')} | "
                f"{a.get('size','—')} | {t['confidence'] or '—'} |")
    (views / "tag_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote tag_index.json ({len(tag_list)} tags) -> {machine}")
    print(f"Wrote tag_index.md -> {views}")


if __name__ == "__main__":
    main()
