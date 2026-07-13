"""
build_cross_references.py — Phase 2, assemble the cross-reference library (no AI)

Ported from read-drawing-beta, repointed at the drawing-engine namespace. Claude
reads each sheet and lists what it references (other sheets via callouts, or
external docs like specs) in <set>/sheets/page_NNNN/refs.json; this script stamps
from_sheet, resolves/validates to_sheet against the known sheet set, demotes
unresolved targets to null (kept as coordination signals, not dropped), validates
enums, and writes <set>/machine/cross_references.json.

Per-page contract — <set>/sheets/page_NNNN/refs.json:
    {
      "references": [
        {
          "to_sheet": "C-501",          // a sheet_number in this set, or null
          "external_ref": null,          // set instead when target is outside the set
          "ref_type": "detail",
          "label": "3/C-501",
          "context": "Trench section for 24\" influent main.",
          "confidence": "high"
        }
      ]
    }

from_sheet is filled by this script from the page's classification.json. Runs
AFTER build_sheet_index.py.

Usage:
    python build_cross_references.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
REF_TYPES = {"detail", "section", "continuation", "schedule", "note", "spec",
             "match_line", "key_plan", "other"}
CONFIDENCE = {"high", "medium", "low"}


def main():
    p = argparse.ArgumentParser(description="Assemble cross-reference library (Phase 2).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    sheets_dir = set_dir / "sheets"
    machine = set_dir / "machine"
    split_manifest = sheets_dir / "manifest.json"
    if not split_manifest.exists():
        sys.exit(f"sheets/manifest.json not found in {sheets_dir} (run process_drawing.py first).")
    manifest = json.loads(split_manifest.read_text(encoding="utf-8"))

    known = set()
    index_path = machine / "sheet_index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        known = {s["sheet_number"] for s in idx.get("sheets", [])}
    else:
        print("NOTE: sheet_index.json not found; resolving from per-page files.", file=sys.stderr)

    references, errors = [], []
    unresolved = 0

    for page in manifest["pages"]:
        folder = page["folder"]
        class_path = sheets_dir / folder / "classification.json"
        refs_path = sheets_dir / folder / "refs.json"
        if not refs_path.exists():
            continue

        from_sheet = None
        if class_path.exists():
            try:
                from_sheet = json.loads(class_path.read_text(encoding="utf-8")).get("sheet_number")
            except json.JSONDecodeError:
                pass
        if from_sheet is None:
            from_sheet = f"UNK-{page['page']}"
            known.add(from_sheet)

        try:
            data = json.loads(refs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{folder}: refs.json is not valid JSON ({e})")
            continue

        for r in data.get("references", []):
            if r.get("ref_type") not in REF_TYPES:
                errors.append(f"{folder}: invalid ref_type {r.get('ref_type')!r}")
            if r.get("confidence") not in CONFIDENCE:
                errors.append(f"{folder}: invalid confidence {r.get('confidence')!r}")

            to_sheet = r.get("to_sheet")
            external_ref = r.get("external_ref")
            context = r.get("context", "")

            if to_sheet is not None and known and to_sheet not in known:
                context = (context + " " if context else "") + \
                    f"[unresolved: '{to_sheet}' not found in this set]"
                to_sheet = None
                unresolved += 1

            entry = {
                "from_sheet": from_sheet,
                "to_sheet": to_sheet,
                "ref_type": r.get("ref_type"),
                "label": r.get("label", ""),
                "context": context.strip(),
                "confidence": r.get("confidence"),
            }
            if external_ref:
                entry["external_ref"] = external_ref
            references.append(entry)

    if errors:
        print("VALIDATION ERRORS — nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    machine.mkdir(parents=True, exist_ok=True)
    (machine / "cross_references.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "references": references,
    }, indent=2), encoding="utf-8")
    print(f"Wrote cross_references.json ({len(references)} references) -> {machine}")
    if unresolved:
        print(f"  ({unresolved} unresolved target(s) -> to_sheet=null, kept as coordination signals)")


if __name__ == "__main__":
    main()
