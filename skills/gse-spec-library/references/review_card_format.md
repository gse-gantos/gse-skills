# Review Card Format

The review card is the primary lookup for `submittal-reviewer` on most submittals. The reviewer reads it first and only opens the full section when the card is insufficient. It is produced alongside the full section `.md` and raw pointer for every processed spec section.

**Goal:** Short, structured, optimized for repeated use. One to two pages. Include only what a reviewer needs to check most submittals. Omit Part 1 boilerplate, redundant language, and anything that doesn't affect approval decisions.

## File path and naming

```
specs-md/review-cards/[section-hyphenated]_CARD.md
```

Example: `specs-md/review-cards/22-05-23_CARD.md`

No date in the filename. There is one active card per section. When a section is superseded by an addendum, the card is replaced (after confirming with the user) and the old card is archived. The `SPEC_INDEX.md` always points to the current card.

## Template

```markdown
# Review Card — [Section Number] [Section Title]

**Source full section:** ../full-sections/[section-hyphenated]_[YYYY-MM-DD].md
**Raw pointer:** ../raw-pointers/[section-hyphenated]_POINTER.md
**Issue date:** [YYYY-MM-DD]
**Source:** [Project Manual | Addendum N]
**Memory applied:** [brief note or None]

## Use This Card For

[List the product categories, systems, or submittal types this section governs. One to three lines. Lets the reviewer confirm this card applies before reading further.]

## Do Not Use This Card For

[List common adjacent categories or similar products likely governed by different sections. Prevents misrouting a submittal to the wrong card.]

## Approval-Critical Checks

| Check | Requirement | Applies When | Source Paragraph | Severity If Failed | Why It Matters |
|---|---|---|---|---|---|

Include only requirements that are measurable, verifiable from a cut sheet or shop drawing, and meaningful for approval decisions. Critical and Major items only. Minor and Informational items belong in the full section.

## Required Submittal Documents

| Document | Required When | Source Paragraph | If Missing | Notes |
|---|---|---|---|---|

Copy directly from the Part 1 Submittals paragraph. Note any size, type, phase, or condition triggers. Do not include closeout documents as missing on first submittals.

## Applicability Rules

| Rule | Applies To | Does Not Apply To | Source |
|---|---|---|---|

Capture every explicit trigger: size thresholds, service conditions, product types, system types, locations, voltage, rating class, material category, installation condition, project phase. These are what the applicability gate checks — missing a trigger here causes the reviewer to over-flag.

## Substitution / Or-Equal Criteria

[List approved manufacturers, basis-of-design language, substitution requirements, and or-equal criteria. Copy the governing language closely — it controls whether a sub can offer an alternate. If no substitutions are permitted, say so explicitly.]

## Usually Do Not Flag

[List patterns that look like issues but are not material. Specific beats general. These directly reduce unnecessary flags.]

Examples of what to include (replace with section-specific patterns):
- Above-minimum ratings unless they create coordination, compatibility, warranty, cost approval, or approval-status issues.
- Different product-data formatting if required values are present.
- Catalog naming differences where model, material, rating, size, and configuration match.
- Boilerplate requirements that do not apply to the submitted item's type, size, or service condition.

## Spec Gaps

| Topic | Requirement | Gap | Review Treatment |
|---|---|---|---|

Use `Spec gap — no criteria` when the spec requires a submission but gives no measurable acceptance criteria. These are N/A by design — do not penalize the sub.

## Escalate To Full Section When

Escalate from this card to `../full-sections/[section-hyphenated]_[YYYY-MM-DD].md` when:
- considering `Reject / Revise and Resubmit` or `Revise and Resubmit`,
- product appears to be a substitution or or-equal,
- requirement applicability is unclear after checking this card,
- current submittal conflicts with a prior approved revision,
- issue involves code, warranty, pressure rating, fire rating, structural capacity, life safety, waterproofing, electrical rating, accessibility, or delegated design,
- user requests Full Audit mode,
- or this card lacks information needed to resolve an ambiguity.
```

## Field guidance

**Use This Card For / Do Not Use This Card For** — these two fields prevent misrouting. If a reviewer is looking at a butterfly valve and the card says "gate, globe, ball valves only," they know to look elsewhere before running a full review against the wrong section.

**Approval-Critical Checks** — Critical and Major items only. Include the spec value, the paragraph cite, the trigger condition, and the severity so the reviewer knows what a mismatch means. Do not include Minor or Informational items here.

**Applicability Rules** — every explicit size limit, service condition, system type, or trigger phrase that controls whether a requirement applies. Pull from the spec verbatim. Missing a trigger here means the reviewer will over-flag inapplicable requirements.

**Usually Do Not Flag** — the most valuable section for reducing noise. Think about what reviewers historically over-flag for this section type and call those patterns out explicitly. "Pressure rating above the minimum is Compliant" is more useful than "better-than-spec is OK."

**Spec Gaps** — mirror the Spec Gaps section from the full `.md`. Short and specific.

**Escalate To Full Section When** — the card should always tell the reviewer exactly when to go deeper. Customize the list if this section has specific escalation triggers beyond the defaults.

## Keeping the card short

The card fails its purpose if it grows to match the full section. When in doubt, cut:
- Don't include Part 1 administrative requirements unless they produce a reviewable submittal item.
- Don't copy boilerplate language that doesn't affect approval.
- Don't list every Part 2 material requirement — only the ones that commonly appear on submittals and have a pass/fail value.
- If a requirement applies only to unusual configurations, put it in the full section, not the card.
