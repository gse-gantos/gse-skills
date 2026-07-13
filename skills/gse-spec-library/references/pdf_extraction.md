# PDF Extraction

Extract spec PDF text once upfront, QC the output section by section, and only fall back to visual page inspection where text actually broke down. Two parallel paths cover Bluebeam-connected and non-Bluebeam workflows — choose at startup and do not switch mid-run.

---

## Path detection

At startup, attempt a lightweight Bluebeam MCP call:

```
tool: list_studio_sessions   (or list_studio_projects)
```

- **Succeeds → Path A (Bluebeam):** Full extraction and visual QC workflow.
- **Fails or errors → Path B (no Bluebeam):** `pdftotext` extraction with user-assisted visual QC.

Tell the user which path was selected before proceeding. If Path B was selected and the user confirms Bluebeam is open, retry detection once, then proceed on the result.

---

## The approach

Both paths use the same scan detection heuristics and section-level QC logic. The difference is what happens when QC flags a page for visual inspection.

| Path | Extraction | Visual QC when flagged | Condition |
|---|---|---|---|
| A | Bluebeam `save_as_text` | Bluebeam screenshot | Bluebeam MCP connected |
| B | `pdftotext -layout` | Surface page number to user | No Bluebeam MCP |

Within each path, four tiers control what happens when extraction degrades:

| Tier | Method | When to use |
|---|---|---|
| 1 | Full-document text extraction | Default. Always try first. |
| 2 | OCR prompt — flag scanned pages to user | Whole document or specific pages have no text layer |
| 3 | Visual page inspection | Specific pages flagged as jumbled by QC |
| 4 | Flag as unreadable, stop | Page is scanned and OCR not run; cannot proceed |

---

## Path A — Bluebeam

### Tier 1 — Full text extraction and scan detection

Open the PDF in Bluebeam and extract the full document text in one call:

```
tool: open_file       → open specs/[file].pdf in Revu
tool: save_as_text    → extract full text to specs/[file].txt
```

Then read the `.txt` file. Before doing anything else, run scan detection.

### Scan detection — run immediately after extraction

`save_as_text` returns nothing useful for scanned pages but does not error — it silently produces empty or near-empty output. Detect this before writing any artifacts.

**Document-level check (run first):**

| Signal | What it means |
|---|---|
| Output file is empty or under ~500 characters for a multi-page document | Whole document is likely scanned — no text layer at all |
| No CSI section headers (`SECTION NN NN NN`) visible anywhere | Either scanned, or a non-spec document — confirm with user |
| Total word count suspiciously low for page count (under ~150 words/page average) | Partial scan — some pages have text layer, some don't |
| Text present but consists almost entirely of numbers, symbols, or gibberish | Encoding failure or partial scan |

**Page-level check (run per section during QC):**

| Signal | What it means |
|---|---|
| Section extracted to under ~100 words with no Part 1/2/3 structure | That section's pages likely scanned |
| Section text jumps from one paragraph directly to a CSI header with no Part 2 or Part 3 content | Middle pages of the section likely scanned |
| Specific page range returns blank when cross-referenced against total word distribution | Those pages have no text layer |

### What to do when scan is detected (Path A)

**Whole document scanned:**
Stop. Do not proceed to section QC. Tell the user:
> "The full text extraction returned [N] characters for a [P]-page document — this appears to be a scanned PDF with no text layer. Please run Bluebeam's OCR function (Document → OCR) on the file and save the result, then re-run extraction on the OCR'd version."

**Partial scan (specific pages or sections):**
Continue processing sections that have clean text. For each section flagged as likely scanned, tell the user:
> "Section [NN NN NN] — [Title] appears to have scanned pages (extracted under [N] words with no product requirements visible). Please run OCR on pp. [N]–[M] in Bluebeam and re-run, or manually provide the content for this section."

Do not write artifacts for a section where scan detection fired and OCR has not been run. Write a placeholder entry in `SPEC_INDEX.md` noting the section is pending OCR.

**Never silently write empty or near-empty artifacts.** A blank review card is worse than no review card — it looks complete but contains nothing.

### Tier 2 — OCR (user action required, Path A)

The skill cannot run OCR itself — Bluebeam's OCR is a user-initiated function. When scan detection fires, pause and let the user run OCR manually.

**User steps in Bluebeam:**
1. With the PDF open in Revu, go to **Document → OCR**
2. Select the page range (whole document, or specific pages flagged by the skill)
3. Run OCR and save the file (Bluebeam writes the text layer into the existing PDF)
4. Tell the skill to re-run extraction on the saved file

After re-extraction, re-run scan detection. If the OCR pass produced usable text, continue to section QC. If it still returns poor results, escalate to Tier 3 visual inspection and note the limitation in the artifacts.

### Tier 3 — Section-level QC and targeted visual inspection (Path A)

Run the QC heuristics in the **Shared QC** section below on each section's extracted text before writing any artifacts.

When QC flags a section, identify the suspect pages and inspect them visually via Bluebeam:

```
tool: get_page_information  → confirm page count and identify target pages
tool: computer              → screenshot the flagged pages in Bluebeam for visual read
```

Manually extract the correct values from the visual and substitute them into the section content. Note in the full section `.md` header: `Extraction note: [paragraph/table] read visually — text extraction garbled on p.[N].`

Do not visual-inspect the whole document. Only the flagged pages.

### Tier 4 — Unreadable page (Path A)

If visual inspection shows the page is a scanned image and OCR has not been run (or OCR ran but produced unusable output):

- Do not guess at content.
- Record the page as `[unreadable — scanned image, OCR required]` in the raw pointer's page map.
- Note in the full section `.md`: `Extraction note: p.[N] is a scanned image with no usable text — content not captured.`
- Flag to the user after the run with the specific page numbers.
- Do not write a review card or full section for a section where critical Part 2 content is in Tier 4 pages.

---

## Path B — No Bluebeam

### Tier 1 — Full text extraction and scan detection

Extract with `pdftotext`:

```bash
pdffonts "specs/[file].pdf"                                  # scan detection: empty output = no text layer
pdftotext -layout "specs/[file].pdf" "specs/[file].txt"      # extract full document
```

`pdffonts` returning no font entries means no text layer — OCR is required before extraction will produce anything useful. Flag to the user the same way as Path A.

Run the same document-level and page-level scan detection heuristics as Path A on the resulting `.txt` file.

### What to do when scan is detected (Path B)

**Whole document scanned:**
Stop. Tell the user:
> "The full text extraction returned [N] characters for a [P]-page document — this appears to be a scanned PDF with no text layer. Please open the file in Bluebeam or Adobe Acrobat, run OCR, save the result, and re-run this skill on the OCR'd version."

**Partial scan:**
Continue processing sections with clean text. Write placeholder entries for scanned sections. Same rules as Path A.

### Tier 2 — OCR (user action required, Path B)

Without Bluebeam, the user must run OCR in whatever PDF tool they have (Bluebeam, Adobe Acrobat, etc.). Same workflow: run OCR, save file, re-run the skill.

### Tier 3 — Section-level QC and user-assisted visual inspection (Path B)

Run the same QC heuristics (see **Shared QC** section below). When QC flags a page or table, the skill cannot take screenshots. Instead:

1. Note which paragraphs or tables are suspect with their estimated page numbers.
2. Tell the user:
   > "Page ~[N]: [paragraph/table name] appears garbled in text extraction — likely a collapsed table or complex layout. Please check this page in your PDF viewer and provide the correct values, or flag it for review."
3. Wait for user input before writing those values, or mark the content as `[requires manual review — text extraction garbled, no visual QC available]` and proceed.
4. Add to the full section `.md` header: `Extraction note: Path B — no visual QC available. [N] items flagged as potentially garbled. Verify before use.`

### Tier 4 — Unreadable page (Path B)

Same treatment as Path A — record as unreadable, flag to user, do not guess.

### Path B fidelity notes

All output files produced under Path B must include a fidelity note in the header block:

```
**Extraction path:** Path B (pdftotext — no Bluebeam visual QC)
**Fidelity note:** Tables and complex layouts were not visually verified. Review flagged items before relying on them for approval decisions. Re-run under Path A with Bluebeam for higher-confidence output.
```

This applies to all three artifacts (full section, review card, raw pointer). Path B artifacts are usable — the note exists so downstream reviewers know what was and wasn't verified.

---

## Shared QC heuristics

Apply these to every section after extraction, regardless of path. Flag a section or paragraph when you see:

**Character-level problems**
- Words running together with no spaces: `concretestrengthshallbe`, `6"HDPEpipe`
- Numeric values jammed against units: `150PSI`, `200WOG`, `SCH40`
- Non-ASCII garbage characters or symbol strings: `•Ã¢â‚¬Â¢`, `Ã‚Â°`
- Repeated identical characters suggesting encoding failure

**Layout collapse**
- Table rows that collapsed into a single run-on line
- Column data merged: `Body MaterialDuctile IronPressure Rating150 WOG` (should be separate cells)
- Paragraph that is a single line of mixed numbers and abbreviations with no sentence structure

**Truncation**
- Key spec fields that appear cut off mid-value: `pressure rating shall be 1` (truncated)
- Bulleted lists where items are missing — compare count to visible document structure if possible
- Section that ends abruptly well before the next CSI header

**Length anomalies**
- A Part 2 (Products) section under ~200 words — Part 2 is always substantive; short = likely truncated or scanned
- Any paragraph under 15 characters that should be prose

### Tables are the most common failure point

Spec tables (valve schedules, pipe schedules, material lists) frequently collapse in text extraction. If a section contains a table and the extracted text looks like a collapsed run-on, go straight to visual inspection for that table — don't try to parse the garbled text. It's faster to read it visually once than to try to reconstruct a table from mangled output.

- **Path A:** Use Bluebeam screenshot for flagged table pages.
- **Path B:** Surface the estimated page number to the user for manual inspection.

---

## Page number tracking

`save_as_text` (Path A) and `pdftotext` (Path B) may not preserve precise page breaks. For the raw pointer, page numbers matter — they're how the markup step confirms it's marking the right page.

Best practice:
1. Note any page markers preserved in the text output (`\f` form-feed characters often mark page breaks in `pdftotext` output; Bluebeam may produce similar markers).
2. Cross-reference section start/end pages:
   - **Path A:** Use `get_page_information` for any section where the pointer needs to cite a specific page.
   - **Path B:** Estimate from form-feed counts, or ask the user to confirm page ranges for critical sections.
3. If page tracking is uncertain for a section, note it in the raw pointer: `Pages: ~[N]–[M] (estimated — verify in source PDF)`.

Uncertain page numbers in the pointer are better than wrong page numbers. A wrong page number sends the reviewer to mark the wrong page.
