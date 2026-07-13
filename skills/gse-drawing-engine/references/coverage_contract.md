# Coverage Contract (FS-4)

The single guard against presenting a partial catalogue as complete. Every
consumer of `drawing-db/` — the query layer, the RFI generator, any v2 output —
**checks coverage before generating output**, and surfaces a caveat or refuses
when the sheets it needs aren't processed.

## `machine/coverage_status.json`

Written by `build_coverage.py` from the post-QC processing ledger. Fields:

- `current` — **True only when the run is complete**: every sheet processed, none
  pending/classified, none failed. A consumer may treat the set as whole only
  when this is True.
- `run_status` — mirrors the ledger (`building | partial | complete`).
- `total_sheets`, `processed` (count of `complete`), `pending`, `failed`,
  `needs_verification` (the YELLOW sheets — answerable but flagged).
- `by_discipline` — total/processed/pending/failed per discipline.
- `unanswerable_domains` — disciplines with any pending/failed sheet; questions
  about these aren't fully supported.

## YELLOW vs. FAILED

- A **YELLOW** sheet is `complete` and queryable, but flagged: it needed a visual
  fallback, came in at medium confidence, or is a dense schedule read below high
  confidence. Answers from it carry a caveat. It still counts as processed.
- A **FAILED** (RED) sheet is an explicit gap — kept in the ledger for honesty,
  never silently dropped. It is NOT processed; questions about it must be refused
  or answered only after (re)processing.

## Mandatory banner

Every markdown view in `views/` carries a coverage banner at the top, derived
from `coverage_status.json`:

- Complete: `> COVERAGE: complete — N/N sheets processed (k flagged for verification).`
- Partial: `> COVERAGE: PARTIAL — M/N sheets processed. Answers about un-processed
  sheets are NOT supported.  pending: …; failed: …`

The view builders (`build_rfi_candidates.py`, the query summary, …) read coverage
and stamp this automatically — re-run them after QC so banners reflect the final
numbers. Never hand-edit a banner; it's a projection of the JSON (D5).
