# Batch Processing & Resume

Large project manuals (a 500-page set can hold 40+ sections, each producing three output files plus an index row) cannot reliably be processed in one session. This reference defines how to split the work into resumable batches, checkpoint progress per section, stop at a clean point, and pick back up the next day without re-reading anything already done.

The unit of work is the **CSI section**, not the page. A section is atomic: it produces one full section `.md`, one review card, one raw pointer, and one index row, all from a single read. Pages only decide how many sections to group before a stopping point.

---

## When to build a ledger

| Source | Ledger? |
|---|---|
| Single-section PDF | No — process directly. |
| Small addendum (a few sections) | No — process directly. |
| Combined manual, ≤ ~60 pages and ≤ ~8 sections | Optional — usually fine in one session. |
| Combined manual, larger than that | **Yes — always.** |

When in doubt, build the ledger. It costs little and makes the run resumable.

---

## Batching rules

1. List every section with start page, end page, and page count (from the TOC / CSI headers — no deep read required yet).
2. Walk the list in order, accumulating sections into a batch until adding the next one would exceed **~50 pages**. Close the batch there and start the next.
3. **Never split a section across a batch.** A section is atomic.
4. A single section longer than ~50 pages is its own batch (don't break it).
5. ~50 pages is a target, not a hard limit. Keeping a natural division boundary (e.g. all of Division 3 together) intact is worth ±10 pages of slack. Prefer batch boundaries that fall on division boundaries when they're close.
6. Number batches sequentially starting at 1.

---

## The ledger: `specs-md/_PROCESSING_STATE.md`

One ledger per spec set, written at Step 2.5, updated after every section. Use this exact structure:

```markdown
# Processing State — [Source PDF name]

- **Source:** specs/[filename].pdf
- **Issue date:** YYYY-MM-DD   (or `date-unconfirmed`)
- **Extraction path:** A (Bluebeam) | B (pdftotext)
- **Total pages:** NNN
- **Total sections:** NN
- **Total batches:** N
- **Batches done:** N
- **Last updated:** YYYY-MM-DD
- **Resume at:** Section NN NN NN — [title]  (batch N)   ← first `pending` section; `— COMPLETE —` when none remain

| # | Section | Title | Pages | Batch | Status | Processed | Files |
|---|---------|-------|-------|-------|--------|-----------|-------|
| 1 | 01 33 00 | Submittal Procedures | 1–12 | 1 | done | 2026-06-25 | S C P I |
| 2 | 03 30 00 | Cast-in-Place Concrete | 13–41 | 1 | done | 2026-06-25 | S C P I |
| 3 | 03 60 00 | Grouting | 42–55 | 2 | pending | — | — |
```

Status values:
- `pending` — not yet processed.
- `done` — all four artifacts written (full section, card, pointer, index row).
- `flagged` — processed but needs human attention (e.g. scanned pages, extraction QC failure, undefined criteria the reviewer should know about). Note why in a trailing notes line; still counts as processed for resume purposes.

The **Files** column ticks which artifacts were written: `S` full Section, `C` Card, `P` Pointer, `I` Index row. All four present = a complete section.

---

## Per-section checkpointing

Update the ledger **after each section**, not after each batch. The moment Steps 3–6 finish for a section:

1. Set that row's status to `done` (or `flagged`).
2. Fill in the processed date and the Files column.
3. Save the ledger.

This guarantees that if the session is interrupted mid-batch — usage runs out, a crash, the user steps away — every section already finished is permanently recorded and never reprocessed.

After the last section in a batch, also update the header block: increment **Batches done**, refresh **Last updated**, and move **Resume at** to the first remaining `pending` section (or `— COMPLETE —`).

---

## Stopping point (stop-and-wait)

After a batch completes, **stop**. Do not roll into the next batch. Report a clean checkpoint:

> Batch 3 of 9 done. 14 of 41 sections complete. Next up: Section 03 30 00 (Cast-in-Place Concrete), batch 4. Re-run the skill on this spec set to continue tomorrow.

Always state: batches done / total, sections done / total, and the exact next section. This is the user's control point for managing usage.

---

## Resuming

At Step 0, before any extraction, check for `specs-md/_PROCESSING_STATE.md`:

1. **No ledger** → fresh run. Proceed normally.
2. **Ledger exists with `pending` sections** → resume:
   - Read the ledger and the **Resume at** pointer.
   - Confirm the source PDF matches.
   - Tell the user where things stand ("Resuming — 14 of 41 done, picking up at batch 4").
   - Re-open the PDF and run Steps 3–6 only for the current batch's `pending` sections. Skip every `done` section — do not re-read or rewrite them.
   - Continue the batch loop from there.
3. **Ledger exists, all `done`** (Resume at = `— COMPLETE —`) → tell the user the set is fully processed. Offer to reprocess a specific section or handle an addendum, but don't redo the whole manual.

**Never restart a partially-done manual from scratch** unless the user explicitly asks to, or the source PDF has changed (a revised manual / new addendum — handle per `addenda_and_versioning.md`).

---

## Integrity note

The ClaudeOS mount can occasionally truncate rapid writes. After updating the ledger, the row count should equal **Total sections**. If the ledger ever looks truncated or shorter than expected, rebuild it from the output folders: every `[section]_CARD.md` present in `specs-md/review-cards/` is a `done` section. Reconstruct the table from what's on disk rather than trusting a corrupted ledger.
