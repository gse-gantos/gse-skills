"""
verify_sample.py — Phase 3, the verification step (sampler + auto cross-check)

For large sets, a subagent re-checks a sample of records against the source
sheets so QC-green doesn't mean "trust me." This script does the deterministic
half and teees up the rest for the subagent:

  1. SAMPLES records (equipment_tags + key_callouts), prioritizing the riskiest
     first: low/medium confidence, then visual-source sheets, then the rest.
  2. AUTO-CONFIRMS text-sourced values: a value claimed on a `pdf_text` sheet
     must literally appear in that sheet's extracted `.txt`. If it doesn't, that
     is a fabricated/misread value → recorded as a FAILURE (this is what catches
     a planted wrong value cheaply, no AI).
  3. Builds a WORKLIST for the subagent: values on visual-source sheets (which
     have no reliable `.txt`) can't be auto-confirmed and are handed off for
     visual confirmation per references/qc_protocol.md.

Writes <set>/machine/verification.json. Exits non-zero if any auto-check failed,
so a planted wrong value fails the gate.

Usage:
    python verify_sample.py --set-dir <…/drawing-db/<set>> [--sample N] [--date YYYY-MM-DD]
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
ORDER = {"low": 0, "medium": 1, "high": 2}
VISUAL = {"image_visual", "crop", "ocr"}


def load(machine, name, default):
    p = machine / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def main():
    p = argparse.ArgumentParser(description="Verification sampler + auto cross-check (Phase 3).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--sample", type=int, default=0,
                   help="Max records to sample (0 = auto: ~20%% of records, min 5, cap 40).")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    args = p.parse_args()

    set_dir = Path(args.set_dir).expanduser().resolve()
    machine = set_dir / "machine"
    cls = load(machine, "sheet_classification.json", {"sheets": []})
    idx = load(machine, "sheet_index.json", {"sheets": []})
    txt_by_sn = {s["sheet_number"]: s.get("paths", {}).get("txt") for s in idx.get("sheets", [])}

    # gather candidate records
    records = []
    for s in cls.get("sheets", []):
        sn = s.get("sheet_number")
        stype = s.get("source_type")
        ec = s.get("extraction_confidence", "medium")
        for tag in s.get("equipment_tags", []) or []:
            records.append({"sheet": sn, "kind": "tag", "value": str(tag),
                            "source_type": stype, "extraction_confidence": ec})
        for co in s.get("key_callouts", []) or []:
            records.append({"sheet": sn, "kind": "callout", "value": str(co),
                            "source_type": stype, "extraction_confidence": ec})

    # risk-first ordering: lower confidence first, visual before text, then stable
    records.sort(key=lambda r: (ORDER.get(r["extraction_confidence"], 1),
                                0 if r["source_type"] in VISUAL else 1,
                                r["sheet"] or "", r["value"]))

    n = args.sample or max(5, min(40, (len(records) + 4) // 5))
    sample = records[:n]

    # cache .txt content per sheet
    txt_cache = {}

    def sheet_text(sn):
        if sn not in txt_cache:
            rel = txt_by_sn.get(sn)
            t = ""
            if rel:
                fp = set_dir / rel
                if fp.exists():
                    t = fp.read_text(encoding="utf-8", errors="ignore")
            txt_cache[sn] = t
        return txt_cache[sn]

    checked, failures, worklist = [], [], []
    for r in sample:
        if r["source_type"] in VISUAL:
            worklist.append({**r, "result": "needs_visual",
                             "note": "visual-source sheet — confirm against .png/crop (subagent)"})
            continue
        txt = sheet_text(r["sheet"])
        if not txt:
            worklist.append({**r, "result": "no_text",
                             "note": "no .txt available — confirm visually (subagent)"})
            continue
        present = r["value"].lower() in txt.lower()
        rec = {**r, "result": "confirmed" if present else "FAILED",
               "note": "" if present else "value not found in source .txt — fabricated/misread?"}
        checked.append(rec)
        if not present:
            failures.append(rec)

    out = {
        "schema_version": SCHEMA_VERSION,
        "generated": args.date,
        "total_records": len(records),
        "sampled": len(sample),
        "auto_confirmed": sum(1 for c in checked if c["result"] == "confirmed"),
        "auto_failed": len(failures),
        "needs_subagent": len(worklist),
        "failures": failures,
        "subagent_worklist": worklist,
        "checked": checked,
    }
    (machine / "verification.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"Verification: sampled {len(sample)}/{len(records)} records — "
          f"{out['auto_confirmed']} confirmed, {out['auto_failed']} FAILED, "
          f"{out['needs_subagent']} for subagent.")
    for f in failures[:10]:
        print(f"  FAIL: {f['kind']} '{f['value']}' claimed on {f['sheet']} not in source text.")
    if worklist:
        print(f"  {len(worklist)} record(s) need subagent visual confirmation "
              f"(see machine/verification.json → subagent_worklist).")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
