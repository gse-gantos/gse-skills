"""
query_drawing.py — Phase 4, the retrieval interface (no AI)

The single entry point for QUERY mode, repointed at drawing-db/<set>/machine/.
This does NOT answer the question — Claude does, after reading the candidate
sheets this surfaces (following the source-of-truth ladder in
references/query_protocol.md). The script does the cheap deterministic work:

  - TAG / equipment queries resolve through the PRECOMPUTED tag_index.json in a
    single lookup (the low-token win over read-drawing-beta, which re-scanned
    every sheet's tag array at query time).
  - NL queries score sheets against classification fields (+ a tag-index boost).
  - FS-1 COVERAGE GAP: a query whose target sheet is pending/failed returns a
    structured coverage_gap signal naming the missing sheets and STOPS. It never
    silently triggers a (re)build. Cheap reads of already-complete sheets are
    fine; heavy processing is never inline.

Usage:
    python query_drawing.py --set-dir <…/drawing-db/<set>> "natural language query"
        [--discipline Civil] [--tag "RAS"] [--equipment P-101] [--limit 8] [--json]
    python query_drawing.py --set-dir <…> --show C-101     # dump one sheet's text
"""

import argparse
import json
import re
import sys
from pathlib import Path

STOP = {"the", "a", "an", "of", "for", "to", "in", "on", "and", "or", "is", "are",
        "what", "which", "where", "how", "show", "me", "find", "sheet", "sheets",
        "drawing", "drawings", "this", "that", "with", "at", "by"}
# rough sheet-number token, e.g. C-101, M-2.04, E001
SHEET_TOKEN = re.compile(r"\b[A-Z]{1,3}-?\d[\w.\-]*\b")


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9\-]+", (text or "").lower())
            if t not in STOP and len(t) > 1]


def load(machine, name, default):
    p = machine / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def sheet_states(ledger):
    """sheet_number -> processing_state (complete/failed/classified/pending)."""
    out = {}
    for s in ledger.get("sheets", []):
        sn = s.get("sheet_number")
        if sn:
            out[sn] = s.get("processing_state", "pending")
    return out


def coverage_gap(reason, sheets, coverage):
    return {
        "result": "coverage_gap",
        "reason": reason,
        "missing_sheets": sheets,
        "guidance": "These sheets are not processed/QC-passed. Do NOT answer from them. "
                    "Run BUILD/UPDATE to process them, or answer only from processed sheets "
                    "with an explicit caveat. (Query never reprocesses inline — FS-1.)",
        "coverage_current": bool(coverage.get("current")) if coverage else False,
    }


def main():
    p = argparse.ArgumentParser(description="Retrieval helper for QUERY mode (Phase 4).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("query", nargs="?", default="", help="Natural language query.")
    p.add_argument("--discipline", help="Restrict to a discipline.")
    p.add_argument("--tag", help="Require this keyword in the sheet's searchable text.")
    p.add_argument("--equipment", help="Resolve this exact tag via the tag index.")
    p.add_argument("--limit", type=int, default=8, help="Max candidates to print.")
    p.add_argument("--show", help="Dump the extracted text for one sheet and exit.")
    p.add_argument("--json", action="store_true", help="JSON output (for tools/tests).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    idx = load(machine, "sheet_index.json", None)
    cls = load(machine, "sheet_classification.json", {"sheets": []})
    tagidx = load(machine, "tag_index.json", {"tags": []})
    coverage = load(machine, "coverage_status.json", {})
    ledger = load(machine, "manifest.json", {"sheets": []})
    if idx is None:
        sys.exit(f"sheet_index.json not found in {machine}. Build the set first.")

    index_by_sn = {s["sheet_number"]: s for s in idx["sheets"]}
    class_by_sn = {s["sheet_number"]: s for s in cls.get("sheets", [])}
    tag_by_name = {t["tag"]: t for t in tagidx.get("tags", [])}
    states = sheet_states(ledger)

    def answerable(sn):
        return states.get(sn) == "complete"

    def emit(obj, human):
        if args.json:
            print(json.dumps(obj, indent=2))
        else:
            print(human)

    # --- --show: cheap single-sheet read, gated on coverage (FS-1) ---
    if args.show:
        sn = args.show
        st = states.get(sn)
        if sn not in index_by_sn or st != "complete":
            gap = coverage_gap(
                f"Sheet {sn!r} is {st or 'not in this set'} — not answerable.",
                [sn], coverage)
            emit(gap, f"COVERAGE GAP: sheet {sn} is {st or 'not in this set'}. "
                      f"Not processed/QC-passed — query does not reprocess (FS-1).")
            sys.exit(4)
        rec = index_by_sn[sn]
        txt = set_dir / rec["paths"].get("txt", "")
        content = txt.read_text(encoding="utf-8", errors="ignore") if txt.exists() else "(text missing)"
        emit({"result": "sheet_text", "sheet_number": sn, "txt": rec["paths"].get("txt"),
              "content": content},
             f"=== {sn} :: {txt} ===\n{content}")
        return

    # --- explicit sheet referenced in the query but not answerable → FS-1 gap ---
    explicit = [t for t in SHEET_TOKEN.findall(args.query or "") if t in states]
    unanswerable_explicit = [t for t in explicit if states.get(t) != "complete"]
    if unanswerable_explicit:
        gap = coverage_gap(
            "Query references sheet(s) that are not processed/QC-passed.",
            unanswerable_explicit, coverage)
        emit(gap, "COVERAGE GAP: " + ", ".join(unanswerable_explicit) +
                  " not processed/QC-passed. Query does not reprocess inline (FS-1).")
        sys.exit(4)

    # --- exact tag / equipment via the precomputed index (one lookup) ---
    if args.equipment or (args.tag and args.tag in tag_by_name):
        key = args.equipment or args.tag
        t = tag_by_name.get(key)
        if not t:
            emit({"result": "no_match", "tag": key},
                 f"Tag {key!r} not found in the tag index.")
            return
        sheets = t["sheets"]
        gaps = [s for s in sheets if not answerable(s)]
        hits = [s for s in sheets if answerable(s)]
        obj = {"result": "tag_lookup", "tag": key, "via": "tag_index",
               "sheets": hits, "confidence": t.get("confidence"),
               "attributes": t.get("attributes", {}),
               "referenced_by": t.get("referenced_by", []),
               "unprocessed_sheets": gaps,
               "evidence": [{"sheet": e["sheet"], "txt": index_by_sn.get(e["sheet"], {}).get("paths", {}).get("txt"),
                             "png": index_by_sn.get(e["sheet"], {}).get("paths", {}).get("png")}
                            for e in t.get("evidence", []) if e.get("sheet") in index_by_sn]}
        human = [banner(coverage), f"Tag {key} (via precomputed tag_index, confidence "
                 f"{t.get('confidence')}): {', '.join(hits) or '—'}"]
        if t.get("attributes"):
            human.append(f"  attributes: {t['attributes']}")
        for e in obj["evidence"]:
            human.append(f"  {e['sheet']}: txt {e['txt']} · png {e['png']}")
        if gaps:
            human.append(f"  NOTE: also appears on un-processed sheet(s): {', '.join(gaps)} "
                         f"(not answerable — FS-1).")
        emit(obj, "\n".join(human))
        return

    if not args.query and not (args.discipline or args.tag):
        sys.exit("Provide a query and/or --discipline/--tag/--equipment, or --show SHEET.")

    # --- NL scoring over COMPLETE sheets, with a tag-index boost ---
    q_tokens = tokens(args.query)
    boosted = set()
    for tok in q_tokens:
        for name, t in tag_by_name.items():
            if tok == name.lower():
                boosted.update(s for s in t["sheets"] if answerable(s))

    scored = []
    for sn, c in class_by_sn.items():
        if not answerable(sn):
            continue
        irec = index_by_sn.get(sn, {})
        if args.discipline and c.get("discipline") != args.discipline:
            continue
        hay = " ".join([irec.get("title", ""), c.get("summary", ""),
                        " ".join(c.get("key_elements", [])), " ".join(c.get("systems", [])),
                        " ".join(c.get("equipment_tags", [])), " ".join(c.get("key_callouts", [])),
                        " ".join(d.get("title", "") for d in c.get("details_defined", []))])
        if args.tag and args.tag.lower() not in hay.lower():
            continue
        hay_tokens = set(tokens(hay))
        s = sum(1 for t in q_tokens if t in hay_tokens)
        if sn in boosted:
            s += 5
        if s > 0 or args.discipline or args.tag:
            scored.append((s, sn, c, irec))

    scored.sort(key=lambda x: (-x[0], x[1]))
    top = scored[: args.limit]

    obj = {"result": "candidates", "query": args.query,
           "coverage_current": bool(coverage.get("current")),
           "pending": coverage.get("pending", []), "failed": coverage.get("failed", []),
           "candidates": [{"sheet_number": sn, "score": sc, "discipline": c.get("discipline"),
                           "title": ir.get("title", ""), "summary": c.get("summary", ""),
                           "equipment_tags": c.get("equipment_tags", []),
                           "txt": ir.get("paths", {}).get("txt"),
                           "png": ir.get("paths", {}).get("png")}
                          for sc, sn, c, ir in top]}

    lines = [banner(coverage)]
    if not top:
        lines.append(f"No candidate sheets matched {args.query!r}. Broaden the query or filters.")
    else:
        lines.append(f"Top {len(top)} candidate(s) for {args.query!r} "
                     "(open the .txt/.png to read the actual sheet — see the ladder):")
        for sc, sn, c, ir in top:
            lines.append(f"[{sc}] {sn} ({c.get('discipline','?')}) {ir.get('title','')}")
            lines.append(f"     {c.get('summary','')}")
            if c.get("equipment_tags"):
                lines.append(f"     tags: {', '.join(c['equipment_tags'])}")
            lines.append(f"     txt: {ir.get('paths',{}).get('txt','-')}  png: {ir.get('paths',{}).get('png','-')}")
    emit(obj, "\n".join(lines))


def banner(coverage):
    if not coverage:
        return "(coverage unknown)"
    if coverage.get("current"):
        return f"COVERAGE: complete — {coverage.get('processed',0)}/{coverage.get('total_sheets',0)} sheets."
    pend = coverage.get("pending", [])
    fail = coverage.get("failed", [])
    extra = ""
    if pend:
        extra += f" pending: {', '.join(map(str, pend))}."
    if fail:
        extra += f" failed: {', '.join(map(str, fail))}."
    return (f"COVERAGE: PARTIAL — {coverage.get('processed',0)}/{coverage.get('total_sheets',0)} "
            f"sheets. Answers about un-processed sheets are not supported.{extra}")


if __name__ == "__main__":
    main()
