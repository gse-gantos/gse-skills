"""
build_sheet_index.py — Phase 1, assemble + validate the sheet index (no AI)

Ported from read-drawing-beta, repointed at the drawing-engine namespace and
extended with the FS-3 provenance contract. Reads the per-page classification.json
files Claude wrote under <set>/sheets/page_NNNN/ and assembles two source-of-truth
files into <set>/machine/:

  - sheet_index.json          identity + file locations (cheap; query loads first)
  - sheet_classification.json content matrix (what's on each sheet) + provenance

It also STAMPS the processing ledger (<set>/machine/manifest.json): for every
classified page it fills sheet_number / discipline / extraction_confidence and
advances processing_state pending → classified. (QC promotes classified → complete
in Phase 3.) This script validates and assembles only — Claude does the
understanding.

Per-page contract — <set>/sheets/page_NNNN/classification.json — see
references/classification_protocol.md. New vs. read-drawing-beta:
  - extraction_confidence : high|medium|low  (sheet-level CONFIDENCE CEILING, FS-3)
  - source_type           : how the sheet was primarily read (FS-3)
  - tag_details (optional) : [{tag,type,size,service,evidence}] cheap attributes
                             captured while the .txt was open (PRD Q2 lean) — stored
                             raw, NOT split into registers (that is v2).

Usage:
    python build_sheet_index.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
                                [--allow-missing]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "1.0"

DISCIPLINES = {
    "General", "Civil", "Structural", "Architectural", "Mechanical",
    "Process", "Electrical", "Instrumentation", "Landscape", "Other",
}
DOC_TYPES = {"contract_drawing", "addendum", "as_built", "shop_drawing", "cut_sheet", "sketch"}
CONFIDENCE = {"high", "medium", "low"}
VIEW_TYPES = {"plan", "section", "detail", "elevation", "diagram", "schedule",
              "profile", "mixed", "other"}
SOURCE_TYPES = {"pdf_text", "bluebeam_text", "bluebeam_markup", "image_visual",
                "crop", "ocr", "user_note", "inference"}

REQUIRED = ["sheet_number", "title", "discipline", "document_type", "confidence",
            "summary", "view_type", "extraction_confidence", "source_type"]


def validate_record(rec, folder):
    errs = []
    for key in REQUIRED:
        if key not in rec:
            errs.append(f"{folder}: missing required field '{key}'")
    if rec.get("discipline") not in DISCIPLINES:
        errs.append(f"{folder}: invalid discipline {rec.get('discipline')!r}")
    if rec.get("document_type") not in DOC_TYPES:
        errs.append(f"{folder}: invalid document_type {rec.get('document_type')!r}")
    if rec.get("confidence") not in CONFIDENCE:
        errs.append(f"{folder}: invalid confidence {rec.get('confidence')!r}")
    if rec.get("extraction_confidence") not in CONFIDENCE:
        errs.append(f"{folder}: invalid extraction_confidence {rec.get('extraction_confidence')!r}")
    if rec.get("source_type") not in SOURCE_TYPES:
        errs.append(f"{folder}: invalid source_type {rec.get('source_type')!r}")
    if rec.get("view_type") not in VIEW_TYPES:
        errs.append(f"{folder}: invalid view_type {rec.get('view_type')!r}")
    for d in rec.get("secondary_disciplines", []) or []:
        if d not in DISCIPLINES:
            errs.append(f"{folder}: invalid secondary_discipline {d!r}")
    # confidence ceiling (FS-3): a record's confidence cannot exceed the sheet's
    # extraction_confidence.
    order = {"low": 0, "medium": 1, "high": 2}
    c, ec = rec.get("confidence"), rec.get("extraction_confidence")
    if c in order and ec in order and order[c] > order[ec]:
        errs.append(f"{folder}: confidence '{c}' exceeds extraction_confidence "
                    f"'{ec}' (FS-3 ceiling violated)")
    return errs


def main():
    p = argparse.ArgumentParser(description="Assemble sheet index/classification (Phase 1).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    p.add_argument("--allow-missing", action="store_true",
                   help="Write partial output even if some pages lack classification.json.")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    sheets_dir = set_dir / "sheets"
    machine_dir = set_dir / "machine"
    split_manifest = sheets_dir / "manifest.json"
    if not split_manifest.exists():
        sys.exit(f"sheets/manifest.json not found in {sheets_dir} (run process_drawing.py first).")
    manifest = json.loads(split_manifest.read_text(encoding="utf-8"))
    if not args.date:
        print("NOTE: no --date supplied; 'generated' will be empty.", file=sys.stderr)

    index_sheets, class_sheets = [], []
    errors, missing = [], []
    seen_numbers = {}
    page_to_meta = {}  # page -> (sheet_number, discipline, extraction_confidence)

    for page in manifest["pages"]:
        folder = page["folder"]
        class_path = sheets_dir / folder / "classification.json"
        if not class_path.exists():
            missing.append(folder)
            continue
        try:
            rec = json.loads(class_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{folder}: classification.json is not valid JSON ({e})")
            continue

        errors.extend(validate_record(rec, folder))

        sn = rec.get("sheet_number", f"UNK-{page['page']}")
        seen_numbers.setdefault(sn, []).append(folder)
        page_to_meta[page["page"]] = (sn, rec.get("discipline"), rec.get("extraction_confidence"))

        # paths are relative to the SET dir (machine/ and sheets/ are siblings)
        paths = {k: f"sheets/{v}" for k, v in page["paths"].items()}

        index_sheets.append({
            "sheet_number": sn,
            "title": rec.get("title", ""),
            "discipline": rec.get("discipline"),
            "document_type": rec.get("document_type"),
            "pdf_page": page["source_page"],
            "source_pdf": page.get("source_pdf", ""),
            "confidence": rec.get("confidence"),
            "paths": paths,
        })
        class_sheets.append({
            "sheet_number": sn,
            "discipline": rec.get("discipline"),
            "secondary_disciplines": rec.get("secondary_disciplines", []),
            "summary": rec.get("summary", ""),
            "key_elements": rec.get("key_elements", []),
            "systems": rec.get("systems", []),
            "equipment_tags": rec.get("equipment_tags", []),
            "tag_details": rec.get("tag_details", []),
            "key_callouts": rec.get("key_callouts", []),
            "details_defined": rec.get("details_defined", []),
            "scale": rec.get("scale", ""),
            "view_type": rec.get("view_type"),
            "scope_relevant": rec.get("scope_relevant", True),
            "confidence": rec.get("confidence"),
            "extraction_confidence": rec.get("extraction_confidence"),
            "source_type": rec.get("source_type"),
            "notes": rec.get("notes", ""),
        })

    dupes = {sn: f for sn, f in seen_numbers.items() if len(f) > 1}
    for sn, folders in dupes.items():
        print(f"WARNING: sheet_number {sn!r} appears on {len(folders)} pages: {', '.join(folders)}",
              file=sys.stderr)

    if errors:
        print("VALIDATION ERRORS — nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    if missing and not args.allow_missing:
        print(f"MISSING classification.json for {len(missing)} page(s):", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print("Classify those pages, or re-run with --allow-missing for partial output.",
              file=sys.stderr)
        sys.exit(1)

    machine_dir.mkdir(parents=True, exist_ok=True)
    (machine_dir / "sheet_index.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "source_pdfs": list(manifest.get("source_pdfs", [])),
        "sheet_count": len(index_sheets),
        "sheets": index_sheets,
    }, indent=2), encoding="utf-8")
    (machine_dir / "sheet_classification.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "sheets": class_sheets,
    }, indent=2), encoding="utf-8")

    stamp_ledger(machine_dir, page_to_meta, args.date)

    print(f"Wrote sheet_index.json + sheet_classification.json ({len(index_sheets)} sheets) -> {machine_dir}")
    if missing:
        print(f"  (partial: {len(missing)} page(s) skipped for missing classification.json)")
    if dupes:
        print(f"  ({len(dupes)} duplicate sheet_number(s) flagged above)")


def stamp_ledger(machine_dir, page_to_meta, date):
    """Advance processing_state pending → classified and fill sheet_number etc."""
    ledger_path = machine_dir / "manifest.json"
    if not ledger_path.exists():
        return
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    now = datetime.now().strftime("%Y-%m-%d") if not date else date
    for s in ledger.get("sheets", []):
        meta = page_to_meta.get(s.get("page"))
        if not meta:
            continue
        sn, disc, ec = meta
        s["sheet_number"] = sn
        s["discipline"] = disc
        s["extraction_confidence"] = ec
        if s.get("processing_state") in (None, "pending", "stale"):
            s["processing_state"] = "classified"
        s["last_processed"] = now
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
