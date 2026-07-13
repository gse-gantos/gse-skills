"""
test_query.py — Phase 4 acceptance test (query interface + FS-1 coverage gap).

Acceptance (PRD Phase 4):
  - a tag query returns the right sheets via the precomputed index
  - a query against a pending/failed sheet returns a coverage_gap signal instead
    of a wrong/empty answer or a silent reprocess
Plus: NL query finds the right sheet; drawings.md entry point carries the
coverage banner; a query never mutates the ledger (no silent reprocess).

Real pipeline on a synthetic 2-sheet set (C-101 complete, C-102 forced to FAILED
so it's a known unanswerable sheet).

Run:  python test_query.py    Exit: 0 pass / 1 fail.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAIL = []


def run(script, *args):
    return subprocess.run([sys.executable, str(HERE / script), *map(str, args)],
                          capture_output=True, text=True)


def make_pdf(path):
    import fitz
    doc = fitz.open()
    for b in ["C-101 YARD PIPING PLAN\nP-101 PUMP\nINV 92.50 STA 12+50",
              "C-102 NOTES\nGENERAL NOTES"]:
        page = doc.new_page(width=792, height=612)
        page.insert_text((72, 72), b, fontsize=12)
    doc.save(str(path)); doc.close()


def rec(sn, disc, tags, callouts, stype, conf, ec):
    return {"sheet_number": sn, "title": sn, "discipline": disc,
            "document_type": "contract_drawing", "confidence": conf,
            "extraction_confidence": ec, "source_type": stype,
            "secondary_disciplines": [], "summary": f"{sn} summary.",
            "key_elements": [], "systems": [], "equipment_tags": tags,
            "tag_details": [], "key_callouts": callouts, "details_defined": [],
            "scale": "", "view_type": "plan", "scope_relevant": True, "notes": ""}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    import fitz  # noqa
    with tempfile.TemporaryDirectory() as tmp:
        sub = Path(tmp) / "sub"
        (sub / "drawings").mkdir(parents=True)
        pdf = sub / "drawings" / "q.pdf"
        make_pdf(pdf)
        set_dir = sub / "drawing-db" / "q"
        machine = set_dir / "machine"
        sheets_dir = set_dir / "sheets"

        run("init_namespace.py", "--set-dir", set_dir, "--date", "2026-06-22")
        run("process_drawing.py", pdf, "--set-dir", set_dir, "--date", "2026-06-22")
        folders = [p["folder"] for p in load(sheets_dir / "manifest.json")["pages"]]
        # C-101 clean/complete; C-102 extraction_confidence low → QC RED → failed
        (sheets_dir / folders[0] / "classification.json").write_text(
            json.dumps(rec("C-101", "Civil", ["P-101"], ["INV 92.50"], "pdf_text", "high", "high")), encoding="utf-8")
        (sheets_dir / folders[1] / "classification.json").write_text(
            json.dumps(rec("C-102", "General", [], [], "image_visual", "low", "low")), encoding="utf-8")

        run("build_sheet_index.py", "--set-dir", set_dir, "--date", "2026-06-22")
        run("build_tag_index.py", "--set-dir", set_dir, "--date", "2026-06-22")
        run("qc_pass.py", "--set-dir", set_dir, "--date", "2026-06-22")
        run("build_summary.py", "--set-dir", set_dir, "--date", "2026-06-22")

        states = {s["sheet_number"]: s["processing_state"]
                  for s in load(machine / "manifest.json")["sheets"]}
        if states.get("C-101") != "complete" or states.get("C-102") != "failed":
            FAIL.append(f"setup states wrong: {states}")

        # 1. TAG query via precomputed index returns the right sheet
        r = run("query_drawing.py", "--set-dir", set_dir, "--equipment", "P-101", "--json")
        out = json.loads(r.stdout)
        if out.get("result") != "tag_lookup" or out.get("via") != "tag_index":
            FAIL.append(f"equipment query did not use tag_index: {out.get('result')}/{out.get('via')}")
        if out.get("sheets") != ["C-101"]:
            FAIL.append(f"tag query wrong sheets: {out.get('sheets')}")

        # 2. NL query finds C-101
        r = run("query_drawing.py", "--set-dir", set_dir, "where is the influent pump P-101", "--json")
        out = json.loads(r.stdout)
        cands = [c["sheet_number"] for c in out.get("candidates", [])]
        if "C-101" not in cands:
            FAIL.append(f"NL query did not surface C-101: {cands}")

        # snapshot ledger to prove no silent reprocess on a gap query
        before = (machine / "manifest.json").read_text(encoding="utf-8")

        # 3. FS-1: --show on a FAILED sheet → coverage_gap, exit 4, no reprocess
        r = run("query_drawing.py", "--set-dir", set_dir, "--show", "C-102", "--json")
        if r.returncode != 4:
            FAIL.append(f"--show on failed sheet should exit 4, got {r.returncode}")
        out = json.loads(r.stdout)
        if out.get("result") != "coverage_gap" or "C-102" not in out.get("missing_sheets", []):
            FAIL.append(f"--show C-102 did not return coverage_gap: {out}")

        # 4. FS-1: explicit failed sheet in NL query → coverage_gap, exit 4
        r = run("query_drawing.py", "--set-dir", set_dir, "what notes are on C-102", "--json")
        if r.returncode != 4:
            FAIL.append(f"explicit failed-sheet query should exit 4, got {r.returncode}")
        if json.loads(r.stdout).get("result") != "coverage_gap":
            FAIL.append("explicit failed-sheet query did not return coverage_gap")

        # no silent reprocess: ledger unchanged by querying
        after = (machine / "manifest.json").read_text(encoding="utf-8")
        if before != after:
            FAIL.append("querying mutated the ledger (silent reprocess?)")

        # 5. drawings.md entry point exists with coverage banner + lists C-101
        dm = (set_dir / "views" / "drawings.md").read_text(encoding="utf-8")
        if "COVERAGE" not in dm or "PARTIAL" not in dm:
            FAIL.append("drawings.md missing partial coverage banner")
        if "C-101" not in dm:
            FAIL.append("drawings.md does not list C-101")

        # 6. cheap read of a COMPLETE sheet works
        r = run("query_drawing.py", "--set-dir", set_dir, "--show", "C-101", "--json")
        if r.returncode != 0 or json.loads(r.stdout).get("result") != "sheet_text":
            FAIL.append("--show on complete sheet C-101 failed")

    if FAIL:
        print("FAIL:")
        for f in FAIL:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — tag query resolves via precomputed index; NL finds the sheet; "
          "query against failed sheet returns coverage_gap (exit 4) with no "
          "reprocess; drawings.md carries the banner.")
    sys.exit(0)


if __name__ == "__main__":
    main()
