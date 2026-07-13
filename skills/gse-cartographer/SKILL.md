---
name: gse-cartographer
description: >
  Maintain the Project File Map (Claude/Map/) — the discovery backbone of the project's Claude OS.
  Use for: boot diff-scans ("what's new in the project folder?"), classifying newly found files,
  full remaps, regenerating map views, and answering "what exists that we haven't processed?".
  Built per the 2026-07-10 OS improvement ultraplan, Phase 2 (decisions D4, D5, D7, D8, D11).
---

# gse-cartographer

Maps the entire project folder — every file classified by content type, tracked for processed-status, with provenance. **Maps the mess; never cleans it.** Raw files are never moved, renamed, or "corrected"; folder-of-origin is a classification hint, not a gate.

## Files

- `Claude/Map/machine/manifest.json` — source of truth (one record per file/batch)
- `Claude/Map/machine/routing_schema.json` — content-type → home → processor + hints + batch rules
- `Claude/Map/machine/scan_state.json` — last sweep, counts
- `Claude/Map/machine/MAP_UPDATE_CONTRACT.md` — what every processing skill owes the map
- `Claude/Map/views/` — FILE_MAP.md, UNPROCESSED.md, SUPERSEDED.md (regenerable; never hand-edit)
- `references/classification-precedents.md` — accumulated human rulings; consult BEFORE asking again

## Operations

**Boot diff-scan (D11b — every session start):**
```bash
python3 scripts/scan.py --root <project_root> --diff
```
Report the output to the user. Detection is automatic; *classification* of new finds runs on approval — or automatically when the batch is small AND every item is high-confidence in a conventional location. Off-convention or low-confidence finds are always proposed first (D8).

**Classify:** for each new record, set `type`, `type_confidence`, `subproject`, `status: "classified"`, `classified_by`, and provenance in `manifest.json`. Check `references/classification-precedents.md` first — a matching precedent means auto-classify citing it. Record every new human ruling as a new precedent.

**Full remap (on command only, D11c):**
```bash
python3 scripts/scan.py --root <project_root> --full   # merge sweep into manifest (classifications preserved)
python3 scripts/render_views.py --root <project_root>  # then regenerate views
```

**View regen (after ANY manifest change):** `render_views.py` as above.

## Rules

1. Write boundary: this skill writes ONLY under `Claude/Map/` (and its own `references/`). It reads everywhere.
2. Batch granularity per `routing_schema.json` `batch_rules` — bulk homogeneous folders (photo albums, submittal packages, sheet exports) get ONE record. Splitting a batch into finer records is allowed when part of it gets processed.
3. A raw record's lifecycle: `unmapped → classified → processed → superseded`. Only processing skills (via the MAP_UPDATE_CONTRACT) or the human move records to `processed`.
4. Supersessions land in the manifest the moment they're known (drawing revs, resubmittals) — SUPERSEDED.md is a safety rail for the whole OS.
5. Log map-affecting sessions in `_Memory/log.md`. Anomalies found while mapping (duplicates, files in odd places, write-boundary violations by humans) go in record `notes` — flag, never fix.
6. Stale-mount caution (F9): before bulk manifest surgery via bash, confirm a couple of records against direct file reads.
