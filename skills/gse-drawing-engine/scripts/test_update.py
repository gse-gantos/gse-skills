"""
test_update.py — Phase 5 acceptance test (incremental update).

Acceptance (PRD Phase 5): re-running after one revised sheet touches only that
sheet and updates all dependent indexes/banners.

Builds a 2-sheet set, then feeds a revised PDF where only sheet 1 changed (sheet
2 byte-for-text identical). Asserts: only page 1 re-rendered + reclassified;
page 2 files + classification untouched; ledger states correct; and after
regenerating derived artifacts the tag index, coverage, and drawings.md reflect
the change; changelog records it.

Run:  python test_update.py    Exit: 0 pass / 1 fail.
"""

import hashlib
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


def make_pdf(path, pages):
    import fitz
    doc = fitz.open()
    for body in pages:
        pg = doc.new_page(width=792, height=612)
        pg.insert_text((72, 72), body, fontsize=12)
    doc.save(str(path)); doc.close()


def rec(sn, disc, tags, callouts):
    return {"sheet_number": sn, "title": sn, "discipline": disc,
            "document_type": "contract_drawing", "confidence": "high",
            "extraction_confidence": "high", "source_type": "pdf_text",
            "secondary_disciplines": [], "summary": f"{sn} summary.",
            "key_elements": [], "systems": [], "equipment_tags": tags,
            "tag_details": [], "key_callouts": callouts, "details_defined": [],
            "scale": "", "view_type": "plan", "scope_relevant": True, "notes": ""}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def digest(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


def regen(set_dir):
    for s in ("build_sheet_index.py", "build_tag_index.py", "build_cross_references.py",
              "build_detail_index.py", "build_rfi_candidates.py", "qc_pass.py", "build_summary.py"):
        run(s, "--set-dir", set_dir, "--date", "2026-06-22")


def main():
    import fitz  # noqa
    with tempfile.TemporaryDirectory() as tmp:
        sub = Path(tmp) / "sub"
        (sub / "drawings").mkdir(parents=True)
        v1 = sub / "drawings" / "set-v1.pdf"
        make_pdf(v1, ["C-101 YARD PIPING PLAN\nP-101 PUMP\nINV 92.50",
                      "C-201 PROCESS\nB-201 BLOWER"])
        set_dir = sub / "drawing-db" / "set"
        machine = set_dir / "machine"
        sheets_dir = set_dir / "sheets"

        # initial BUILD
        run("init_namespace.py", "--set-dir", set_dir, "--date", "2026-06-22")
        run("process_drawing.py", v1, "--set-dir", set_dir, "--date", "2026-06-22")
        folders = [p["folder"] for p in load(sheets_dir / "manifest.json")["pages"]]
        (sheets_dir / folders[0] / "classification.json").write_text(
            json.dumps(rec("C-101", "Civil", ["P-101"], ["INV 92.50"])), encoding="utf-8")
        (sheets_dir / folders[1] / "classification.json").write_text(
            json.dumps(rec("C-201", "Process", ["B-201"], [])), encoding="utf-8")
        regen(set_dir)

        # baseline checks
        tags0 = {t["tag"] for t in load(machine / "tag_index.json")["tags"]}
        if tags0 != {"P-101", "B-201"}:
            FAIL.append(f"baseline tag index wrong: {tags0}")

        # snapshot sheet 2 (must be untouched by the update)
        p2 = sheets_dir / folders[1]
        snap = {f: digest(p2 / f"{folders[1]}.{f}") for f in ("pdf", "png", "txt")}
        snap_cls = (p2 / "classification.json").read_text(encoding="utf-8")
        txt1_before = (sheets_dir / folders[0] / f"{folders[0]}.txt").read_text(encoding="utf-8")

        # revised PDF: sheet 1 changed (P-105 / INV 88.00), sheet 2 identical text
        v2 = sub / "drawings" / "set-v2.pdf"
        make_pdf(v2, ["C-101 YARD PIPING PLAN\nP-105 PUMP\nINV 88.00",
                      "C-201 PROCESS\nB-201 BLOWER"])

        r = run("update_drawing.py", v2, "--set-dir", set_dir, "--date", "2026-06-23")
        if r.returncode != 0:
            FAIL.append(f"update_drawing failed: {r.stderr}")

        # only sheet 1 touched
        if "1 revised" not in r.stdout or "1 unchanged" not in r.stdout:
            FAIL.append(f"update did not report 1 revised / 1 unchanged: {r.stdout.splitlines()[-2:]}")
        # sheet 2 files byte-identical
        for f in ("pdf", "png", "txt"):
            if digest(p2 / f"{folders[1]}.{f}") != snap[f]:
                FAIL.append(f"sheet 2 {f} was modified by the update (should be untouched)")
        if (p2 / "classification.json").read_text(encoding="utf-8") != snap_cls:
            FAIL.append("sheet 2 classification.json was modified by the update")
        # sheet 1 re-rendered + classification cleared
        if (sheets_dir / folders[0] / "classification.json").exists():
            FAIL.append("sheet 1 classification.json not cleared on revise")
        txt1_after = (sheets_dir / folders[0] / f"{folders[0]}.txt").read_text(encoding="utf-8")
        if "P-105" not in txt1_after or txt1_after == txt1_before:
            FAIL.append("sheet 1 text not re-extracted from the revised PDF")

        # ledger states + router → UPDATE
        led = {s["page"]: s["processing_state"] for s in load(machine / "manifest.json")["sheets"]}
        if led.get(1) != "stale" or led.get(2) != "complete":
            FAIL.append(f"ledger states after update wrong: {led}")
        rr = run("router.py", "--set-dir", set_dir)
        if json.loads(rr.stdout)["mode"] != "UPDATE":
            FAIL.append(f"router did not route UPDATE after revise: {json.loads(rr.stdout)['mode']}")

        # reclassify ONLY the revised sheet, then regenerate everything
        (sheets_dir / folders[0] / "classification.json").write_text(
            json.dumps(rec("C-101", "Civil", ["P-105"], ["INV 88.00"])), encoding="utf-8")
        regen(set_dir)

        # dependent artifacts updated
        tags1 = {t["tag"] for t in load(machine / "tag_index.json")["tags"]}
        if "P-105" not in tags1 or "P-101" in tags1 or "B-201" not in tags1:
            FAIL.append(f"tag index did not update on revise: {tags1}")
        cov = load(machine / "coverage_status.json")
        if not cov["current"] or cov["processed"] != 2:
            FAIL.append(f"coverage not current after update: {cov['processed']}/{cov['total_sheets']} current={cov['current']}")
        dm = (set_dir / "views" / "drawings.md").read_text(encoding="utf-8")
        if "C-101" not in dm or "C-201" not in dm or "complete" not in dm:
            FAIL.append("drawings.md not refreshed after update")
        rr = run("router.py", "--set-dir", set_dir)
        if json.loads(rr.stdout)["mode"] != "QUERY":
            FAIL.append("router not back to QUERY after finalized update")

        # changelog recorded the revision
        cl = (set_dir / "views" / "changelog.md").read_text(encoding="utf-8")
        if "Revised" not in cl:
            FAIL.append("changelog did not record the revision")

    if FAIL:
        print("FAIL:")
        for f in FAIL:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — revise touched only sheet 1 (sheet 2 byte-identical, classification kept); "
          "tag index dropped P-101/added P-105; coverage + drawings.md refreshed; "
          "router UPDATE→QUERY; changelog recorded it.")
    sys.exit(0)


if __name__ == "__main__":
    main()
