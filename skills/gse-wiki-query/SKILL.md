---
name: gse-wiki-query
description: >
  Answer questions from the job wiki (Claude/_Memory/). Fork of gsewiki:query — map-aware:
  knows what exists-but-unprocessed via Claude/Map/, so it can say "the wiki doesn't cover this
  yet, but the raw document exists at X" instead of a bare "unknown."
---

# gse-wiki query (GSE fork)

Read `references/house-rules.md` first. Respect `_Memory/AGENTS.md`. *(Note: until this fork is proven on real work, the plugin `gsewiki:query` remains the sanctioned query path — ultraplan 3.6. This fork supersedes it after validation.)*

## Workflow

1. Classify: lookup / factual / synthesis / source-verification / report / maintenance.
2. Route via `index.md` → relevant `wiki/` pages → follow load-bearing `[[wikilinks]]`. Check frontmatter confidence/source_depth.
3. Check `meta/open-questions.md` + `meta/contradictions.md` when the topic may have known gaps or conflicts. **Check AGENTS.md §3 binding-clarifications table** for anything spec-related — it overrides spec text.
4. **Map fallback (the map upgrade):** if the wiki lacks the answer, consult `Claude/Map/views/FILE_MAP.md` / `UNPROCESSED.md` before declaring ignorance — the answer may exist in a mapped-but-unprocessed document. Report that honestly: name the document and offer to ingest it (do not auto-process; standing rule).
5. Drawing-derived claims: confirm the current set via `SUPERSEDED.md` + subproject context; cite the responsible design firm (roster in AGENTS.md §9).
6. Answer directly; distinguish fact / source-backed / inference / uncertainty / active contradiction. Never invent names, dates, or confidence.
7. Durable, reusable answers → write to `_Memory/outputs/` (`YYYY-MM-DD-<slug>.md`) + house-style log entry. Simple lookups get no output file.
8. Real knowledge gaps → `meta/open-questions.md`.
