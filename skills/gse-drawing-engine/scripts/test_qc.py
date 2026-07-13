"""
test_qc.py — Phase 3 acceptance test (coverage, QC gate, verification).

Acceptance (PRD Phase 3):
  - QC flags an intentionally under-extracted sheet
  - coverage banner reflects true processed/total
  - verification catches a planted wrong value
Plus: a visual-fallback sheet cannot be GREEN; partial coverage is not "current";
the set becomes QUERY-able after QC; ledger promotes classified→complete/failed.

Uses the real pipeline on a synthetic 4-page PDF (so .txt exists for the
verification cross-check).

Run:  python test_qc.py    Exit: 0 pass / 1 fail.
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
    bodies = [
        "C-101 YARD PIPING PLAN\nP-101 PUMP\nINV 92.50 STA 12+50",
        "C-501 DETAILS\nTRENCH SECTION",
        "E-001 ONE-LINE\nMCC-1 FEEDER",
        None,  # page 4: intentionally blank (no text → likely_scanned)
    ]
    for b in bodies:
        page = doc.new_page(width=792, height=612)
        if b:
            page.insert_text((72, 72), b, fontsize=12)
    doc.save(str(path)); doc.close()


def rec(sn, disc, tags, callouts, stype, conf, ec, view):
    return {"sheet_number": sn, "title": sn, "discipline": disc,
            "document_type": "contract_drawing", "confidence": conf,
            "extraction_confidence": ec, "source_type": stype,
            "secondary_disciplines": [], "summary": f"{sn} test.",
            "key_elements": [], "systems": [], "equipment_tags": tags,
            "tag_details": [], "key_callouts": callouts, "details_defined": [],
            "scale": "", "view_type": view, "scope_relevant": True, "notes": ""}


def write_cls(sheets_dir, folder, r):
    (sheets_dir / folder / "classification.json").write_text(json.dumps(r, indent=2), encoding="utf-8")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    import fitz  # noqa
    with tempfile.TemporaryDirectory() as tmp:
        sub = Path(tmp) / "sub"
        (sub / "drawings").mkdir(parents=True)
        pdf = sub / "drawings" / "qc-set.pdf"
        make_pdf(pdf)
        set_dir = sub / "drawing-db" / "qc-set"
        sheets_dir = set_dir / "sheets"
        machine = set_dir / "machine"

        run("init_namespace.py", "--set-dir", set_dir, "--date", "2026-06-22")
        run("process_drawing.py", pdf, "--set-dir", set_dir, "--date", "2026-06-22")
        folders = [p["folder"] for p in load(sheets_dir / "manifest.json")["pages"]]

        # GREEN, YELLOW(visual), GREEN, RED(under-extracted: blank page claims clean high pdf_text)
        write_cls(sheets_dir, folders[0], rec("C-101", "Civil", ["P-101"], ["INV 92.50"], "pdf_text", "high", "high", "plan"))
        write_cls(sheets_dir, folders[1], rec("C-501", "Civil", [], [], "image_visual", "high", "high", "detail"))
        write_cls(sheets_dir, folders[2], rec("E-001", "Electrical", ["MCC-1"], [], "pdf_text", "high", "high", "diagram"))
        write_cls(sheets_dir, folders[3], rec("UNK-4", "Other", [], [], "pdf_text", "high", "high", "other"))

        run("build_sheet_index.py", "--set-dir", set_dir, "--date", "2026-06-22")

        # QC
        r = run("qc_pass.py", "--set-dir", set_dir, "--date", "2026-06-22")
        if r.returncode != 0:
            FAIL.append(f"qc_pass failed: {r.stderr}")
        qc = {s["sheet_number"]: s for s in load(machine / "qc_status.json")["sheets"]}

        if qc.get("C-101", {}).get("qc") != "green":
            FAIL.append(f"C-101 expected green, got {qc.get('C-101', {}).get('qc')}")
        if qc.get("C-501", {}).get("qc") != "yellow":
            FAIL.append(f"C-501 (visual fallback) expected yellow, got {qc.get('C-501', {}).get('qc')}")
        # under-extracted sheet flagged RED
        if qc.get("UNK-4", {}).get("qc") != "red":
            FAIL.append(f"under-extracted UNK-4 expected red, got {qc.get('UNK-4', {}).get('qc')}")
        elif not any("under-extracted" in why for why in qc["UNK-4"]["reasons"]):
            FAIL.append(f"UNK-4 red but not for under-extraction: {qc['UNK-4']['reasons']}")

        # ledger promotion
        ledger = {s["sheet_number"]: s["processing_state"] for s in load(machine / "manifest.json")["sheets"]}
        if ledger.get("C-101") != "complete" or ledger.get("C-501") != "complete":
            FAIL.append(f"green/yellow not promoted to complete: {ledger}")
        if ledger.get("UNK-4") != "failed":
            FAIL.append(f"red sheet not set to failed: {ledger.get('UNK-4')}")
        if load(machine / "manifest.json")["run_status"] != "partial":
            FAIL.append("run_status should be partial (one failed sheet)")

        # coverage reflects true processed/total
        cov = load(machine / "coverage_status.json")
        if cov["total_sheets"] != 4 or cov["processed"] != 3:
            FAIL.append(f"coverage processed/total wrong: {cov['processed']}/{cov['total_sheets']}")
        if cov["current"] is not False:
            FAIL.append("partial coverage wrongly marked current=True")
        if "C-501" not in cov["needs_verification"]:
            FAIL.append("yellow C-501 not listed in needs_verification")
        banner = (set_dir / "views" / "coverage.md").read_text(encoding="utf-8")
        if "3/4" not in banner or "PARTIAL" not in banner:
            FAIL.append(f"coverage banner wrong: {[l for l in banner.splitlines() if 'COVERAGE' in l]}")

        # set is now QUERY-able (router routes a QC'd set to QUERY)
        rr = run("router.py", "--set-dir", set_dir)
        if json.loads(rr.stdout)["mode"] != "QUERY":
            FAIL.append(f"router did not reach QUERY after QC: {json.loads(rr.stdout)['mode']}")

        # verification — clean sample: no failures
        r = run("verify_sample.py", "--set-dir", set_dir, "--sample", "100", "--date", "2026-06-22")
        if r.returncode != 0:
            FAIL.append(f"verification flagged a failure on clean data: {r.stdout}")
        v = load(machine / "verification.json")
        if v["auto_failed"] != 0:
            FAIL.append(f"clean verification has auto_failed={v['auto_failed']}")

        # verification catches a PLANTED wrong value (callout not in source .txt)
        bad = rec("C-101", "Civil", ["P-101"], ["INV 92.50", "INV 99.99"], "pdf_text", "high", "high", "plan")
        write_cls(sheets_dir, folders[0], bad)
        run("build_sheet_index.py", "--set-dir", set_dir, "--date", "2026-06-22")
        r = run("verify_sample.py", "--set-dir", set_dir, "--sample", "100", "--date", "2026-06-22")
        if r.returncode == 0:
            FAIL.append("verification did NOT catch the planted wrong value (INV 99.99)")
        else:
            v = load(machine / "verification.json")
            if not any(f["value"] == "INV 99.99" for f in v["failures"]):
                FAIL.append(f"planted value not in failures: {v['failures']}")

    if FAIL:
        print("FAIL:")
        for f in FAIL:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — under-extracted sheet flagged RED, visual sheet capped at YELLOW, "
          "coverage banner shows true 3/4 PARTIAL, set becomes QUERY-able, "
          "verification catches the planted wrong value.")
    sys.exit(0)


if __name__ == "__main__":
    main()
