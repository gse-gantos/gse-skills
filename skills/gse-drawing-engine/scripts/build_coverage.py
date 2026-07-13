"""
build_coverage.py — Phase 3, the machine-readable coverage gate (FS-4)

Coverage honesty is the difference between "the drawings don't say" and a silent
wrong answer. This writes <set>/machine/coverage_status.json from the post-QC
processing ledger + classification, so every consumer can check, before
generating output, whether the sheets it needs are actually processed. Partial
coverage is never presented as complete.

`current` is True only when the run is complete (every sheet processed, none
pending/classified, none failed). A YELLOW (flagged) sheet still counts as
processed/answerable-with-caveat; a FAILED sheet is an explicit gap.

Reads (from <set>/machine/): manifest.json (ledger), sheet_classification.json,
and qc_status.json (if QC has run — supplies needs_verification / qc levels).
Writes: coverage_status.json + a readable views/coverage.md banner page.

Usage:
    python build_coverage.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA_VERSION = "1.0"
# states that mean "not yet answerable"
UNFINISHED = {"pending", "partial", "classified"}


def load(machine, name, default):
    p = machine / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def compute(set_dir: Path, date: str) -> dict:
    machine = set_dir / "machine"
    ledger = load(machine, "manifest.json", None)
    if not ledger:
        sys.exit(f"machine/manifest.json not found in {set_dir} (run process_drawing.py first).")
    cls = load(machine, "sheet_classification.json", {"sheets": []})
    qc = load(machine, "qc_status.json", {"sheets": []})

    disc_by_sn = {s.get("sheet_number"): s.get("discipline") for s in cls.get("sheets", [])}
    qc_by_sn = {s.get("sheet_number"): s for s in qc.get("sheets", [])}

    total = len(ledger.get("sheets", []))
    processed, pending, failed, needs_verification = [], [], [], []
    by_disc = defaultdict(lambda: {"total": 0, "processed": 0, "pending": 0, "failed": 0})
    unanswerable = set()

    for s in ledger.get("sheets", []):
        sn = s.get("sheet_number") or f"page-{s.get('page')}"
        state = s.get("processing_state", "pending")
        disc = s.get("discipline") or disc_by_sn.get(s.get("sheet_number")) or "Unknown"
        by_disc[disc]["total"] += 1

        if state == "complete":
            processed.append(sn)
            by_disc[disc]["processed"] += 1
            if qc_by_sn.get(s.get("sheet_number"), {}).get("qc") == "yellow":
                needs_verification.append(sn)
        elif state == "failed":
            failed.append(sn)
            by_disc[disc]["failed"] += 1
            unanswerable.add(disc)
        elif state in UNFINISHED:
            pending.append(sn)
            by_disc[disc]["pending"] += 1
            unanswerable.add(disc)

    run_status = ledger.get("run_status", "building")
    current = (run_status == "complete" and not pending and not failed)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated": date,
        "set_name": set_dir.name,
        "current": current,
        "run_status": run_status,
        "total_sheets": total,
        "processed": len(processed),
        "pending": pending,
        "failed": failed,
        "needs_verification": needs_verification,
        "by_discipline": {k: v for k, v in sorted(by_disc.items())},
        "unanswerable_domains": sorted(unanswerable),
    }


def banner_line(cov: dict) -> str:
    if cov["current"]:
        flagged = f" ({len(cov['needs_verification'])} flagged for verification)" if cov["needs_verification"] else ""
        return f"> COVERAGE: complete — {cov['processed']}/{cov['total_sheets']} sheets processed{flagged}."
    parts = []
    if cov["pending"]:
        parts.append(f"pending: {', '.join(map(str, cov['pending']))}")
    if cov["failed"]:
        parts.append(f"failed: {', '.join(map(str, cov['failed']))}")
    detail = ("  " + "; ".join(parts)) if parts else ""
    return (f"> COVERAGE: PARTIAL — {cov['processed']}/{cov['total_sheets']} sheets processed. "
            f"Answers about un-processed sheets are NOT supported.{detail}")


def write_coverage_md(set_dir: Path, cov: dict):
    views = set_dir / "views"
    views.mkdir(parents=True, exist_ok=True)
    L = [f"# Coverage — {cov['set_name']}", "",
         banner_line(cov), "",
         f"_Generated {cov['generated'] or '(no date)'} · run_status: {cov['run_status']}_", "",
         "| Discipline | Total | Processed | Pending | Failed |",
         "|---|---|---|---|---|"]
    for d, v in cov["by_discipline"].items():
        L.append(f"| {d} | {v['total']} | {v['processed']} | {v['pending']} | {v['failed']} |")
    if cov["needs_verification"]:
        L += ["", f"**Flagged for verification (YELLOW):** {', '.join(map(str, cov['needs_verification']))}"]
    if cov["unanswerable_domains"]:
        L += ["", f"**Domains not fully answerable:** {', '.join(cov['unanswerable_domains'])}"]
    (views / "coverage.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Write coverage_status.json (Phase 3, FS-4).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    cov = compute(set_dir, args.date)
    (set_dir / "machine").mkdir(parents=True, exist_ok=True)
    (set_dir / "machine" / "coverage_status.json").write_text(json.dumps(cov, indent=2), encoding="utf-8")
    write_coverage_md(set_dir, cov)
    print(f"Wrote coverage_status.json — {'COMPLETE' if cov['current'] else 'PARTIAL'}: "
          f"{cov['processed']}/{cov['total_sheets']} processed, "
          f"{len(cov['pending'])} pending, {len(cov['failed'])} failed, "
          f"{len(cov['needs_verification'])} flagged -> {set_dir / 'machine'}")


if __name__ == "__main__":
    main()
