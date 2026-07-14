# Provenance & Confidence Contract (FS-3)

Every extracted claim in `drawing-db/` carries its origin and how much to trust
it. This is the single defense against a low-confidence or inferred value being
used as fact in an RFI, takeoff, or budget downstream. It is mandatory on every
record the write engine produces.

## The three fields

1. **`source_type`** — how the claim was read. Closed set:
   `pdf_text` · `bluebeam_text` · `bluebeam_markup` · `image_visual` · `crop` ·
   `ocr` · `user_note` · `inference`.

   **Field-validated caveat on `bluebeam_text` / `pdf_text` for vector CAD (L-001):**
   on vector-CAD sheets, text extraction (Bluebeam `save_as_text` and often the
   embedded PDF text layer) returns the **title block only** — sheet number,
   title, date — with the schedules, key notes, tags, and dimensions absent.
   Do not classify a vector-CAD sheet from `bluebeam_text` and rate it `high`;
   the "text" you got is the title block, not the sheet. Read vector-CAD sheets
   visually (`image_visual`) plus high-DPI crops, and note the reason. This does
   not apply to scanned/raster sheets, where OCR can recover body content. See
   `references/validated_constraints.md` (L-001) for the full finding.
2. **`confidence`** — `high | medium | low`.
3. **`evidence`** — enough to find it again: sheet number + page, and (where
   applicable) the callout/phrase quoted or the visual description.

Inferences are labeled **`[inferred]`** in any text and never presented as fact.

## The sheet-level confidence ceiling

Each sheet's classification carries an **`extraction_confidence`** — how reliably
the sheet itself was read (a clean vector-text sheet is `high`; a sheet that
needed a visual fallback or came in scanned is `medium`/`low`). This value is a
**ceiling**: no record sourced from that sheet may claim a higher confidence than
the sheet it came from. `build_sheet_index.py` enforces this — a per-page record
whose `confidence` exceeds its `extraction_confidence` is a validation error and
nothing is written until it's fixed.

`build_tag_index.py` applies the same rule across sheets: a tag's aggregate
confidence is the **minimum** `extraction_confidence` of the sheets it appears
on — a tag is never more trusted than the least-trusted sheet it was read from.

## How `source_type` and `extraction_confidence` are set in the v1 spine

The full multi-method source validation (cross-comparing Bluebeam text vs. PDF
text vs. visual) is a v2 feature. In the v1 spine, derive them cheaply at
classification time:

- Sheet has dense, coherent vector text (`text_chars` healthy, callouts legible
  in the `.txt`) → `source_type: pdf_text`, `extraction_confidence: high`.
- Sheet text is thin or the `.txt` clearly dropped a schedule/table you can see
  in the PNG, so you read it from the image → `source_type: image_visual`,
  `extraction_confidence: medium` (or `low` if you couldn't fully resolve it).
- Sheet is flagged `likely_scanned` in the split manifest (little/no text) and
  read entirely from the image → `source_type: image_visual`,
  `extraction_confidence: low` unless a crop made it clearly legible.
- A value you had to read from a high-DPI crop → `source_type: crop` on that
  record's evidence.

When in doubt, rate lower. A correctly-cautious `medium` costs nothing; an
optimistic `high` on a misread schedule propagates a wrong number into an RFI.
