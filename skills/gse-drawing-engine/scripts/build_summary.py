"""
build_summary.py — Phase 4, the query entry point drawings.md (no AI)

Renders <set>/views/drawings.md — the compact master summary ingested at the
start of every query session to route a question to the right sheets without
opening raw files. Pure projection of the machine JSON (D5) — introduces no new
facts. Carries the FS-4 coverage banner.

Reads (from <set>/machine/): sheet_index.json, sheet_classification.json,
coverage_status.json, rfi_candidates.json. Writes <set>/views/drawings.md.

Usage:
    python build_summary.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DISC_ORDER = ["General", "Civil", "Structural", "Architectural", "Mechanical",
              "Process", "Electrical", "Instrumentation", "Landscape", "Other"]


def load(machine, name, default):
    p = machine / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def banner(cov):
    if not cov:
        return "> COVERAGE: unknown."
    if not cov.get("total_sheets"):
        return ("> COVERAGE: unknown — coverage_status.json is still the init stub (0 sheets). "
                "Run scripts/build_coverage.py after QC, then re-render. Never publish a 0/0 banner.")
    if cov.get("current"):
        flagged = f" ({len(cov.get('needs_verification', []))} flagged)" if cov.get("needs_verification") else ""
        return f"> COVERAGE: complete — {cov.get('processed',0)}/{cov.get('total_sheets',0)} sheets processed{flagged}."
    pend, fail = cov.get("pending", []), cov.get("failed", [])
    extra = ""
    if pend:
        extra += f" pending: {', '.join(map(str, pend))}."
    if fail:
        extra += f" failed: {', '.join(map(str, fail))}."
    return (f"> COVERAGE: PARTIAL — {cov.get('processed',0)}/{cov.get('total_sheets',0)} sheets "
            f"processed. Answers about un-processed sheets are NOT supported.{extra}")


def main():
    p = argparse.ArgumentParser(description="Render drawings.md query entry point (Phase 4).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    idx = load(machine, "sheet_index.json", None)
    if idx is None:
        sys.exit(f"sheet_index.json not found in {machine}. Build the set first.")
    cls = load(machine, "sheet_classification.json", {"sheets": []})
    cov = load(machine, "coverage_status.json", {})
    rfi = load(machine, "rfi_candidates.json", {"candidates": []})

    class_by_sn = {s["sheet_number"]: s for s in cls.get("sheets", [])}
    by_disc = defaultdict(list)
    for s in idx["sheets"]:
        by_disc[s.get("discipline") or "Other"].append(s)

    systems = defaultdict(set)
    for s in cls.get("sheets", []):
        for sys_name in s.get("systems", []) or []:
            systems[sys_name].add(s.get("sheet_number"))

    src = ", ".join(idx.get("source_pdfs", [])) or "(unknown)"
    L = [f"# Drawings — {set_dir.name}", "", banner(cov), "",
         f"_Generated {args.date or '(no date)'} · {idx.get('sheet_count', 0)} sheets · source: {src}_", "",
         "## How to query this set",
         "Run `query_drawing.py --set-dir <set> \"question\"` (tag/equipment queries resolve "
         "through the precomputed `tag_index.json` in one lookup). It surfaces candidate sheets; "
         "then follow the source-of-truth ladder — `views/cards/[sheet].md` → raw "
         "`sheets/page_NNNN/*.txt` → `*.png` → `crop_region.py` — before stating any value. "
         "Machine source of truth lives in `machine/*.json`; these views are projections.", "",
         "## Set overview",
         f"{idx.get('sheet_count', 0)} sheets across "
         f"{len([d for d in by_disc if by_disc[d]])} disciplines. "
         f"{'Coverage is complete.' if cov.get('current') else 'Coverage is PARTIAL — see banner.'}", "",
         "## Sheets by discipline"]

    for disc in DISC_ORDER + sorted(set(by_disc) - set(DISC_ORDER)):
        sheets = by_disc.get(disc)
        if not sheets:
            continue
        L += [f"### {disc}", "| Sheet | Title | Summary |", "|---|---|---|"]
        for s in sorted(sheets, key=lambda x: x["sheet_number"]):
            sn = s["sheet_number"]
            summ = class_by_sn.get(sn, {}).get("summary", "").replace("\n", " ").replace("|", "/")
            title = (s.get("title", "") or "").replace("|", "/")
            L.append(f"| {sn} | {title} | {summ} |")
        L.append("")

    L.append("## Key systems")
    if systems:
        for sysn in sorted(systems):
            L.append(f"- **{sysn}** — {', '.join(sorted(x for x in systems[sysn] if x))}")
    else:
        L.append("_No named systems captured._")
    L.append("")

    cands = rfi.get("candidates", [])
    if cands:
        hi = sum(1 for c in cands if c.get("severity") == "high")
        md = sum(1 for c in cands if c.get("severity") == "medium")
        lo = sum(1 for c in cands if c.get("severity") == "low")
        L += ["## Coordination / RFI candidates",
              f"{len(cands)} RFI candidate(s): {hi} high, {md} medium, {lo} low — "
              "see `rfi_candidates.md` / `coordination_issues.md`.", ""]
    else:
        L += ["## Coordination / RFI candidates", "_None identified._", ""]

    views = set_dir / "views"
    views.mkdir(parents=True, exist_ok=True)
    (views / "drawings.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote drawings.md ({idx.get('sheet_count', 0)} sheets) -> {views}")


if __name__ == "__main__":
    main()
