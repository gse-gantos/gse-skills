# QC & Verification Protocol (Phase 3)

The gate that makes a set trustworthy enough to query. Run after the write engine
(Phases 1–2) has built the index, tag index, cross-references, details, and RFI
candidates. A set is not QUERY-able until QC runs: the router only reaches QUERY
once `run_status` is `complete`/`partial` with no sheet still `pending`/
`classified`, which only QC sets.

## 1. Run the QC gate

```
python scripts/qc_pass.py --set-dir "<set>" --date YYYY-MM-DD
```

It performs, deterministically:

1. **Schema validation** — classification enums + the FS-3 confidence ceiling;
   cross-reference enums.
2. **Coverage reconciliation** — split pages == ledger sheets == classified
   sheets in the index. A mismatch (a lost or double-counted sheet) blocks GREEN.
3. **Broken-reference report** — unresolved structural callouts (`to_sheet: null`,
   no `external_ref`) listed in `qc_status.json.broken_references`.
4. **Confidence-ceiling enforcement** — re-checks every record against its sheet
   ceiling.
5. **Per-sheet QC level**, then promotes the ledger and sets `run_status`, and
   refreshes `coverage_status.json`.

### QC level rules

| Level | When |
|---|---|
| **RED** (→ `failed`) | schema error on the sheet · `extraction_confidence: low` · classification `confidence: low` · "under-extracted": ≈no text on the page yet it claims clean high-confidence `pdf_text` |
| **YELLOW** (→ `complete`, flagged) | visual fallback (`source_type` image_visual/crop/ocr) · `extraction_confidence: medium` · schedule sheet not read at high confidence |
| **GREEN** (→ `complete`) | clean vector-text sheet, high confidence, no flags |

A sheet that required a **visual fallback** or **failed validation cannot be
GREEN** — this is the drawing-library discipline carried forward. RED sheets
become `failed` (kept for coverage honesty, never dropped); GREEN/YELLOW become
`complete`. `run_status` = `complete` (all green/yellow, none pending), `partial`
(some failed), or `building` (some still unclassified).

Outputs: `machine/qc_status.json` (per-sheet levels + reasons, schema errors,
reconciliation, broken refs) and refreshed `machine/coverage_status.json` +
`views/coverage.md`. After QC, re-run `build_rfi_candidates.py` so its banners
reflect the final coverage.

## 2. Verification step (sample re-check; subagent for large sets)

```
python scripts/verify_sample.py --set-dir "<set>" [--sample N] --date YYYY-MM-DD
```

- **Auto cross-check (no AI):** samples records risk-first (low/medium confidence
  and visual sheets first) and confirms each text-sourced value literally appears
  in its sheet's `.txt`. A value that isn't there is a fabricated/misread value →
  recorded as a FAILURE and the script exits non-zero. This catches planted/wrong
  values cheaply.
- **Subagent worklist:** values on visual-source sheets have no reliable `.txt`,
  so they're written to `verification.json.subagent_worklist`. For a large set,
  spawn a verification **subagent** (Task tool) to confirm each worklisted value
  against the sheet's `.png`/crop, returning pass/fail per item. Feed any failure
  back as a RED demotion (re-run QC) — a sheet with a confirmed wrong value cannot
  stay green/complete.

Keep the subagent read-only and scoped to the worklist; it confirms values, it
does not re-classify. A failure here means the catalogue lied about a value —
fix the classification and re-run QC before the set is trusted.

## 3. Result

When QC is GREEN/partial and verification clean, the set is queryable: the router
will route questions to QUERY, and every view carries an honest coverage banner.
