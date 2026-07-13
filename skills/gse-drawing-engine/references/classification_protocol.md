# Classification Protocol (Phase 1)

This is the AI step of the write engine. Scripts split, extract, and render
(deterministic); **Claude classifies** (understanding). For **every** page in
`<set>/sheets/manifest.json`, write one file:
`<set>/sheets/page_NNNN/classification.json`. Then `build_sheet_index.py`
validates and assembles them — it does not classify.

## How to classify one page

1. Read `<set>/sheets/page_NNNN/page_NNNN.txt` — the extracted vector text.
2. View `page_NNNN.png` — the rendered sheet, for layout/overview. If the title
   block or a callout is too small to read, crop it sharply with
   `crop_region.py` (Phase 4 utility) rather than guessing.
3. Apply `references/drawing_types.md` to set `discipline`, `document_type`,
   `view_type`, and `confidence`. Classify from **content**, never the filename
   or a single keyword.
4. Set the provenance fields per `references/provenance_contract.md`:
   `source_type` and the sheet-level `extraction_confidence` (the confidence
   ceiling). Rate lower when in doubt.
5. Write `classification.json`.

## Per-page contract

```json
{
  "sheet_number": "C-101",
  "title": "YARD PIPING PLAN",
  "discipline": "Civil",
  "document_type": "contract_drawing",
  "confidence": "high",
  "extraction_confidence": "high",
  "source_type": "pdf_text",
  "secondary_disciplines": ["Process"],
  "summary": "1-3 plain-language sentences on what the sheet shows.",
  "key_elements": ["24\" influent main", "splitter box SB-1"],
  "systems": ["influent conveyance"],
  "equipment_tags": ["SB-1", "P-101"],
  "tag_details": [
    {"tag": "P-101", "type": "submersible pump", "size": "", "service": "influent", "evidence": "pump schedule, this sheet"}
  ],
  "key_callouts": ["24\" INFLUENT INV 92.50", "#6 @ 12\" OC EW", "STA 12+50"],
  "details_defined": [],
  "scale": "1\"=20'",
  "view_type": "plan",
  "scope_relevant": true,
  "notes": ""
}
```

Required: `sheet_number`, `title`, `discipline`, `document_type`, `confidence`,
`extraction_confidence`, `source_type`, `summary`, `view_type`. Use the closed
enum values from `drawing_types.md` and `provenance_contract.md` exactly. If the
sheet number is unreadable, use `"UNK-<page>"` and set `confidence: "low"`.

### Depth fields (capture while the `.txt` is already open — cheap)

- **`key_elements` / `systems`** — salient drawn items and named systems.
- **`equipment_tags`** — the canonical tag **strings** on the sheet (e.g.
  `"P-101"`, `"FIT-2103"`). This is what `build_tag_index.py` inverts. `[]` if none.
- **`tag_details`** *(optional, PRD Q2 lean)* — lightweight attributes for tags
  you can read off the sheet at no extra cost: `{tag, type, size, service,
  evidence}`. **Store raw; do not build typed registers** — that is v2. Only fill
  a field you actually see; leave it `""` otherwise. Skip the whole array on
  sheets with no readable attributes.
- **`key_callouts`** — ~5–10 notable dimensions, rebar, materials, elevations, or
  stations actually printed (e.g. `"#6 @ 12\" OC"`, `"2'-0\" MIN COVER"`). `[]`
  on legends/schedules with none. Makes depth queryable.
- **`details_defined`** — **only on detail sheets**: the details drawn here, as
  `{"number","title"}`. `[]` elsewhere. Feeds the detail index (Phase 2).

## Working style

- For large sets, classify in batches (10–20 sheets), writing each
  `classification.json` as you go. The per-page files make the work **resumable**
  — if interrupted, only un-classified pages remain (FS-7).
- Then run `build_sheet_index.py` — it errors loudly on a bad enum, a missing
  required field, or an FS-3 ceiling violation, writing nothing until fixed.
- Then run `build_tag_index.py` to build the inverted lookup.
