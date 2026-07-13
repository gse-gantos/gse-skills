# Section `.md` Template

The full section file is the complete distillation of the spec section. It is the fallback when the review card is insufficient — used for escalations, substitution evaluations, high-stakes findings, and Full Audit mode. Produced alongside the review card and raw pointer from the same spec reading.

## File path and naming

```
specs-md/full-sections/[section-hyphenated]_[YYYY-MM-DD].md
```

Example: `specs-md/full-sections/22-05-23_2026-05-22.md`

Date in the filename is the issue date of the source document (addendum or project manual). Never overwrite an existing file — if one exists for the same section and date, confirm with the user before proceeding.

## Template

```markdown
# [Section Number] — [Section Title]

**Source:** [filename.pdf], pp. [start]–[end]
**Issue date:** [YYYY-MM-DD]
**Source type:** [Project Manual | Addendum N]
**Date confidence:** [confirmed | date-unconfirmed]
**Review card:** ../review-cards/[section-hyphenated]_CARD.md
**Raw pointer:** ../raw-pointers/[section-hyphenated]_POINTER.md
**Memory applied:** [brief note or None]

## Summary

[Two to four sentences describing what this section covers, what products or systems it governs, and any notable scope limitations.]

## Part 1 — General / Submittals

[Structured extraction of submittal requirements, quality assurance, references, warranties, substitutions, and administrative requirements that affect review. Include paragraph cites. Omit boilerplate that has no effect on submittal review or approval.]

## Part 2 — Products

[Structured extraction of approved manufacturers, materials, ratings, product types, accessories, fabrication requirements, standards references, and finishes. This is the core of the file — pull every measurable, verifiable requirement. Quote numbers and materials verbatim. Cite every paragraph.]

## Part 3 — Execution (submittal-relevant only)

[Include only execution items that affect submittal review, installation coordination, warranties, certifications, closeout, delegated design, or approval decisions. Omit field installation procedure that has no bearing on submittal content.]

## Approval-Critical Requirements

[Expanded version of the review card's Approval-Critical Checks. Include all Critical and Major requirements with spec value, paragraph cite, and applicability conditions. This section is what the reviewer reads when escalating from the card.]

| Check | Requirement | Applies When | Source Paragraph | Severity If Failed |
|---|---|---|---|---|

## Required Submittal Documents

[Expanded version of the review card's document list. Include all submittal items from the Part 1 Submittals paragraph, with condition triggers, phase requirements, and notes on what constitutes adequate submission for each.]

| Document | Required When | Source Paragraph | If Missing | Notes |
|---|---|---|---|---|

## Substitution / Or-Equal Criteria

[Full substitution language from the section. Include approved manufacturers list, basis-of-design language, what documentation a substitution must provide, and any explicit "no substitutions" language. This section is what the reviewer checks on any substitution escalation.]

## Spec Gaps

[Requirements the spec asks for but defines no pass/fail standard for. These are the engineer's gaps — keep separate from approval-critical requirements so the reviewer does not penalize the sub.]

| Topic | Paragraph | Requirement | Gap | Review Treatment |
|---|---|---|---|---|

## Raw Section Pointer

Full text: [filename.pdf], pp. [start]–[end]
Subsections: [list of major subsection headings — e.g., 1.1 Summary | 1.3 Submittals | 2.1 Manufacturers | 2.2 Materials | 2.3 Accessories | 3.1 Installation]
```

## Field guidance

**Header block.** `Source type` is `Addendum N` only when the source is an addendum. `Date confidence` is `date-unconfirmed` when you fell back to today's date because no date was findable. Both `Review card` and `Raw pointer` paths are required — the reviewer needs to be able to navigate between the three artifacts.

**Summary.** Two to four sentences max. Scope, products/systems governed, notable limitations. A reviewer escalating from the card should be able to confirm they're in the right section in ten seconds.

**Part 2 — Products is the core.** For each Part 2 requirement, ask: *could I confirm or refute this from a cut sheet or shop drawing?* If yes, it belongs here with a value, a paragraph cite, and enough context to find it on a submittal. If no (vague, references an unstated standard, depends on field conditions not visible on a submittal), note it as a spec gap or omit it.

**Part 3 — submittal-relevant only.** Execution procedures that have no bearing on what a sub submits should be omitted. Include anything that affects certifications, testing, delegated design, warranties, coordination requirements visible on shop drawings, or closeout documents.

**Approved Manufacturers / Substitution Criteria.** Substitution language is as important as the names. "Subject to compliance with requirements, provide products by one of the following" means alternates are possible. "No substitutions" means they aren't. Copy governing language closely.

**Spec Gaps.** The test: the spec requires a submission but defines no standard to judge it against. Keep these clearly separate from approval-critical requirements so the reviewer doesn't penalize the sub for the engineer's omission.

**Raw Section Pointer.** Points to the raw pointer file and restates the page range and subsection list. This is the navigator back to the source PDF for source-verification escalations.

## Relationship to the review card

The full section contains everything. The review card contains only what a reviewer needs for most submittals. When writing the full section, also write the card — they are produced together from the same spec reading. Don't write one without the other.
