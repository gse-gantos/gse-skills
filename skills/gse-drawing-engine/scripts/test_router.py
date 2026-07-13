"""
test_router.py — Phase 0 acceptance test for the drawing-engine router.

Acceptance (PRD Phase 0): "router correctly classifies all three states on stub
data without loading write protocols during a query."

Builds stub drawing-db/<set>/ fixtures in a temp dir for each state, runs
router.decide(), and asserts:
  1. BUILD  — no manifest.
  2. BUILD  — manifest present but run unfinished (pending sheets).
  3. UPDATE — manifest present, a sheet marked stale.
  4. QUERY  — manifest complete, no stale sheets.
  5. FS-2   — the QUERY decision loads ONLY query_protocol.md (no write protocol).

Run:  python test_router.py
Exit: 0 if all pass, 1 otherwise.
"""

import json
import sys
import tempfile
from pathlib import Path

import router  # same scripts/ dir


def write_manifest(set_dir: Path, run_status, sheets):
    machine = set_dir / "machine"
    machine.mkdir(parents=True, exist_ok=True)
    (machine / "manifest.json").write_text(json.dumps({
        "schema_version": "1.0",
        "generated": "2026-06-22",
        "set_name": set_dir.name,
        "run_status": run_status,
        "source_pdfs": ["stub.pdf"],
        "sheets": sheets,
    }, indent=2), encoding="utf-8")


def main():
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "drawing-db"

        # 1. BUILD — no manifest at all
        sd = root / "no-catalogue"
        sd.mkdir(parents=True)
        d = router.decide(sd)
        if d["mode"] != "BUILD":
            failures.append(f"no-manifest expected BUILD, got {d['mode']}")

        # 2. BUILD (resume) — unfinished run
        sd = root / "unfinished"
        write_manifest(sd, "building", [
            {"sheet_number": "C-101", "processing_state": "complete"},
            {"sheet_number": "C-102", "processing_state": "pending"},
        ])
        d = router.decide(sd)
        if d["mode"] != "BUILD":
            failures.append(f"unfinished expected BUILD, got {d['mode']}")

        # 3. UPDATE — a stale sheet
        sd = root / "revised"
        write_manifest(sd, "complete", [
            {"sheet_number": "C-101", "processing_state": "complete"},
            {"sheet_number": "C-102", "processing_state": "stale"},
        ])
        d = router.decide(sd)
        if d["mode"] != "UPDATE":
            failures.append(f"revised expected UPDATE, got {d['mode']}")
        if d.get("stale_sheets") != ["C-102"]:
            failures.append(f"revised expected stale_sheets=['C-102'], got {d.get('stale_sheets')}")

        # 4. QUERY — complete, current
        sd = root / "current"
        write_manifest(sd, "complete", [
            {"sheet_number": "C-101", "processing_state": "complete"},
            {"sheet_number": "C-102", "processing_state": "complete"},
        ])
        d = router.decide(sd)
        if d["mode"] != "QUERY":
            failures.append(f"current expected QUERY, got {d['mode']}")

        # 5. FS-2 — QUERY loads only query_protocol.md, no write protocol
        if d["load_references"] != ["references/query_protocol.md"]:
            failures.append(f"QUERY load_references should be only query_protocol.md, "
                            f"got {d['load_references']}")
        if not d["fs2_ok"]:
            failures.append(f"QUERY tripped FS-2 guard: {d.get('fs2_violation')}")

        # bonus: a complete run with a failed sheet still queries (partial coverage)
        sd = root / "partial-coverage"
        write_manifest(sd, "partial", [
            {"sheet_number": "C-101", "processing_state": "complete"},
            {"sheet_number": "C-102", "processing_state": "failed"},
        ])
        d = router.decide(sd)
        if d["mode"] != "QUERY":
            failures.append(f"partial-coverage expected QUERY, got {d['mode']}")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — all three states classified correctly; FS-2 guard holds on QUERY.")
    sys.exit(0)


if __name__ == "__main__":
    main()
