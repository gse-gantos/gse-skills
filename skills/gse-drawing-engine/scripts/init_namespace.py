"""
init_namespace.py — drawing-engine canonical namespace writer (Phase 0)

Creates the isolated drawing-db/<set>/ namespace (PRD §4.4) and an initial
manifest + coverage stub, so the rest of the pipeline has a single, predictable
place to write. Writes ONLY under drawing-db/ — it never touches the originals'
folders (analyzed-drawings/, drawings-data/, drawings-md/), satisfying the D4 /
FS-6 coexistence isolation.

Layout created:

    drawing-db/<set>/
    ├── machine/        ← SOURCE OF TRUTH (schema-validated JSON)
    ├── views/          ← regenerable markdown projections
    │   └── cards/
    └── sheets/         ← per-sheet pdf/png/txt + split manifest

It is idempotent and SAFE: it never overwrites an existing manifest.json or
coverage_status.json (file-safety rule). Re-running only fills in missing
folders/stubs and reports what already existed.

Usage:
    python init_namespace.py --set-dir <drawing-db/<set>> --date YYYY-MM-DD
                             [--set-name NAME] [--source-pdf NAME ...]
    python init_namespace.py --db-root <drawing-db> --set-name <set> --date YYYY-MM-DD
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
SUBDIRS = ["machine", "views", "views/cards", "sheets"]


def sanitize(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip().rstrip(".")
    return s or "set"


def resolve_set_dir(args):
    if args.set_dir:
        sd = Path(args.set_dir).expanduser().resolve()
        return sd, args.set_name or sd.name
    if args.db_root and args.set_name:
        name = sanitize(args.set_name)
        return Path(args.db_root).expanduser().resolve() / name, name
    sys.exit("Specify --set-dir, or --db-root with --set-name.")


def main():
    p = argparse.ArgumentParser(description="Create the drawing-db/<set>/ namespace (Phase 0).")
    p.add_argument("--set-dir", help="Path to drawing-db/<set-name>/ to create.")
    p.add_argument("--db-root", help="Path to drawing-db/ root (used with --set-name).")
    p.add_argument("--set-name", help="Set name under drawing-db/.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    p.add_argument("--source-pdf", action="append", default=[],
                   help="Source PDF name(s) to record in the manifest (repeatable).")
    args = p.parse_args()

    set_dir, set_name = resolve_set_dir(args)
    if not args.date:
        print("NOTE: no --date supplied; 'generated' fields will be empty.", file=sys.stderr)

    created, existed = [], []
    for sub in SUBDIRS:
        d = set_dir / sub
        if d.exists():
            existed.append(sub)
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(sub)

    machine = set_dir / "machine"
    manifest_path = machine / "manifest.json"
    coverage_path = machine / "coverage_status.json"

    # SAFE: never clobber an existing manifest/coverage.
    if not manifest_path.exists():
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated": args.date,
            "set_name": set_name,
            "run_status": "building",      # router reads this → BUILD until a run completes
            "source_pdfs": list(args.source_pdf),
            "sheets": [],                  # bootstrapped to all-pending by Phase 1 after split
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        created.append("machine/manifest.json")
    else:
        existed.append("machine/manifest.json")

    if not coverage_path.exists():
        coverage = {
            "schema_version": SCHEMA_VERSION,
            "generated": args.date,
            "set_name": set_name,
            "current": False,
            "total_sheets": 0,
            "processed": 0,
            "pending": [],
            "failed": [],
            "needs_verification": [],
            "unanswerable_domains": [],
        }
        coverage_path.write_text(json.dumps(coverage, indent=2), encoding="utf-8")
        created.append("machine/coverage_status.json")
    else:
        existed.append("machine/coverage_status.json")

    print(f"Namespace: {set_dir}")
    if created:
        print("  created: " + ", ".join(created))
    if existed:
        print("  existed (left untouched): " + ", ".join(existed))


if __name__ == "__main__":
    main()
