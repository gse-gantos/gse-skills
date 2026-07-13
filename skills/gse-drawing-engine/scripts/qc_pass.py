"""
qc_pass.py — Phase 3, the QC gate (no AI for the deterministic checks)

The reliability gate before a set becomes queryable. Runs five checks, assigns a
GREEN/YELLOW/RED level to every sheet, promotes the ledger
(classified → complete / failed), sets run_status, writes qc_status.json, and
refreshes coverage. A set isn't QUERY-able until this runs (the router only
reaches QUERY once run_status is complete/partial with no pending/classified).

Checks:
  1. Schema validation — classification enums + the FS-3 confidence ceiling;
     cross-reference enums.
  2. Coverage reconciliation — split pages == ledger sheets == index sheets.
  3. Broken-reference report — unresolved structural callouts (to_sheet null,
     no external_ref).
  4. Confidence-ceiling enforcement — no record may exceed its sheet ceiling.
  5. Per-sheet QC level (see rules below).

QC level rules (a sheet that needed a visual fallback or failed validation can
NOT be green — FS-4 / drawing-library discipline):
  RED    schema error on the sheet · extraction_confidence low · classification
         confidence low · "scanned but claimed clean" (≈no text yet source_type
         pdf_text + high) — an under-extracted sheet.
  YELLOW visual fallback (source_type image_visual/crop/ocr) · extraction_
         confidence medium · schedule view not read at high confidence.
  GREEN  clean vector-text sheet, high confidence, no flags.

Promotion: GREEN/YELLOW → complete (queryable; YELLOW flagged for verification);
RED → failed (kept for coverage honesty, never silently dropped).

Usage:
    python qc_pass.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_VERSION = "1.0"

DISCIPLINES = {"General", "Civil", "Structural", "Architectural", "Mechanical",
               "Process", "Electrical", "Instrumentation", "Landscape", "Other"}
CONF = {"high", "medium", "low"}
ORDER = {"low": 0, "medium": 1, "high": 2}
VISUAL = {"image_visual", "crop", "ocr"}
REF_TYPES = {"detail", "section", "continuation", "schedule", "note", "spec",
             "match_line", "key_plan", "other"}


def load(machine, name, default):
    p = machine / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def main():
    p = argparse.ArgumentParser(description="QC gate (Phase 3).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    sheets_dir = set_dir / "sheets"

    ledger = load(machine, "manifest.json", None)
    if not ledger:
        sys.exit(f"machine/manifest.json not found in {set_dir}.")
    cls = load(machine, "sheet_classification.json", {"sheets": []})
    idx = load(machine, "sheet_index.json", {"sheets": []})
    xref = load(machine, "cross_references.json", {"references": []})
    split = load(sheets_dir, "manifest.json", {"pages": [], "page_count": 0})

    cls_by_sn = {s.get("sheet_number"): s for s in cls.get("sheets", [])}
    text_by_page = {pg["page"]: pg for pg in split.get("pages", [])}

    schema_errors = []

    # 1+4. schema + ceiling on classification
    for s in cls.get("sheets", []):
        sn = s.get("sheet_number", "?")
        if s.get("discipline") not in DISCIPLINES:
            schema_errors.append(f"{sn}: invalid discipline {s.get('discipline')!r}")
        if s.get("confidence") not in CONF:
            schema_errors.append(f"{sn}: invalid confidence {s.get('confidence')!r}")
        if s.get("extraction_confidence") not in CONF:
            schema_errors.append(f"{sn}: invalid extraction_confidence {s.get('extraction_confidence')!r}")
        c, ec = s.get("confidence"), s.get("extraction_confidence")
        if c in ORDER and ec in ORDER and ORDER[c] > ORDER[ec]:
            schema_errors.append(f"{sn}: confidence '{c}' exceeds extraction_confidence '{ec}' (FS-3 ceiling)")
    # cross-ref enums
    for r in xref.get("references", []):
        if r.get("ref_type") not in REF_TYPES:
            schema_errors.append(f"cross-ref from {r.get('from_sheet')}: bad ref_type {r.get('ref_type')!r}")

    # 2. reconciliation
    split_pages = split.get("page_count", len(split.get("pages", [])))
    ledger_sheets = len(ledger.get("sheets", []))
    index_sheets = len(idx.get("sheets", []))
    recon_notes = []
    if split_pages != ledger_sheets:
        recon_notes.append(f"split pages ({split_pages}) != ledger sheets ({ledger_sheets})")
    # index counts only classified sheets; it should be <= ledger and == classified count
    classified_count = sum(1 for s in ledger.get("sheets", [])
                           if s.get("processing_state") in ("classified", "complete", "failed"))
    if index_sheets and index_sheets != classified_count:
        recon_notes.append(f"index sheets ({index_sheets}) != classified sheets ({classified_count})")
    recon_ok = not recon_notes

    # 3. broken references
    broken = [{"from_sheet": r.get("from_sheet"), "label": r.get("label"),
               "ref_type": r.get("ref_type"), "context": r.get("context", "")}
              for r in xref.get("references", [])
              if r.get("to_sheet") is None and not r.get("external_ref")
              and r.get("ref_type") in {"detail", "section", "continuation", "match_line", "key_plan"}]

    # 5. per-sheet QC + promotion
    sheet_errs = {}
    for e in schema_errors:
        sn = e.split(":")[0].strip()
        sheet_errs.setdefault(sn, []).append(e)

    qc_sheets = []
    counts = {"green": 0, "yellow": 0, "red": 0, "unclassified": 0}
    any_failed = any_pending = False

    for s in ledger.get("sheets", []):
        sn = s.get("sheet_number")
        page = s.get("page")
        state = s.get("processing_state", "pending")
        crec = cls_by_sn.get(sn)

        if crec is None or state == "pending":
            counts["unclassified"] += 1
            any_pending = True
            qc_sheets.append({"sheet_number": sn or f"page-{page}", "qc": "unclassified",
                              "reasons": ["no classification.json / still pending"]})
            continue

        reasons = []
        level = "green"
        ec = crec.get("extraction_confidence")
        conf = crec.get("confidence")
        stype = crec.get("source_type")
        view = crec.get("view_type")
        pg = text_by_page.get(page, {})
        low_text = pg.get("likely_scanned", False) or pg.get("text_chars", 1) < 20

        def demote(to, why):
            nonlocal level
            if to == "red" or (to == "yellow" and level == "green"):
                level = to
            reasons.append(why)

        if sn in sheet_errs:
            demote("red", f"schema error(s): {'; '.join(sheet_errs[sn])}")
        if ec == "low":
            demote("red", "extraction_confidence low")
        if conf == "low":
            demote("red", "classification confidence low")
        if low_text and stype == "pdf_text" and ec == "high":
            demote("red", "under-extracted: ~no text on sheet but claims clean high-confidence pdf_text")
        if stype in VISUAL:
            demote("yellow", f"visual fallback (source_type {stype}) — cannot be green")
        if ec == "medium":
            demote("yellow", "extraction_confidence medium")
        if view == "schedule" and ec != "high":
            demote("yellow", "schedule sheet not read at high confidence (dense-table risk)")

        counts[level] += 1
        if level == "red":
            s["processing_state"] = "failed"
            any_failed = True
        else:
            s["processing_state"] = "complete"
        if not reasons:
            reasons = ["clean"]
        qc_sheets.append({"sheet_number": sn, "qc": level, "reasons": reasons})

    # run_status
    if any_pending:
        run_status = "building"
    elif any_failed:
        run_status = "partial"
    else:
        run_status = "complete"
    ledger["run_status"] = run_status
    ledger["generated"] = args.date or ledger.get("generated", "")
    (machine / "manifest.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    overall = "red" if (schema_errors or not recon_ok) else \
              ("green" if run_status == "complete" and counts["yellow"] == 0 else "partial")

    qc_status = {
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "overall": overall,
        "run_status": run_status,
        "schema_errors": schema_errors,
        "reconciliation": {"split_pages": split_pages, "ledger_sheets": ledger_sheets,
                           "index_sheets": index_sheets, "ok": recon_ok, "notes": recon_notes},
        "broken_references": broken,
        "counts": counts,
        "sheets": qc_sheets,
    }
    (machine / "qc_status.json").write_text(json.dumps(qc_status, indent=2), encoding="utf-8")

    # refresh coverage from post-QC states
    subprocess.run([sys.executable, str(HERE / "build_coverage.py"),
                    "--set-dir", str(set_dir), "--date", args.date],
                   capture_output=True, text=True)

    print(f"QC: overall={overall}, run_status={run_status} — "
          f"{counts['green']} green, {counts['yellow']} yellow, {counts['red']} red, "
          f"{counts['unclassified']} unclassified")
    if schema_errors:
        print(f"  SCHEMA ERRORS ({len(schema_errors)}): " + "; ".join(schema_errors[:5]))
    if not recon_ok:
        print(f"  RECONCILIATION: " + "; ".join(recon_notes))
    if broken:
        print(f"  BROKEN REFERENCES ({len(broken)}): "
              + ", ".join(f"{b['label']} on {b['from_sheet']}" for b in broken[:5]))


if __name__ == "__main__":
    main()
