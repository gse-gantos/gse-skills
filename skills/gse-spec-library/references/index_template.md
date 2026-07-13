# `SPEC_INDEX.md` Template

The index is the read-first entry point for `submittal-reviewer`. It answers three questions: which review card does the reviewer load for this section? Which full section `.md` is current? Which raw pointer exists for source verification? Plus three registries that keep the reviewer honest about gaps and supersessions.

When updating (not creating from scratch), read the existing index first and edit in place — regenerating from scratch loses prior rows and registry entries.

## Template

```markdown
# Spec Index

**Project:** [project name]
**Last updated:** [YYYY-MM-DD]

## Section Directory

| Section | Title | Current Review Card | Current Full Section | Raw Pointer | Issue Date | Source | Supersedes |
|---|---|---|---|---|---|---|---|
| 22 05 23 | General-Duty Valves | review-cards/22-05-23_CARD.md | full-sections/22-05-23_2026-05-22.md | raw-pointers/22-05-23_POINTER.md | 2026-05-22 | Addendum 3 | full-sections/22-05-23_2026-03-10.md |
| 22 05 29 | Hangers and Supports | review-cards/22-05-29_CARD.md | full-sections/22-05-29_2026-03-10.md | raw-pointers/22-05-29_POINTER.md | 2026-03-10 | Project Manual | — |

## Missing Sections Registry

Submittal categories that have come up with no corresponding spec section. Lets the reviewer say "no governing spec" honestly.

| Date | Section / Topic | Issue | Notes |
|---|---|---|---|

## Undefined Criteria Registry

Sections that exist but require a submittal item with no measurable acceptance criteria. These are engineer gaps — surfaced so reviews stay fair to the sub.

| Section | Paragraph / Topic | Undefined Requirement | Review Treatment |
|---|---|---|---|

## Addenda / Supersession Notes

| Date | Addendum | Sections Updated | Notes |
|---|---|---|---|
```

## Field guidance

**Current Review Card** — the active `_CARD.md` for this section. `submittal-reviewer` loads this first on every review. Paths are relative to `specs-md/`. When a section is superseded, update this to point to the new card.

**Current Full Section** — the active full section `.md`. Loaded only when the card is insufficient or escalation criteria are met. Paths relative to `specs-md/`.

**Raw Pointer** — the active pointer file. Loaded only for source verification on high-stakes escalations. Paths relative to `specs-md/`.

**Supersedes** — `—` for a section seen only once. When an addendum supersedes a section, set this to the prior full section filename (not the card — cards are replaced in place). Old full section files stay in `specs-md/full-sections/` as archive; never delete them.

**Issue Date** — the date of the current governing version. When an addendum supersedes a section, this date updates to the addendum date.

**Source** — `Project Manual` or `Addendum N`. An addendum row outranks the project-manual row for the same section.

**Missing Sections Registry** — grows over time as submittals arrive for categories the project manual never specced. Seed it during processing if you notice referenced sections with no spec text. `submittal-reviewer` also adds to it when a section comes up mid-review.

**Undefined Criteria Registry** — mirrors the "Spec Gaps" sections of individual files, collected in one place. The reviewer sees every known gap before starting and can flag those items as "Spec gap — no criteria" rather than sub deficiencies.

**Addenda / Supersession Notes** — a running record of every addendum processed and which sections it affected. Lets anyone reconstruct the version history without opening old files.
