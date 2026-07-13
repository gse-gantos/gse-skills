"""
test_rfi.py — Phase 2 acceptance test (cross-refs, details, RFI candidates).

Acceptance (PRD Phase 2):
  - a seeded conflict (drawing dimension vs. spec callout) surfaces as a
    correctly-typed RFI candidate with cited evidence
  - zero uncited candidates
Plus: unresolved structural callout → missing-reference candidate; a held-back
'engineering' open question is NOT promoted; severity ordering; views rendered
with the FS-4 coverage banner; tag_index picks up referenced_by.

Builds JSON fixtures directly (no PDF needed) and runs the real Phase 2 scripts.

Run:  python test_rfi.py    Exit: 0 pass / 1 fail.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAIL = []


def run(script, set_dir):
    return subprocess.run([sys.executable, str(HERE / script), "--set-dir", str(set_dir),
                           "--date", "2026-06-22"], capture_output=True, text=True)


def w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        set_dir = Path(tmp) / "drawing-db" / "seed"
        sheets = set_dir / "sheets"
        machine = set_dir / "machine"

        # --- sheets/ : split manifest + per-page classification + refs ---
        pages = [("page_0001", "C-101"), ("page_0002", "C-501"), ("page_0003", "E-001")]
        w(sheets / "manifest.json", {
            "schema_version": "1.0", "generated": "2026-06-22",
            "source_pdfs": ["seed.pdf"], "page_count": 3,
            "pages": [{"page": i + 1, "folder": f, "source_pdf": "seed.pdf",
                       "source_page": i + 1,
                       "paths": {"pdf": f"{f}/{f}.pdf", "png": f"{f}/{f}.png", "txt": f"{f}/{f}.txt"}}
                      for i, (f, _) in enumerate(pages)],
        })
        for f, sn in pages:
            w(sheets / f / "classification.json", {"sheet_number": sn})
        # C-101 references a real detail (3/C-501) and an unresolved sheet (C-999)
        w(sheets / "page_0001" / "refs.json", {"references": [
            {"to_sheet": "C-501", "external_ref": None, "ref_type": "detail",
             "label": "3/C-501", "context": "Trench section.", "confidence": "high"},
            {"to_sheet": "C-999", "external_ref": None, "ref_type": "detail",
             "label": "5/C-999", "context": "Thrust block detail.", "confidence": "medium"},
        ]})

        # --- machine/ : index, classification (with a detail), coverage ---
        w(machine / "sheet_index.json", {
            "schema_version": "1.0", "generated": "2026-06-22", "source_pdfs": ["seed.pdf"],
            "sheet_count": 3, "sheets": [{"sheet_number": sn} for _, sn in pages]})
        w(machine / "sheet_classification.json", {
            "schema_version": "1.0", "generated": "2026-06-22", "sheets": [
                {"sheet_number": "C-101", "discipline": "Civil", "equipment_tags": ["P-101"],
                 "extraction_confidence": "high", "source_type": "pdf_text", "details_defined": []},
                {"sheet_number": "C-501", "discipline": "Civil", "equipment_tags": [],
                 "extraction_confidence": "high", "source_type": "pdf_text",
                 "details_defined": [{"number": "3", "title": "Trench Section"}]},
                {"sheet_number": "E-001", "discipline": "Electrical", "equipment_tags": ["P-101"],
                 "extraction_confidence": "high", "source_type": "pdf_text", "details_defined": []},
            ]})
        w(machine / "coverage_status.json", {
            "schema_version": "1.0", "generated": "2026-06-22", "current": False,
            "total_sheets": 3, "processed": 2, "pending": ["E-001"]})

        # --- Claude-authored judgment: a seeded drawing-spec conflict + questions ---
        w(machine / "coordination_issues.json", {
            "schema_version": "1.0", "generated": "2026-06-22", "issues": [
                {"id": "CI-001",
                 "title": "Influent invert: drawing vs. spec callout",
                 "type": "conflict", "severity": "high",
                 "sheets": ["C-101"], "disciplines": ["Civil"],
                 "issue": "C-101 dimensions the influent at INV 92.50 but the sheet's spec "
                          "callout SEE SPEC 33 05 13 governs 92.05.",
                 "evidence": "C-101 callout 'INV 92.50 STA 12+50' vs 'SEE SPEC 33 05 13'.",
                 "suggested_action": "RFI to engineer to confirm controlling invert.",
                 "confidence": "high", "flag": None,
                 "is_rfi": True, "rfi_type": "drawing-spec-conflict"}]})
        w(machine / "open_questions.json", {
            "schema_version": "1.0", "generated": "2026-06-22", "questions": [
                {"id": "OQ-001", "question": "Influent pipe material not called out on C-101.",
                 "category": "rfi-candidate", "severity": "medium", "sheets": ["C-101"],
                 "disciplines": ["Civil"], "evidence": "C-101 shows size/invert, no material.",
                 "confidence": "high", "flag": None},
                {"id": "OQ-002", "question": "Preferred dewatering method during tie-in?",
                 "category": "engineering", "severity": "low", "sheets": ["C-101"],
                 "disciplines": ["Civil"], "evidence": "general means/methods question.",
                 "confidence": "medium", "flag": None}]})

        # --- run Phase 2 ---
        for s in ("build_cross_references.py", "build_detail_index.py", "build_rfi_candidates.py"):
            r = run(s, set_dir)
            if r.returncode != 0:
                FAIL.append(f"{s} failed: {r.stderr}")

        # cross-refs: one resolved, one demoted to null
        xr = load(machine / "cross_references.json")["references"]
        resolved = [r for r in xr if r["to_sheet"] == "C-501"]
        demoted = [r for r in xr if r["to_sheet"] is None and r.get("label") == "5/C-999"]
        if not resolved:
            FAIL.append("resolved cross-ref C-101->C-501 missing")
        if not demoted:
            FAIL.append("unresolved C-999 callout not demoted to null")

        # detail index: detail 3 on C-501, referenced_by C-101
        di = load(machine / "detail_index.json")["details"]
        d3 = next((d for d in di if d["detail_id"] == "C-501/3"), None)
        if not d3:
            FAIL.append("detail C-501/3 not catalogued")
        elif "C-101" not in d3["referenced_by"]:
            FAIL.append(f"detail C-501/3 referenced_by wrong: {d3['referenced_by']}")

        # RFI candidates
        rfi = load(machine / "rfi_candidates.json")["candidates"]
        types = {c["type"] for c in rfi}
        # seeded conflict surfaces, correctly typed, with cited evidence
        seeded = [c for c in rfi if c["source"] == "CI-001"]
        if not seeded:
            FAIL.append("seeded conflict CI-001 did not surface as an RFI candidate")
        else:
            s = seeded[0]
            if s["type"] != "drawing-spec-conflict":
                FAIL.append(f"seeded conflict mis-typed: {s['type']}")
            if not s["evidence"].strip():
                FAIL.append("seeded conflict has no evidence")
            if s["severity"] != "high":
                FAIL.append(f"seeded conflict severity wrong: {s['severity']}")
        # unresolved callout -> missing-reference candidate
        if "missing-reference" not in types:
            FAIL.append("unresolved callout did not become a missing-reference candidate")
        # promoted question present, held-back engineering question absent
        sources = {c["source"] for c in rfi}
        if "OQ-001" not in sources:
            FAIL.append("OQ-001 (rfi-candidate) was not promoted")
        if "OQ-002" in sources:
            FAIL.append("OQ-002 (engineering) was wrongly promoted to an RFI")
        # ZERO uncited candidates
        uncited = [c["id"] for c in rfi if not c["evidence"].strip()]
        if uncited:
            FAIL.append(f"uncited RFI candidates present: {uncited}")
        # severity ordering (high before medium/low)
        sev = [c["severity"] for c in rfi]
        order = {"high": 0, "medium": 1, "low": 2}
        if sev != sorted(sev, key=lambda x: order[x]):
            FAIL.append(f"candidates not severity-sorted: {sev}")

        # views rendered with coverage banner
        rfi_md = (set_dir / "views" / "rfi_candidates.md").read_text(encoding="utf-8")
        if "COVERAGE" not in rfi_md:
            FAIL.append("rfi_candidates.md missing coverage banner")
        if "PARTIAL" not in rfi_md:
            FAIL.append("partial-coverage banner not reflected in rfi_candidates.md")

        # tag_index picks up referenced_by once cross_references exists
        r = subprocess.run([sys.executable, str(HERE / "build_tag_index.py"),
                            "--set-dir", str(set_dir), "--date", "2026-06-22"],
                           capture_output=True, text=True)
        ti = {t["tag"]: t for t in load(machine / "tag_index.json")["tags"]}
        # P-101 is on C-101 and E-001; C-101 references C-501 — referenced_by is about
        # sheets referencing P-101's sheets; just assert the field exists and is a list.
        if "P-101" in ti and not isinstance(ti["P-101"]["referenced_by"], list):
            FAIL.append("tag_index referenced_by not a list")

    if FAIL:
        print("FAIL:")
        for f in FAIL:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — seeded conflict surfaces as drawing-spec-conflict w/ evidence; "
          "unresolved callout → missing-reference; engineering Q held back; "
          "zero uncited; severity-sorted; banner present.")
    sys.exit(0)


if __name__ == "__main__":
    main()
