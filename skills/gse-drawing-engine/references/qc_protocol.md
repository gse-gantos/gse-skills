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

---

## Post-QC accuracy gates (added 2026-07-02 — from an independent QA audit)

These four checks are MANDATORY before a set is declared query-ready. Each maps
to a real defect found by an independent QA audit.

### 1. Write-integrity scan
```
python scripts/integrity_check.py --set-dir "<set>"
```
Enforced by script (exit 2 blocks promotion); covers gate 2 as well. What it does: re-read every file the run wrote (`machine/*.json`, `views/*.md`). Every JSON
must parse; every markdown must end with a complete sentence/table row, not
mid-word. Scan JSON string values for truncation tells: values ending mid-word,
with an unclosed parenthesis/quote, or in a dangling article ("the", "a").
One audited set shipped `"...gallery basemen"` and `"...('FALL PROTECTION DETA"` inside
rfi_candidates.json, plus five project files cut off mid-word. A truncated file
is a RED condition: rewrite it before promoting the run.

### 2. Banner-vs-machine consistency
Enforced by `integrity_check.py` (gate 1's script). For every `views/*.md`, the coverage banner numbers must equal
`machine/coverage_status.json` (`processed`/`total_sheets`/`current`). If any
view disagrees, re-run `build_rfi_candidates.py` / `build_summary.py` /
`build_coverage.py`. Views rendered before the QC gate are stale by
construction (see processing_protocol step 5).

### 3. Tag-family sweep
```
python scripts/tag_sweep.py --set-dir "<set>" [--extra-prefix W1 ...]
```
Enforced by script: sweeps every `sheets/page_NNNN/page_NNNN.txt` for tag-shaped
strings (longest-match, overlap-deduped) and diffs against `tag_index.json`.
Exit 2 lists the missing families — add the tags (re-classify those sheets) or
log an open question for each. The sweep only sees text-layer sheets; raster
sheets remain covered by the classification pass. On re-validation against an
audited set the script found the known missed `W1-CLF-*` family AND five more
unindexed `W1-*` families the manual audit had not enumerated. On that set
the whole `W1-CLF-*` family on I-4 was missed, including two probable source
typos (`W1-CLF-0307D`, `W1-CPL-0301B`) that should have been RFI candidates.

### 4. Schedule/matrix blind second read
Any schedule sheet whose cells will feed a takeoff, procurement quantity, or
register (demolition/repair matrices, pump schedules, conduit schedules) must be
extracted TWICE before its values are treated as `high` confidence:
- First read: normal classification pass.
- Second read: an independent pass (fresh subagent or fresh session) that does
  NOT see the first read's output, using identical-x-range header/data cropping
  (crop the rotated header band and the data band over the same left/right
  fractions of page width so columns map 1:1; verify against detected gridlines).
- Reconcile cell-by-cell. Any mismatch demotes that cell to
  `UNCERTAIN — PE REVIEW REQUIRED`; it must not enter a takeoff as confirmed.
On one audited set, a single-read pass missed one X-cell in a 34x16 matrix (fall protection,
effluent channel row) and a non-blind self-audit re-confirmed the wrong value.
The blind second read caught it. X-mark applicability cells count: an X missed
or invented changes a procurement quantity exactly like a wrong number.

### 5. Field-validated constraint check
Before declaring the set query-ready, reconcile it against
`references/validated_constraints.md` — these are behaviors confirmed on a full
prior set and are the likeliest silent errors:
- Any vector-CAD sheet classified `high` off `bluebeam_text`/`pdf_text` with only
  a title block in its `.txt` is suspect — it was probably read from the title
  block alone (L-001). Re-check it was read visually.
- P&ID loop tags sourced only from a balloon read must be `low` and carry an open
  question (L-002).
- Where a schedule sheet and a plan view disagree, confirm the schedule value
  won and the conflict is logged (L-003).
- Any count off an "illustration only" / "by manufacturer" / "typical" sheet must
  be flagged as an open question, not a confirmed quantity (L-004).
- Instrumented set (PLC/VFD/actuated valve/SCADA) → confirm a
  `control_system_relationships.md` view exists or a coverage gap is logged (L-005).
- Cross-discipline alias pairs (VAL/EMV, PMP/MTR) are deduped for any count (L-008).

### Token note for visual sweeps
When a gate or verification step needs the SAME small region checked on many
sheets (title blocks, stamps, north arrows), do not view full pages one by one.
Use:
```
python scripts/contact_sheet.py --pdf "<set.pdf>" --out-dir "<tmp>" [--region x0,y0,x1,y1] [--pages 1-54]
```
It renders the region of every page into labeled grid images (default region =
bottom-right title block; ~12 tiles per image). Accuracy-neutral — same pixels
at equal or better zoom, every tile labeled with its page number. Validated on
a 54-sheet set: all 54 title blocks legible across 5 images, immediately
re-confirming two known title findings.
