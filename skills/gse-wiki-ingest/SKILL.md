---
name: gse-wiki-ingest
description: >
  Ingest source material into the job wiki (Claude/_Memory/). Fork of gsewiki:ingest tailored
  to this OS (ultraplan Phase 3): any-source ingest driven by the Project File Map, split-and-route
  for mixed packages, seed-page overlay enrichment, D9 link-mesh enforcement, and the map-update
  contract. Use when the user asks to process, ingest, file, or add a source — from _raw/, skill
  outputs, or ANY mapped document in the project folder.
---

# gse-wiki ingest (GSE fork)

Read `references/house-rules.md` first — it defines the real layout (`_Memory/`, `_raw/`, `outputs/`), the link mesh, the seed overlay, and the map-update contract. Respect `_Memory/AGENTS.md` always.

**Standing constraint:** never bulk-process the UNPROCESSED queue unprompted. Ingest runs on a human's specific request or an approved proposal.

## Workflow

1. **Locate via the map.** Find the source's record in `Claude/Map/machine/manifest.json` (or `views/FILE_MAP.md`). If it isn't mapped yet, add a record per the cartographer rules (propose classification if off-convention, D8). Note provenance.
2. **Enumerate link targets:** list `wiki/` filenames — the link inventory. (Ghost nodes for shared entities are allowed per house rules.)
3. **Assess the source:** type, origin, date, reliability. Discuss-first for important/ambiguous/sensitive/contradiction-relevant sources; direct ingest for routine ones.
4. **Mixed package? Split (D6):** identify the pieces; route non-narrative pieces to their content-type homes (drawing→drawing-engine, spec→spec-library — propose those runs, don't do them inline); create ONE package node wiki page preserving the grouping; cross-link every piece to it.
5. **Extract durable knowledge:** decisions, constraints, risks, entities, commitments, field conditions. Update existing pages before creating new ones. Required frontmatter on new pages; source attribution on every claim; contradictions to `meta/contradictions.md` — but check AGENTS.md §3's binding clarifications table first (those override spec text and are NOT contradictions).
6. **Enforce the mesh (D9):** hub page created/updated for the processed set; topic pages woven (first mention linked, ~40% density, relevance-gated); every non-wiki output file touched gets a `**Wiki:** [[hub]]` backlink.
7. **Seed overlay (3.3):** project facts that belong on seed/topic pages go under the `## Project decisions` heading — never blended into seed prose.
8. **Map-update contract (3.5):** mark the manifest record processed + `processed_home`; register any supersessions; regenerate map views.
9. **Index + log:** `index.md` entries for new/changed pages; house-style `log.md` entry.
10. Open questions → `meta/open-questions.md`.

## Report

Source processed (with map record id) · pages created/updated · package node (if split) · overlay edits · density/mesh check · map records updated · contradictions/open questions · items needing human review.
