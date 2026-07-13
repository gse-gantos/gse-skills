# Processing Protocol — BUILD mode pipeline (Phase 1)

Run order for a BUILD (or BUILD-resume). Scripts do the deterministic work;
Claude does the classification. Everything writes under `drawing-db/<set>/`.
Persist per sheet so an interrupted run resumes cleanly (FS-7).

All script paths are relative to the skill's `scripts/` folder; `<set>` is the
canonical `…/drawing-db/<set-name>/` folder.

## 0. Namespace
```
python scripts/init_namespace.py --set-dir "<set>" --date YYYY-MM-DD
```
Idempotent; never clobbers an existing manifest/coverage. Skip if the router
already routed to an existing set.

## 1. Split, extract, render (deterministic)
```
python scripts/process_drawing.py "<PDF or drawings/ folder>" --set-dir "<set>" --date YYYY-MM-DD
```
Writes `<set>/sheets/page_NNNN/` (`.pdf`, `.png`, `.txt`), the split manifest
`<set>/sheets/manifest.json`, and **bootstraps the processing ledger**
`<set>/machine/manifest.json` with every page `processing_state: pending` — the
hard rule: the ledger exists all-pending before any index row is written. Each
page carries a `source_hash` (Phase-5 stale detection). Re-running skips pages
whose outputs already exist (resume); `--force` re-renders. Note any
`LIKELY SCANNED` pages — classify those from the image.

## 2. Classify each sheet (Claude — no script)
Follow `references/classification_protocol.md`: read each page's `.txt`, view its
`.png` (crop when needed), and write `<set>/sheets/page_NNNN/classification.json`
with the closed-enum fields, the FS-3 provenance fields (`source_type`,
`extraction_confidence`), and the cheap depth fields (`equipment_tags`,
`tag_details`, `key_callouts`, `details_defined`). Work in batches; each file
written makes the work resumable.

## 3. Assemble the index (deterministic)
```
python scripts/build_sheet_index.py --set-dir "<set>" --date YYYY-MM-DD
```
Validates every `classification.json` (enums + required fields + the FS-3
confidence ceiling) and writes `machine/sheet_index.json` +
`machine/sheet_classification.json`. It also stamps the ledger: fills
`sheet_number`/`discipline`/`extraction_confidence` and advances
`pending → classified`. Fix any reported errors and re-run; it writes nothing on
a validation failure. `--allow-missing` writes partial output if you intend to
skip pages.

## 4. Build the inverted tag index (deterministic)
```
python scripts/build_tag_index.py --set-dir "<set>" --date YYYY-MM-DD
```
Inverts `equipment_tags` → `machine/tag_index.json` (tag → sheets), carrying each
tag's confidence ceiling (min across its sheets), cheap attributes, and evidence.
Re-run after `cross_references.json` exists (Phase 2) to also stamp
`referenced_by`. Writes the `views/tag_index.md` projection.

## What's next
Cross-references, detail index, coordination issues, and the RFI-candidate
contract are Phase 2. Coverage status, the QC gate, and promotion of
`classified → complete` (which lets the router reach QUERY) are Phase 3. Until
then a built set stays in BUILD-resume — correct, because it isn't QC-verified
yet.
