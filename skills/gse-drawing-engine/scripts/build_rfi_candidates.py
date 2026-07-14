"""
build_rfi_candidates.py — Phase 2, the D3 first-output contract (no AI)

The RFI candidate list is the first downstream output the retrieval contract is
designed against (PRD D3). Per D5, JSON is the source of truth and markdown is a
regenerable projection — so Claude writes the *judgment* as structured JSON
(coordination_issues.json + open_questions.json) and THIS script assembles the
RFI candidates deterministically and renders every markdown view. Nothing here
manufactures an issue; it only reshapes what Claude already cited.

Reads (from <set>/machine/):
  - coordination_issues.json   (Claude-authored; schema in rfi_candidate_protocol.md)
  - open_questions.json        (Claude-authored)
  - cross_references.json      (unresolved structural callouts → missing-reference RFIs)
  - coverage_status.json       (for the mandatory FS-4 banner)

Writes:
  - <set>/machine/rfi_candidates.json     (SOURCE OF TRUTH, §5.4 schema)
  - <set>/views/rfi_candidates.md         (projection, D3)
  - <set>/views/coordination_issues.md    (projection)
  - <set>/views/open_questions.md         (projection)

Usage:
    python build_rfi_candidates.py --set-dir <…/drawing-db/<set>> [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
RFI_TYPES = {"drawing-spec-conflict", "cross-discipline-conflict",
             "missing-reference", "ambiguity", "gap", "field-verification"}
SEV_ORDER = {"high": 0, "medium": 1, "low": 2}

# Default coordination-issue.type → RFI type when Claude didn't set rfi_type.
COORD_TO_RFI = {"gap": "gap", "ambiguity": "ambiguity",
                "missing-reference": "missing-reference", "coordination": "gap"}
# Default open-question.category → RFI type.
Q_TO_RFI = {"rfi-candidate": "ambiguity", "spec-drawing-conflict": "drawing-spec-conflict",
            "cross-discipline-conflict": "cross-discipline-conflict",
            "field-verification": "field-verification"}
# Categories that are NOT auto-promoted to RFIs unless is_rfi is explicitly true.
Q_NON_RFI = {"engineering", "procurement-risk", "commissioning-risk"}
# Structural ref types whose unresolved target becomes a missing-reference RFI.
STRUCT_REF = {"detail", "section", "continuation", "match_line", "key_plan"}


def load(machine, name, default):
    p = machine / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"WARNING: {name} is not valid JSON; treating as empty.", file=sys.stderr)
    return default


def coord_rfi_type(issue):
    if issue.get("rfi_type") in RFI_TYPES:
        return issue["rfi_type"]
    t = issue.get("type")
    if t == "conflict":
        return "cross-discipline-conflict" if len(issue.get("disciplines", [])) > 1 else "gap"
    return COORD_TO_RFI.get(t, "gap")


def main():
    p = argparse.ArgumentParser(description="Assemble RFI candidates + render views (Phase 2).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    views = set_dir / "views"
    views.mkdir(parents=True, exist_ok=True)
    if not machine.exists():
        sys.exit(f"machine/ not found in {set_dir}.")

    coord = load(machine, "coordination_issues.json", {"issues": []})
    oq = load(machine, "open_questions.json", {"questions": []})
    xrefs = load(machine, "cross_references.json", {"references": []}).get("references", [])
    coverage = load(machine, "coverage_status.json", None)

    candidates = []

    # 1. From coordination issues
    for iss in coord.get("issues", []):
        promote = iss.get("is_rfi")
        if promote is None:
            promote = iss.get("type") in {"conflict", "gap", "ambiguity", "missing-reference"}
        if not promote:
            continue
        candidates.append({
            "title": iss.get("title", ""),
            "type": coord_rfi_type(iss),
            "severity": iss.get("severity", "medium"),
            "sheets": iss.get("sheets", []),
            "disciplines": iss.get("disciplines", []),
            "evidence": iss.get("evidence", ""),
            "suggested_action": iss.get("suggested_action", ""),
            "confidence": iss.get("confidence", "medium"),
            "flag": iss.get("flag"),
            "source": iss.get("id", "coordination_issue"),
        })

    # 2. From open questions
    for q in oq.get("questions", []):
        cat = q.get("category")
        promote = q.get("is_rfi")
        if promote is None:
            promote = cat not in Q_NON_RFI
        if not promote:
            continue
        rfi_type = q.get("rfi_type") if q.get("rfi_type") in RFI_TYPES else Q_TO_RFI.get(cat, "ambiguity")
        candidates.append({
            "title": q.get("question", "")[:80],
            "type": rfi_type,
            "severity": q.get("severity", "medium"),
            "sheets": q.get("sheets", []),
            "disciplines": q.get("disciplines", []),
            "evidence": q.get("evidence", ""),
            "suggested_action": q.get("suggested_action",
                                      "Issue RFI to the design engineer for clarification."),
            "confidence": q.get("confidence", "medium"),
            "flag": q.get("flag"),
            "source": q.get("id", "open_question"),
        })

    # 3. From unresolved structural cross-references (deterministic — a callout to a
    #    sheet not in this set). Dedup by (from_sheet, label).
    seen = set()
    for r in xrefs:
        if r.get("to_sheet") is not None or r.get("external_ref"):
            continue
        if r.get("ref_type") not in STRUCT_REF:
            continue
        key = (r.get("from_sheet"), r.get("label"))
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "title": f"Unresolved callout {r.get('label', '')} on {r.get('from_sheet', '?')}",
            "type": "missing-reference",
            "severity": "medium",
            "sheets": [r.get("from_sheet")] if r.get("from_sheet") else [],
            "disciplines": [],
            "evidence": f"{r.get('from_sheet', '?')}: callout '{r.get('label', '')}' "
                        f"({r.get('ref_type', '')}) — {r.get('context', '')}".strip(),
            "suggested_action": "Confirm the referenced sheet/detail; the callout targets a "
                                "sheet not in this set. Obtain the missing sheet or issue an RFI.",
            "confidence": r.get("confidence", "medium"),
            "flag": None,
            "source": "cross_reference",
        })

    # sort by severity then keep source order; assign IDs
    candidates.sort(key=lambda c: SEV_ORDER.get(c.get("severity"), 1))
    for i, c in enumerate(candidates, 1):
        c["id"] = f"RFI-{i:03d}"

    # validate types/flags
    for c in candidates:
        if c["type"] not in RFI_TYPES:
            c["type"] = "ambiguity"
        if c.get("flag") not in (None, "safety", "code", "contractual"):
            c["flag"] = None

    out = {
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "candidate_count": len(candidates),
        "candidates": [
            {"id": c["id"], "title": c["title"], "type": c["type"], "severity": c["severity"],
             "sheets": c["sheets"], "disciplines": c["disciplines"], "evidence": c["evidence"],
             "suggested_action": c["suggested_action"], "confidence": c["confidence"],
             "flag": c["flag"], "source": c["source"]}
            for c in candidates
        ],
    }
    (machine / "rfi_candidates.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    banner = coverage_banner(coverage)
    render_rfi(views, set_dir.name, args.date, candidates, banner)
    render_coord(views, set_dir.name, args.date, coord.get("issues", []), banner)
    render_oq(views, set_dir.name, args.date, oq.get("questions", []), banner)

    n_hi = sum(1 for c in candidates if c["severity"] == "high")
    n_md = sum(1 for c in candidates if c["severity"] == "medium")
    n_lo = sum(1 for c in candidates if c["severity"] == "low")
    print(f"Wrote rfi_candidates.json ({len(candidates)}: {n_hi} high, {n_md} medium, {n_lo} low) -> {machine}")
    print(f"Wrote rfi_candidates.md, coordination_issues.md, open_questions.md -> {views}")


def coverage_banner(coverage):
    if not coverage:
        return "> COVERAGE: unknown — coverage_status.json not yet written (Phase 3)."
    if not coverage.get("total_sheets"):
        return ("> COVERAGE: unknown — coverage_status.json is still the init stub (0 sheets). "
                "Run scripts/build_coverage.py after the QC gate, then re-run this script so "
                "the banner reflects the real ledger. Never publish a 0/0 banner.")
    if coverage.get("current"):
        return f"> COVERAGE: complete — {coverage.get('processed', 0)}/{coverage.get('total_sheets', 0)} sheets processed."
    total = coverage.get("total_sheets", 0)
    proc = coverage.get("processed", 0)
    pend = coverage.get("pending", [])
    extra = f" Pending: {', '.join(map(str, pend))}." if pend else ""
    return (f"> COVERAGE: PARTIAL — {proc}/{total} sheets processed. Answers may be "
            f"incomplete; verify against source before acting.{extra}")


def _fmt_list(xs):
    return ", ".join(str(x) for x in xs if x) or "—"


def render_rfi(views, name, date, candidates, banner):
    L = [f"# RFI Candidates — {name}", "", banner,
         "> AI-GENERATED DRAFT — PE review required. Verify every cited value against the source sheet before issuing.", "",
         f"_Generated {date or '(no date)'} · {len(candidates)} candidates_", "",
         "_Drawing-derived RFI candidates from the GC's perspective. Each cites "
         "evidence; confirm before issuing. Not a substitute for the Procore RFI log._", ""]
    if not candidates:
        L.append("_No RFI candidates identified in this set._")
    else:
        for c in candidates:
            flag = f" · ⚑ {c['flag']}" if c.get("flag") else ""
            L += [f"### {c['id']} — {c['title']}", "",
                  f"- **Type:** {c['type']}",
                  f"- **Severity:** {c['severity']}{flag}",
                  f"- **Sheets:** {_fmt_list(c['sheets'])}",
                  f"- **Discipline(s):** {_fmt_list(c['disciplines'])}",
                  f"- **Confidence:** {c['confidence']}",
                  f"- **Source:** {c['source']}", "",
                  f"**Evidence.** {c['evidence'] or '—'}", "",
                  f"**Suggested action.** {c['suggested_action'] or '—'}", ""]
    (views / "rfi_candidates.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def render_coord(views, name, date, issues, banner):
    L = [f"# Coordination Issues — {name}", "", banner,
         "> AI-GENERATED DRAFT — PE review required.", "",
         f"_Generated {date or '(no date)'} · {len(issues)} issues_", ""]
    if not issues:
        L.append("_No coordination issues identified in this set._")
    else:
        for iss in issues:
            flag = f" · ⚑ {iss['flag']}" if iss.get("flag") else ""
            L += [f"### {iss.get('id', 'CI-?')} {iss.get('title', '')}", "",
                  f"- **Severity:** {iss.get('severity', '?')}{flag}",
                  f"- **Type:** {iss.get('type', '?')}",
                  f"- **Sheets:** {_fmt_list(iss.get('sheets', []))}",
                  f"- **Discipline(s):** {_fmt_list(iss.get('disciplines', []))}",
                  f"- **Confidence:** {iss.get('confidence', '?')}", "",
                  f"**Issue.** {iss.get('issue', '')}", "",
                  f"**Evidence.** {iss.get('evidence', '')}", "",
                  f"**Suggested action.** {iss.get('suggested_action', '')}", ""]
    (views / "coordination_issues.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def render_oq(views, name, date, questions, banner):
    L = [f"# Open Questions — {name}", "", banner,
         "> AI-GENERATED DRAFT — PE review required.", "",
         f"_Generated {date or '(no date)'} · {len(questions)} questions_", ""]
    if not questions:
        L.append("_No open questions logged for this set._")
    else:
        L += ["| ID | Category | Question | Sheets | Confidence |", "|---|---|---|---|---|"]
        for q in questions:
            L.append(f"| {q.get('id', '?')} | {q.get('category', '?')} | "
                     f"{q.get('question', '')} | {_fmt_list(q.get('sheets', []))} | "
                     f"{q.get('confidence', '?')} |")
    (views / "open_questions.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
