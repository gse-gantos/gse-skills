# Router Protocol (Phase 0)

The router is a thin, deterministic state classifier run at the top of every
drawing-engine invocation. It answers one question — *what mode are we in?* —
from **disk + coverage state, never from the user's wording** (PRD §4.1). This
keeps the skill from, say, re-processing a finished set because the user said
"process" out of habit, or trying to query a set that was never built.

## Decision table

The router inspects `<set-dir>/machine/manifest.json` and
`<set-dir>/machine/coverage_status.json`.

| Disk / coverage state | Mode | Why |
|---|---|---|
| `manifest.json` absent | **BUILD** | No catalogue exists. Full process. |
| Manifest present; ≥1 sheet `processing_state: stale` | **UPDATE** | A sheet is revised/new. Reprocess only those sheets (Phase 5). |
| Manifest present; `run_status: building`, or ≥1 sheet `pending`/`partial` | **BUILD (resume)** | A run never finished. Continue from the manifest — never rebuild from scratch (FS-7). |
| Manifest present; `run_status: complete` or `partial`; no `stale` sheets | **QUERY** | Catalogue is as-built and current. Answer from it. |

`partial` as a *run_status* means a run concluded with some sheets `failed` (could
not be extracted) — the catalogue is queryable with coverage gaps, not stuck
forever in BUILD. `partial` as a *sheet processing_state* means that one sheet's
extraction is incomplete and the run is still active → BUILD (resume).

## Manifest state fields the router reads

- `run_status`: `building | complete | partial` — set by the build/QC steps.
- `sheets[].processing_state`: `pending | partial | complete | failed | stale`.
  - `pending` — discovered, not yet classified.
  - `partial` — classification started, not finished.
  - `complete` — fully processed and QC-passed.
  - `failed` — extraction could not be completed (kept for coverage honesty).
  - `stale` — source hash changed since last process (set by Phase 5 hash-diff);
    triggers UPDATE.

Until Phase 5 lands the hash-diff, no sheet is ever marked `stale` in normal
operation, so UPDATE only fires when a revision is explicitly detected. The
branch exists and is tested now so the spine is stable when Phase 5 plugs in.

## FS-1 — the deliberate seam (query never silently rebuilds)

The router classifies; it does not act. In particular, when the mode is QUERY and
a question targets a sheet whose coverage is `pending`/`failed`, the **query layer**
(Phase 4) returns a `coverage_gap` signal naming the missing sheets and lets the
caller decide. The router never auto-escalates a QUERY into a heavy BUILD. Cheap
single-sheet reads of already-processed sheets are allowed inline; full
(re)processing is never silent. This is the guard on the low-token guarantee.

## FS-2 — lazy reference loading (write protocols never load on a read)

`router.py` owns the single `MODE_REFERENCES` map: the exact reference files each
mode may load. The caller loads only that list. A QUERY decision lists **only**
`query_protocol.md`; it carries no processing/classification/provenance/coverage
write protocol. The script cross-checks the QUERY list against a `WRITE_PROTOCOLS`
set and **exits non-zero (code 3)** if any leaks in — so the guarantee is
machine-checkable, not just documented.

| Mode | Loads |
|---|---|
| BUILD | processing, classification, provenance, coverage contracts + drawing_types |
| UPDATE | incremental_update + processing, classification, provenance, coverage |
| QUERY | query_protocol only |

## Output contract

`router.py` prints a JSON object: `mode`, `set_dir`, `reason`, `run_status`,
`coverage`, `sheet_summary` (counts + stale/failed/pending sheet lists),
`load_references`, and `fs2_ok`. `--explain` prints the human-readable form. Exit
0 on a clean decision, 3 on an FS-2 violation.
