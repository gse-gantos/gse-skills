# Project OS orientation (replaces upstream memory workflow)

> **Upstream superseded (2026-07-10, ultraplan 4.1/D2):** the ClaudeOS MEMORY.md hierarchy this file used to describe is retired. `Claude/_Memory/` is the single memory system on this job.

## Where knowledge lives

- **Operating contract:** `Claude/_Memory/AGENTS.md` — read first; §3 = binding owner/engineer clarifications (override spec text), §4 = routing schema, §9 = project rulings.
- **Job knowledge:** `Claude/_Memory/wiki/` — query via the gse-wiki-query skill, not by loading files wholesale.
- **Discovery:** `Claude/Map/` — where every raw file is, what's processed, what's superseded.

## Correction routing (replaces MEMORY.md capture)

User corrections during a spec run are durable knowledge → route through **gse-wiki ingest**: it lands on the right wiki/topic pages (seed overlay if applicable), updates `index.md`/`log.md`, and preserves source attribution. Card-affecting corrections also update the review card, citing the wiki page. Contradictions → `meta/contradictions.md`, never silently resolved. Check AGENTS.md §3 FIRST — a "conflict" already covered by the clarifications table is not a contradiction; don't re-flag it.

## Apply-memory equivalents at each step

- Review cards (Step 4): apply AGENTS.md §3 locks + relevant wiki topic pages so cards never re-flag settled items.
- Non-material differences / spec gaps: check `meta/open-questions.md` + the subproject's Missing Sections Registry (if one exists) before declaring a new gap.
