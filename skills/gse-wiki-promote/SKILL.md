---
name: gse-wiki-promote
description: >
  Promote an explicitly approved artifact from Claude/_Memory/outputs/ into durable wiki knowledge.
  Fork of gsewiki:promote for Job 824 (real staging home is _Memory/outputs/, created 2026-07-10).
  Only on explicit approval — never inferred.
---

# gse-wiki promote (824 fork)

Read `references/house-rules.md` first. Respect `_Memory/AGENTS.md`.

**Approval is a hard gate:** promote only when the human explicitly approves or requests it. Praise ≠ approval. Unclear → ask.

## Workflow

1. Identify the exact artifact in `_Memory/outputs/` (staging home — F3 fix; artifacts are immutable, promotion rewrites INTO `wiki/`).
2. Read `index.md` + relevant `wiki/` pages + applicable `meta/` files. Inspect `_raw/`/mapped sources only for sensitive/disputed/high-value claims.
3. Choose the smallest durable shape: update existing pages / one new page / synthesis + updates / source-summary page.
4. Rewrite report-style content into compact wiki knowledge: house frontmatter, source attribution, `[[wikilinks]]` per the D9 mesh (hub + topic weaving, relevance-gated ~40%), seed-overlay heading for any seed-page touches.
5. Preserve contradictions; never silently resolve.
6. `index.md` + house-style `log.md` entry (`## YYYY-MM-DD — Promotion: Title`); `meta/` updates as needed.
7. Map-update contract: if the promoted artifact synthesized a mapped raw source, update its manifest record + regenerate views.

## Report

Output promoted · pages created/updated · index/log/meta changes · claims needing source review · follow-ups needing approval.
