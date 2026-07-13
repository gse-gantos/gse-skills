---
name: gse-spec-library
description: Job-824 fork of spec-library (ultraplan 4.1) — input is whatever spec-type files the Project File Map queues, from ANYWHERE in the project folder; outputs per the D1 placement rule. Convert construction specification PDFs (combined project manuals, individual CSI sections, or addenda) into a normalized set of per-section markdown files plus a master index, so submittals can later be reviewed cheaply without re-reading source PDFs. Use this whenever the user points to spec PDFs, a project manual, or an addendum and wants them processed, indexed, or prepped for submittal review. Also trigger when the user says "add this to my library", "file this spec", "process this spec", "file this", "log this spec", "add to spec library", "save to library", or similar phrasing indicating they want a spec saved for future reference. Also trigger on "specs-md", "SPEC_INDEX", processing a project manual, or extracting discrepancy checklists from specs — even if they don't say the word "skill". This is step 1 of a two-skill submittal-review system; it produces the retrieval layer the submittal-reviewer skill consumes.
---

# GSE Spec Library (824 fork)

> **Fork provenance:** forked 2026-07-10 from installed `spec-library` per ultraplan 4.1. Changes: map-driven input, D1 output placement, `_Memory/` orientation replacing the retired MEMORY.md loader, backlink emission, map-update contract. Extraction, batching, templates, and QC are inherited unchanged.

Convert spec PDFs into a layered retrieval system. Read each section once, produce three artifacts per section plus a master index, and never pay the cost of re-reading the source PDF on every future submittal review. Everything downstream (`submittal-reviewer`) consumes these artifacts — extraction quality here determines review quality later.

---

## Project 824 OS — inputs and outputs

*(Replaces upstream's three-tier workspace detection — this fork runs in exactly one environment: the Job 824 `Claude/` OS. See `_Memory/AGENTS.md`.)*

**Input — wherever the map points (D5).** Source spec PDFs may sit anywhere in the project folder (`Specs & Drawings/Specs/`, a submittal package, a Change Events folder). Find them via `Claude/Map/` (`views/FILE_MAP.md` / `UNPROCESSED.md`) — never assume a fixed input folder, never move or rename the raw PDF. Record the source path exactly as found (provenance).

**Output — D1 placement rule (writes ONLY inside `Claude/`):**

```
Claude/Specifications/                        <- JOB-WIDE layer (the Project Manual):
    full-sections/  review-cards/  raw-pointers/
Claude/Specifications/_spNN-name/specs-md/    <- SUBPROJECT-scoped layer:
    SPEC_INDEX.md + full-sections/ review-cards/ raw-pointers/
```

Job-wide manual sections -> the flat layer; subproject-issued specs -> that subproject's `specs-md/`. Unsure which layer? Ask. Create missing output folders before writing.

**Existing state (don't clobber):** the job-wide layer holds 63 sections from the consolidated Project Manual; `_sp01`/`_sp02` have populated SPEC_INDEXes. Always read the existing index and edit in place.

---

## Bluebeam availability

At startup, attempt a lightweight Bluebeam MCP call to detect connectivity:

```
tool: list_studio_sessions   (or list_studio_projects)
```

- **Call succeeds → Path A (Bluebeam):** Full extraction and visual QC workflow.
- **Call fails or errors → Path B (no Bluebeam):** `pdftotext` extraction with reduced visual QC capability.

Tell the user which path was selected before proceeding. If Path B was selected and the user confirms Bluebeam is actually open, retry detection once then proceed on the result.

Full details for both paths in `references/pdf_extraction.md`.

---

## How spec PDFs are read

**Path A:** Open the PDF in Bluebeam and extract full document text in one call using `save_as_text`. Parse from the resulting text file. After extraction, run scan detection and section-level QC. Visual inspection of flagged pages via Bluebeam screenshot.

**Path B:** Extract using `pdftotext -layout` via bash. Same scan detection and QC heuristics apply. When QC flags specific pages, surface the page numbers to the user for manual inspection — visual screenshot is unavailable without Bluebeam. Note Path B fidelity limitations in all output files.

Full extraction workflow, QC heuristics, and both paths in `references/pdf_extraction.md`. Read it before touching any PDF.

---

## Workflow

### Step 0 — Orient in the 824 OS

1. Read `Claude/CLAUDE.md` -> `_Memory/AGENTS.md` if not already loaded this session. AGENTS.md §3 carries the binding 11/20/2025 Opterra clarifications table — it OVERRIDES spec text; review cards must reflect it (e.g., 09 90 00 governs painting; 1/8" EPDM gaskets project-wide).
2. Locate the source in `Claude/Map/machine/manifest.json`; note its record id, type confidence, and subproject. Unmapped source -> add a record first (cartographer rules; propose if off-convention, D8).
3. Job context (three-firm risk, locked decisions, subproject status) comes from `_Memory/` wiki pages — query via gse-wiki if needed. The old ClaudeOS MEMORY.md hierarchy is RETIRED (AGENTS.md §9) — do not look for MEMORY.md files.
4. `references/memory_workflow.md` in this fork is rewritten as the 824 orientation reference — read it for the correction-routing rules.

**Resume check (all tiers):**

After loading memory, check `specs-md/_PROCESSING_STATE.md`. If it exists and lists any section with status `pending`, a prior run on this spec set was left unfinished. Do **not** start over:

1. Read the ledger.
2. Tell the user where things stand: e.g. "Resuming WCW project manual — 14 of 41 sections done, picking up at batch 4 (Section 03 30 00)."
3. Skip straight to Step 8 (batch processing) and resume at the first `pending` section.

Only run Steps 1–7 from scratch when no ledger exists, or the user explicitly asks to reprocess. Full resume rules in `references/batch_processing.md`.

---

### Step 1 — Identify source type

Three types, each handled differently:

- **Combined project manual** — many sections in one PDF; detect boundaries, process section by section.
- **Single section PDF** — process directly.
- **Addendum** — process only the sections it revises; update only those index entries. Addendum version outranks project-manual version for those sections.

Detect sections by CSI headers (`SECTION NN NN NN — TITLE`). Sections are organized in Part 1 (General/Submittals), Part 2 (Products), Part 3 (Execution).

### Step 2 — Determine issue date

Priority order:
1. Addendum date from cover sheet or title block.
2. Document issue date from PDF title block or cover sheet.
3. No date findable — use today's date and mark `date-unconfirmed` in all output files and the index.

### Step 2.5 — Build the processing ledger & batch plan (combined manuals only)

Skip this step for a single-section PDF or a small addendum (just process it directly — no ledger needed). Run it for any combined project manual, and **always** when the manual is large enough that finishing in one session is doubtful (rule of thumb: more than ~60 pages or more than ~8 sections).

1. From the section boundaries detected in Step 1, build the full list of sections with their start/end pages and page counts. You do this from the table of contents / CSI headers and the extracted text — you do **not** need to have deeply read each section yet.
2. Group consecutive sections into **batches targeting ~50 pages each**. Never split a section across a batch boundary — a section is the atomic unit. A single section longer than ~50 pages becomes its own batch. Two or three short sections combine into one batch up to the page target.
3. Write `specs-md/_PROCESSING_STATE.md` — the resume ledger — using the template and rules in `references/batch_processing.md`. Every section starts as status `pending`.
4. Tell the user the plan: total sections, total batches, and that you'll process one batch per session then stop. Then begin Step 3 on batch 1.

This ledger is the resume backbone. From here on, the per-section steps (3–6) run **inside the batch loop** defined in Step 7 — process only the sections in the current batch, then stop.

### Step 3 — Write the full section `.md`

Output path: `specs-md/full-sections/[section-hyphenated]_[YYYY-MM-DD].md`

Use template in `references/section_template.md`. Apply relevant memory entries before writing. Never overwrite an existing file — if one exists for the same section and date, increment a suffix or confirm with the user.

### Step 4 — Write the review card

Output path: `specs-md/review-cards/[section-hyphenated]_CARD.md`

Use template in `references/review_card_format.md`. Apply relevant memory entries to: approval-critical trigger selection, applicability conditions, non-material differences, spec gap classification. If memory materially affected the card, note it in the `Memory applied` header field. Never overwrite an existing card without confirming with the user.

The review card is the most important output. `submittal-reviewer` reads it first on every review. Get it right before worrying about the other files.

### Step 5 — Write the raw pointer

Output path: `specs-md/raw-pointers/[section-hyphenated]_POINTER.md`

Use template in `references/raw_pointer_format.md`. Build this from the same extracted text used for Steps 3 and 4 — marginal cost is low since the PDF is already open. The pointer exists so future high-stakes escalations can verify source context without re-reading the whole project manual.

### Step 6 — Update `SPEC_INDEX.md`

The index is the read-first entry point for `submittal-reviewer`. Update it after every run using the template in `references/index_template.md`.

Three things the index must get right:
- **Current entries** — review card path, full section path, raw pointer path, and supersession chain all accurate.
- **Missing Sections Registry** — sections with no spec so the reviewer can say "no governing spec" honestly.
- **Undefined Criteria Registry** — sections requiring submittals but defining no acceptance standard.

When updating (not creating from scratch), read the existing index first and edit in place — regenerating from scratch loses prior rows and registry entries.

### Step 7 — Batch loop & stopping point (combined manuals with a ledger)

When a ledger exists (Step 2.5), Steps 3–6 are not run across the whole manual at once — they run one batch at a time:

1. Process every `pending` section in the **current batch**, running Steps 3→4→5→6 for each.
2. **After each section finishes**, immediately mark it `done` in `_PROCESSING_STATE.md` (set the processed date and tick the files written). Update the ledger per-section, not per-batch — an interruption mid-batch must never lose a completed section.
3. When the batch is complete, update the ledger header (batches done, last-updated date, resume pointer → first remaining `pending` section).
4. **Stop here.** Report a clean checkpoint to the user and do not start the next batch:

   > Batch 3 of 9 done. 14 of 41 sections complete. Next up: Section 03 30 00 (Cast-in-Place Concrete), batch 4. Re-run the skill on this spec set to continue.

5. On the next session, Step 0's resume check brings you straight back here at the first `pending` section.

If the whole manual fits comfortably in one session (no ledger was created), ignore this step and finish all sections in one pass, then go to Step 8.

Full batching, ledger format, and resume rules in `references/batch_processing.md`.

### Step 8 — Capture corrections into the wiki

If the user provides a correction during the session (a clarification outranks spec text, a section is superseded, an interpretation ruling), it is wiki knowledge, not a MEMORY.md entry:

- Route it through **gse-wiki ingest** (house rules apply: source attribution, seed overlay for topic pages, log entry).
- If it changes how a review card should read, update the card AND note the wiki page it came from.
- Never write MEMORY.md files anywhere.

### Step 9 — Backlinks + map-update contract (MANDATORY before finishing)

1. **Backlink emission (D9):** every SPEC_INDEX.md carries `**Wiki:** [[hub-page]]` (existing indexes already do — preserve it); new full-sections/review-cards inherit the index's hub. New spec sets get/update a wiki hub page via gse-wiki ingest.
2. **Map-update contract** (`Claude/Map/machine/MAP_UPDATE_CONTRACT.md`): mark the source's manifest record `processed` + `processed_home`; register supersessions (an addendum supersedes prior section versions -> old record/notes updated, feeds SUPERSEDED.md); regenerate views (`gse-cartographer/scripts/render_views.py`).
3. Log the run in `_Memory/log.md` (house format).

## What "good" looks like

Hand the review card to someone who's never seen the spec. They should be able to approve or flag most submittals using only the card, and know exactly when to go deeper. Pull requirements verbatim where a number or material is involved. Cite the paragraph. Distinguish real checkable requirements from boilerplate. Spec gaps are the engineer's undefined criteria, not the sub's deficiencies.

---

## Reference files

Read the relevant reference before each step — don't rely on memory of the template.

- `references/memory_workflow.md` — **rewritten for 824:** OS orientation, correction routing via gse-wiki, retired-MEMORY.md notice. Read at Step 0.
- `references/pdf_extraction.md` — Path A (Bluebeam) and Path B (pdftotext) extraction: scan detection, QC heuristics, visual inspection, page tracking, fidelity notes. Read before touching any PDF.
- `references/review_card_format.md` — review card template and field guidance. Read before Step 4.
- `references/section_template.md` — full section `.md` template. Read before Step 3.
- `references/raw_pointer_format.md` — raw pointer template. Read before Step 5.
- `references/index_template.md` — `SPEC_INDEX.md` template and update rules. Read before Step 6.
- `references/batch_processing.md` — large-manual batching, the `_PROCESSING_STATE.md` ledger template, per-section checkpointing, stopping points, and resume rules. Read at Step 2.5 (and at Step 0 when a ledger is found).
- `references/addenda_and_versioning.md` — addendum handling, supersession logic, version conflicts. Read when processing an addendum.
