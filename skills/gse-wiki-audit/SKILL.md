---
name: gse-wiki-audit
description: >
  Audit the job wiki for health, consistency, sourcing, and mesh quality. Fork of gsewiki:audit
  plus two house-specific checks (ultraplan 3.5): the whole-tree backlink sweep and the map-vs-disk
  consistency check.
---

# gse-wiki audit (GSE fork)

Read `references/house-rules.md` first. Respect `_Memory/AGENTS.md`.

## Scope — upstream checks, house-adjusted

Frontmatter completeness/staleness · index/log coverage · duplicates/overlaps · stale claims · weak sourcing · contradictions/open-questions hygiene · promotion candidates in `_Memory/outputs/` · density ~40% **relevance-gated** (dense AND relevant; over-linking is a finding too). **House difference:** intentional ghost nodes (shared people/entity nodes) are a supported feature, NOT broken links — flag only unintentional phantoms (formal policy pending P5.3). Seed-page audit: project facts outside a `## Project decisions` overlay heading are a finding (harvest separability, 3.3).

## House-specific checks (the fork's additions)

1. **Whole-tree backlink sweep (D9):** every synthesis file under `Claude/` (drawing-db views, specs-md, reviews, extracts, map views) carries a `**Wiki:** [[...]]` backlink that resolves. Report resolved/total — every synthesis file must resolve.
2. **Map-vs-disk consistency:** run `gse-cartographer/scripts/scan.py --diff` — must be clean (0/0/0) or explained. Spot-check that records marked `processed` have `processed_home` paths that exist on disk, and that `SUPERSEDED.md` matches the drawing-db sets' own supersession metadata.
3. **Mount-freshness (F9):** before bash-driven bulk checks, verify a couple of files against direct reads.

## Fixes

Low-risk direct fixes allowed (links, frontmatter, index entries, formatting, open-question/contradiction entries). Ask before: rename/merge/split, resolving contradictions, promoting, structure changes, AGENTS.md edits. **Never delete — retire to `Claude/_archive/`.**

Findings report → `_Memory/outputs/YYYY-MM-DD-audit.md` + house-style log entry.
