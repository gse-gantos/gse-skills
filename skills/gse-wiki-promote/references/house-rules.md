# gse-wiki house rules

Shared by all four gse-wiki skills (ingest / promote / query / audit). These OVERRIDE the upstream gsewiki plugin's generic assumptions. Where this file and `_Memory/AGENTS.md` differ, AGENTS.md wins.

## Layout (F3 fixes — this is the real repo shape)

```
Claude/_Memory/
  AGENTS.md        # operating contract — read first, every session
  index.md         # routing index
  log.md           # append-only change log
  wiki/            # maintained knowledge layer (~51+ pages: seed + project)
  meta/            # open-questions.md, contradictions.md, audits, tag taxonomy
  _raw/            # PE's manual input channel — IMMUTABLE (note: underscore, not raw/)
  outputs/         # unpromoted artifacts (created 2026-07-10; promote's staging home)
```

Hierarchy for reading: `index.md → wiki/ → meta/ → _raw/ → outputs/`. There is no `raw/` — it's `_raw/`. AGENTS.md lives IN `_Memory/`, not repo root.

## Any-source ingest (D5/D6 — the v2 upgrade)

Ingest consumes from wherever **the map** points — not just `_raw/` and skill outputs. Sources: `Claude/Map/views/UNPROCESSED.md` queue items routed to ingest by the §4 schema; skill outputs (specs-md, drawing-db, extracted meetings); `_raw/`; any mapped document anywhere in the project folder. **Mixed packages split per D6:** each piece routes to its content-type home; ALL pieces cross-link to ONE package node (a wiki page preserving the original grouping, e.g. `ce-03-package.md`). Never move raw files; record provenance from the map record.

**Do not bulk-process the queue unprompted** (standing rule): ingest runs when a human asks for a specific source or approves a proposed one.

## Link mesh (D9 — three enforced layers)

1. **Backlinks:** every synthesis file created ANYWHERE by any skill carries `**Wiki:** [[hub-page]]` at creation.
2. **Hub pages:** every processed set/package gets or updates a wiki hub (`headworks-bypass-drawings` is the model): what it is, where the synthesis lives, headline findings, open items.
3. **Topic weaving:** ingest also touches the relevant TOPIC pages — a gasket decision lands links on `bolts-nuts-gaskets`, not just the hub.

Density target ~40%, but **dense AND relevant** — indiscriminate linking destroys routing value; relevance is the gate. **Ghost nodes are a supported house feature** (unlike upstream): ~21 intentional page-less nodes (people, shared entities) connect clusters by design. Prefer linking existing pages; use ghost nodes deliberately for shared entities; formal policy lands in ultraplan P5.3.

## Seed overlay (3.3 — keeps seed and job knowledge separable)

When an ingested project fact (locked decision, RFI resolution, binding clarification) also belongs on a **seed/topic page** (pipe-materials, valves, bolts-nuts-gaskets, waterstop, division-3-concrete, …), add it under an overlay heading on that page:

```markdown
## Project decisions
- 1/8" EPDM flange gaskets project-wide (Opterra Clarifications 11/20/2025) — see [[hub-or-decision-page]]
```

Never blend job facts into seed prose outside the overlay heading — harvest (P6.4) must be able to separate company knowledge from job facts at closeout.

## Map-update contract (3.5 — MANDATORY, see Claude/Map/machine/MAP_UPDATE_CONTRACT.md)

After every ingest/promote that consumes a mapped source: mark the manifest record processed with `processed_home` pointer(s); register supersessions; add records for stumbled-on files (propose off-convention finds, D8); regenerate views (`gse-cartographer/scripts/render_views.py`); log it.

## House formats

- **Frontmatter** (required, all wiki pages): `title, type, status, created, updated, source_depth, confidence, sensitivity, tags, related`. Slug filenames.
- **Log entries** (house style, NOT upstream's one-liner): `## YYYY-MM-DD — Ingest: Title` followed by `- **Action:** / - **Sources:** / - **Pages affected:** / - **Notes:**` bullets. Existing `log.md` is exemplary — match it.
- **Source attribution required** on every claim (AGENTS.md §5).
- **Compounding, not overwriting:** contradictions go to `meta/contradictions.md`, never silently resolved.

## Job-specific cautions

- **PII discipline (D7):** synthesis from payroll/payment/timecard sources summarizes — individual wage/PII detail stays out of wiki prose.
- **Three-firm rule:** any drawing-derived claim cites whose drawing (original EOR / PK / MKM / G3). PK=concrete/structural layout, MKM=equipment supports/handrails/screw conveyor slab; overlaps get flagged, not resolved.
- **Binding clarifications:** the 11/20/2025 Opterra table in AGENTS.md §3 overrides spec text — don't re-flag those as discrepancies or contradictions.
- **Never delete** — retire to `Claude/_archive/` (standing rule).
