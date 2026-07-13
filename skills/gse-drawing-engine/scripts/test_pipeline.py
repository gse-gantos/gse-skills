"""
test_pipeline.py — Phase 1 acceptance test for the drawing-engine write engine.

Acceptance (PRD Phase 1):
  - sheet count in PDF == sheet count in index
  - tag index resolves a known tag to all its sheets in one lookup
  - interrupt-and-resume processes only unfinished sheets
Plus: FS-3 confidence-ceiling rejection, and ledger state advances pending →
classified.

Self-contained: builds a synthetic 3-page PDF with PyMuPDF, runs the real
scripts as subprocesses, and asserts on the JSON they produce.

Run:  python test_pipeline.py
Exit: 0 if all pass, 1 otherwise.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAIL = []


def run(*args):
    r = subprocess.run([sys.executable, *map(str, args)],
                       capture_output=True, text=True)
    return r


def make_pdf(path: Path):
    import fitz
    doc = fitz.open()
    pages = [
        ("C-101", "YARD PIPING PLAN", "24\" INFLUENT INV 92.50  STA 12+50\nPUMP P-101 SUBMERSIBLE\nSEE 3/C-501"),
        ("C-501", "CIVIL DETAILS", "DETAIL 3 TRENCH SECTION\nPUMP P-101 BASE\n2'-0\" MIN COVER"),
        ("E-001", "ELECTRICAL ONE-LINE", "MCC-1 FEEDER\nP-101 MOTOR 5HP\nPANEL LP-1"),
    ]
    for _, title, body in pages:
        page = doc.new_page(width=792, height=612)  # 11x8.5 landscape
        page.insert_text((72, 72), title, fontsize=18)
        page.insert_text((72, 120), body, fontsize=11)
    doc.save(str(path))
    doc.close()
    return [p[0] for p in pages]


def write_classification(sheets_dir: Path, folder, rec):
    (sheets_dir / folder / "classification.json").write_text(
        json.dumps(rec, indent=2), encoding="utf-8")


def base_rec(sn, title, disc, tags, tag_details=None, conf="high", ec="high"):
    return {
        "sheet_number": sn, "title": title, "discipline": disc,
        "document_type": "contract_drawing", "confidence": conf,
        "extraction_confidence": ec, "source_type": "pdf_text",
        "secondary_disciplines": [], "summary": f"{title} test sheet.",
        "key_elements": [], "systems": [], "equipment_tags": tags,
        "tag_details": tag_details or [], "key_callouts": [], "details_defined": [],
        "scale": "", "view_type": "plan", "scope_relevant": True, "notes": "",
    }


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    import fitz  # ensure available; process_drawing installs it otherwise  # noqa
    with tempfile.TemporaryDirectory() as tmp:
        sub = Path(tmp) / "sub"
        (sub / "drawings").mkdir(parents=True)
        pdf = sub / "drawings" / "test-set.pdf"
        sheet_numbers = make_pdf(pdf)
        set_dir = sub / "drawing-db" / "test-set"

        # init + process
        run(HERE / "init_namespace.py", "--set-dir", set_dir, "--date", "2026-06-22")
        r = run(HERE / "process_drawing.py", pdf, "--set-dir", set_dir, "--date", "2026-06-22")
        if r.returncode != 0:
            FAIL.append(f"process_drawing failed: {r.stderr}")

        sheets_dir = set_dir / "sheets"
        machine = set_dir / "machine"

        # PDF page count == split manifest pages
        split = load(sheets_dir / "manifest.json")
        if split["page_count"] != 3:
            FAIL.append(f"expected 3 pages split, got {split['page_count']}")

        # ledger bootstrapped all-pending
        ledger = load(machine / "manifest.json")
        if [s["processing_state"] for s in ledger["sheets"]] != ["pending"] * 3:
            FAIL.append("ledger not bootstrapped to all-pending")

        # classify each page (P-101 appears on all three sheets)
        folders = [p["folder"] for p in split["pages"]]
        write_classification(sheets_dir, folders[0],
            base_rec("C-101", "YARD PIPING PLAN", "Civil", ["P-101"],
                     [{"tag": "P-101", "type": "submersible pump", "size": "", "service": "influent", "evidence": "this sheet"}]))
        write_classification(sheets_dir, folders[1],
            base_rec("C-501", "CIVIL DETAILS", "Civil", ["P-101"]))
        write_classification(sheets_dir, folders[2],
            base_rec("E-001", "ELECTRICAL ONE-LINE", "Electrical", ["P-101", "MCC-1"]))

        # build index
        r = run(HERE / "build_sheet_index.py", "--set-dir", set_dir, "--date", "2026-06-22")
        if r.returncode != 0:
            FAIL.append(f"build_sheet_index failed: {r.stderr}")

        idx = load(machine / "sheet_index.json")
        # ACCEPTANCE: PDF sheet count == index sheet count
        if idx["sheet_count"] != 3 or len(idx["sheets"]) != 3:
            FAIL.append(f"index sheet_count != 3 (got {idx['sheet_count']})")

        # ledger advanced pending -> classified
        ledger = load(machine / "manifest.json")
        if {s["processing_state"] for s in ledger["sheets"]} != {"classified"}:
            FAIL.append(f"ledger states after index: "
                        f"{[s['processing_state'] for s in ledger['sheets']]}")
        if {s["sheet_number"] for s in ledger["sheets"]} != set(sheet_numbers):
            FAIL.append("ledger sheet_numbers not stamped correctly")

        # build tag index
        r = run(HERE / "build_tag_index.py", "--set-dir", set_dir, "--date", "2026-06-22")
        if r.returncode != 0:
            FAIL.append(f"build_tag_index failed: {r.stderr}")
        tagidx = load(machine / "tag_index.json")
        tags = {t["tag"]: t for t in tagidx["tags"]}
        # ACCEPTANCE: one lookup resolves P-101 to all three sheets
        if "P-101" not in tags:
            FAIL.append("P-101 missing from tag index")
        elif sorted(tags["P-101"]["sheets"]) != ["C-101", "C-501", "E-001"]:
            FAIL.append(f"P-101 sheets wrong: {tags['P-101']['sheets']}")
        # cheap attribute carried through
        if tags.get("P-101", {}).get("attributes", {}).get("type") != "submersible pump":
            FAIL.append("P-101 cheap attribute (type) not carried into tag index")

        # ACCEPTANCE: resume processes only unfinished sheets.
        # Re-run process_drawing; all outputs exist -> all 3 should be skipped/resumed,
        # and classified states must be PRESERVED (not reset to pending).
        r = run(HERE / "process_drawing.py", pdf, "--set-dir", set_dir, "--date", "2026-06-22")
        if "3 resumed" not in r.stdout:
            FAIL.append(f"resume did not skip all 3 pages: {r.stdout.strip().splitlines()[-1:]}")
        ledger = load(machine / "manifest.json")
        if {s["processing_state"] for s in ledger["sheets"]} != {"classified"}:
            FAIL.append("resume reset classified sheets back to pending (should preserve)")

        # FS-3 ceiling: a record claiming confidence>extraction_confidence is rejected
        bad = base_rec("X-1", "BAD", "Civil", [], conf="high", ec="low")
        write_classification(sheets_dir, folders[0], bad)
        r = run(HERE / "build_sheet_index.py", "--set-dir", set_dir, "--date", "2026-06-22")
        if r.returncode == 0:
            FAIL.append("FS-3 ceiling violation was NOT rejected by build_sheet_index")
        elif "ceiling" not in (r.stderr + r.stdout).lower():
            FAIL.append("FS-3 rejection did not cite the ceiling")

    if FAIL:
        print("FAIL:")
        for f in FAIL:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — split==index, tag lookup resolves across sheets, resume skips "
          "done pages, ledger advances pending→classified, FS-3 ceiling enforced.")
    sys.exit(0)


if __name__ == "__main__":
    main()
