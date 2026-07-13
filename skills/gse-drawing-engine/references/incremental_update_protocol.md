# Incremental Update Protocol (Phase 5 — UPDATE mode)

UPDATE reprocesses only what changed when a drawing set is revised, then
regenerates every derived artifact from the current JSON so no projection drifts
(D5). This is the token-control guarantee: an unchanged sheet is never reprocessed.

## When UPDATE runs

- The user re-points at a revised PDF for an existing set ("the drawings were
  reissued / addendum 2 came in"). Run `update_drawing.py` to diff and re-render.
- Or the router already routed UPDATE because a prior `update_drawing` left sheets
  marked `stale` (an interrupted update to resume).

## 1. Diff + reprocess only changed sheets

```
python scripts/update_drawing.py "<new PDF or drawings/ folder>" --set-dir "<set>" --date YYYY-MM-DD
```

It compares each page's content hash against the ledger:

- **unchanged** → skipped entirely (files + classification + `complete` state kept);
- **revised** → pdf/png/txt re-rendered, old `classification.json`/`refs.json`
  deleted, state set `stale`;
- **new** → rendered, state `pending`;
- **removed** → dropped from the manifest + ledger, logged.

It rewrites `sheets/manifest.json` and the ledger, sets `run_status: building`,
and appends a changelog (`machine/changelog.json` + `views/changelog.md`).

### What the content hash is (and its limitation)

The hash is over the sheet's **normalized extracted text**, not raw PDF bytes.
This is deliberate: a re-exported set gives unchanged sheets new bytes/metadata,
which a byte hash would flag as changed (reprocessing everything). Text is stable
across re-export, and a revised callout/note/title-block changes the text. **Limit:**
a purely visual revision with no text-layer change (e.g. a moved line, no callout
change) won't be auto-detected — reprocess that sheet explicitly if you know it
changed (delete its `classification.json` and re-render, or rebuild the set).

## 2. Reclassify only the changed/new sheets (Claude)

Per `references/classification_protocol.md`, classify the pages now marked
`stale`/`pending` (their `classification.json` was cleared) — and only those. Add
`refs.json` for them if they carry callouts.

## 3. Regenerate ALL derived artifacts (so nothing drifts)

Run, in order, against the whole set:

```
build_sheet_index.py → build_tag_index.py → build_cross_references.py →
build_detail_index.py → build_rfi_candidates.py → qc_pass.py → build_summary.py
```

These rebuild the index, the inverted tag index, cross-references, details, RFI
candidates, QC/coverage, and `drawings.md` from the current JSON. A tag that
existed only on the revised sheet disappears; a new tag appears; coverage and the
banners reflect the new state. Derived files are never hand-patched — always
regenerated (D5).

## Result

Only the revised sheet's raw files and classification were touched; every index,
banner, and projection reflects the change; the changelog records what moved.
