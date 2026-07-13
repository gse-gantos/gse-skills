"""
router.py — drawing-engine three-state router (Phase 0)

Decides the processing mode from DISK + COVERAGE STATE, never from user phrasing
(PRD §4.1). Emits one of:

    BUILD   — no catalogue yet, or an unfinished run to resume.
    UPDATE  — catalogue exists but one or more sheets are revised/new/stale
              (manifest marks them "stale"; the hash-diff that sets that flag
              lands in Phase 5).
    QUERY   — catalogue exists and is current; answer from it.

It ALSO emits, per FS-2 (lazy reference loading), the exact reference files the
chosen mode is allowed to load. A QUERY never lists a write protocol — that is
the machine-checkable form of "write protocols never load during a query".

This script does not process, classify, or answer. It only classifies state and
prints a JSON decision so the SKILL.md router step is deterministic and testable.

Usage:
    python router.py --set-dir <drawing-db/<set-name>>
    python router.py --db-root <drawing-db> --set-name <set>
    python router.py --drawings <path/to/pdf-or-folder> [--db-root <drawing-db>]
                     [--set-name <set>]          # resolves the set dir, then routes
    python router.py --set-dir <...> --explain    # human-readable, not JSON
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"

# FS-2 — the single source of truth for which references each mode may load.
# Files named here are created across Phases 1–5; the router names them whether
# or not they exist yet. A QUERY lists ONLY the query protocol: no write rigor
# (processing / classification / provenance / coverage-write) loads on a read.
MODE_REFERENCES = {
    "BUILD": [
        "references/processing_protocol.md",
        "references/classification_protocol.md",
        "references/provenance_contract.md",
        "references/coverage_contract.md",
        "references/drawing_types.md",
    ],
    "UPDATE": [
        "references/incremental_update_protocol.md",
        "references/processing_protocol.md",
        "references/classification_protocol.md",
        "references/provenance_contract.md",
        "references/coverage_contract.md",
    ],
    "QUERY": [
        "references/query_protocol.md",
    ],
}

# Write protocols that must NEVER appear in a QUERY's load list (FS-2 guard).
WRITE_PROTOCOLS = {
    "references/processing_protocol.md",
    "references/classification_protocol.md",
    "references/provenance_contract.md",
    "references/coverage_contract.md",
    "references/incremental_update_protocol.md",
    "references/drawing_types.md",
}

# An unfinished run → BUILD (resume). "classified" = per-page classification.json
# written but the set has not yet passed QC (Phase 3 promotes classified→complete).
ACTIVE_STATES = {"pending", "partial", "classified"}


def sanitize(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip().rstrip(".")
    return s or "set"


def resolve_set_dir(args) -> Path:
    """Resolve the canonical drawing-db/<set>/ folder from whatever was given."""
    if args.set_dir:
        return Path(args.set_dir).expanduser().resolve()

    if args.drawings:
        dpath = Path(args.drawings).expanduser().resolve()
        # default set name from the PDF/folder name unless overridden
        set_name = sanitize(args.set_name) if args.set_name else \
            sanitize(dpath.stem if dpath.is_file() else dpath.name)
        if args.db_root:
            db_root = Path(args.db_root).expanduser().resolve()
        else:
            # subproject = parent of drawings/ (or the input's own folder)
            anchor = dpath.parent if dpath.is_file() else dpath
            subproject = anchor.parent if anchor.name.lower() == "drawings" else anchor
            db_root = subproject / "drawing-db"
        return db_root / set_name

    if args.db_root and args.set_name:
        return Path(args.db_root).expanduser().resolve() / sanitize(args.set_name)

    sys.exit("Specify --set-dir, or --drawings [--set-name], or --db-root --set-name.")


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def summarize_sheets(manifest: dict) -> dict:
    counts = {"total": 0, "complete": 0, "pending": 0, "partial": 0,
              "classified": 0, "failed": 0, "stale": 0}
    stale, failed, pending = [], [], []
    for s in manifest.get("sheets", []) if manifest else []:
        counts["total"] += 1
        st = s.get("processing_state", "pending")
        if st in counts:
            counts[st] += 1
        else:
            counts["pending"] += 1
            st = "pending"
        sn = s.get("sheet_number") or f"page-{s.get('page', '?')}"
        if st == "stale":
            stale.append(sn)
        elif st == "failed":
            failed.append(sn)
        elif st in ACTIVE_STATES:
            pending.append(sn)
    return {"counts": counts, "stale": stale, "failed": failed, "pending": pending}


def decide(set_dir: Path) -> dict:
    machine = set_dir / "machine"
    manifest_path = machine / "manifest.json"

    decision = {
        "schema_version": SCHEMA_VERSION,
        "set_dir": str(set_dir),
        "manifest": str(manifest_path),
    }

    if not manifest_path.exists():
        decision.update({
            "mode": "BUILD",
            "reason": "No catalogue exists for this set (machine/manifest.json absent).",
            "run_status": None,
            "coverage": None,
        })
    else:
        manifest = load_json(manifest_path) or {}
        run_status = manifest.get("run_status", "building")
        summ = summarize_sheets(manifest)
        coverage = load_json(machine / "coverage_status.json")

        if summ["stale"]:
            mode = "UPDATE"
            reason = (f"Catalogue exists; {len(summ['stale'])} sheet(s) marked stale "
                      f"(revised/new): {', '.join(summ['stale'])}. Reprocess only those.")
        elif run_status == "building" or summ["pending"]:
            mode = "BUILD"
            reason = (f"Catalogue is unfinished (run_status={run_status!r}, "
                      f"{len(summ['pending'])} sheet(s) pending/partial). Resume build.")
        else:
            mode = "QUERY"
            reason = (f"Catalogue exists and is current (run_status={run_status!r}). "
                      f"Answer from it; do not reprocess.")

        decision.update({
            "mode": mode,
            "reason": reason,
            "run_status": run_status,
            "coverage": coverage,
            "sheet_summary": summ,
            "stale_sheets": summ["stale"],
        })

    mode = decision["mode"]
    refs = MODE_REFERENCES[mode]
    decision["load_references"] = refs

    # FS-2 hard guard: a QUERY must never carry a write protocol.
    if mode == "QUERY":
        leaked = sorted(set(refs) & WRITE_PROTOCOLS)
        decision["fs2_ok"] = not leaked
        if leaked:
            decision["fs2_violation"] = leaked
    else:
        decision["fs2_ok"] = True

    return decision


def main():
    p = argparse.ArgumentParser(description="drawing-engine three-state router (Phase 0).")
    p.add_argument("--set-dir", help="Path to drawing-db/<set-name>/.")
    p.add_argument("--db-root", help="Path to a drawing-db/ root (used with --set-name or --drawings).")
    p.add_argument("--set-name", help="Set name under drawing-db/.")
    p.add_argument("--drawings", help="Path to input PDF or drawings/ folder (resolves the set dir).")
    p.add_argument("--explain", action="store_true", help="Human-readable output instead of JSON.")
    args = p.parse_args()

    set_dir = resolve_set_dir(args)
    decision = decide(set_dir)

    if args.explain:
        print(f"MODE:   {decision['mode']}")
        print(f"SET:    {decision['set_dir']}")
        print(f"WHY:    {decision['reason']}")
        if decision.get("sheet_summary"):
            print(f"SHEETS: {decision['sheet_summary']['counts']}")
        print(f"LOAD:   {', '.join(decision['load_references'])}")
        print(f"FS-2:   {'ok' if decision['fs2_ok'] else 'VIOLATION ' + str(decision.get('fs2_violation'))}")
    else:
        print(json.dumps(decision, indent=2))

    # Non-zero exit on an FS-2 violation so a test harness catches it.
    sys.exit(0 if decision["fs2_ok"] else 3)




if __name__ == "__main__":
    main()
