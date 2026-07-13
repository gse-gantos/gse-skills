# Raw Pointer Format

The raw pointer is a lightweight source-verification artifact. It records where each section lives in the source PDF, maps its internal structure, and provides search terms for locating content without re-reading the full document. It is built once during `specs-processor` and used by `submittal-reviewer` only when a high-stakes escalation needs to verify exact source language.

The raw pointer does not replace the full section `.md` — it is the navigator back to the source PDF when the full section is also insufficient.

## File path and naming

```
specs-md/raw-pointers/[section-hyphenated]_POINTER.md
```

Example: `specs-md/raw-pointers/22-05-23_POINTER.md`

No date in the filename. One active pointer per section. When a section is superseded by an addendum, the pointer is updated to reflect the new source pages and structure.

## Template

```markdown
# Raw Pointer — [Section Number] [Section Title]

**Source PDF:** [filename.pdf]
**Pages:** [start]–[end]
**Issue date:** [YYYY-MM-DD]
**Source type:** [Project Manual | Addendum N]
**Full section:** ../full-sections/[section-hyphenated]_[YYYY-MM-DD].md
**Review card:** ../review-cards/[section-hyphenated]_CARD.md

## Page / Paragraph Map

| Paragraph | Heading | Source Page | Notes |
|---|---|---|---|
| 1.1 | Summary | [page] | |
| 1.2 | Quality Assurance | [page] | |
| 1.3 | Submittals | [page] | Key submittal list here |
| 1.4 | Warranty | [page] | |
| 2.1 | Manufacturers | [page] | Approved list here |
| 2.2 | Materials | [page] | Core material requirements |
| 2.3 | [heading] | [page] | |
| 3.1 | Installation | [page] | |

Add or remove rows to match the actual section structure. Note the most important paragraphs (submittals list, manufacturers, key material requirements) so a reviewer knows exactly where to go.

## Search Terms

[List specific strings useful for locating requirements in the source PDF. Include spec values (materials, ratings, standards), product names, and key trigger phrases. These are what a text search in Bluebeam or a PDF viewer would use.]

- [e.g., "200 WOG"]
- [e.g., "ASTM B62"]
- [e.g., "gear operator"]
- [e.g., "factory hydrostatic"]
- [e.g., "approved manufacturers"]
- [e.g., "no substitutions" or "or equal"]
```

## Field guidance

**Page / Paragraph Map** — the primary value of this file. A reviewer who needs to verify exact spec language can jump directly to the right paragraph without scanning the whole section. Include every paragraph heading that appears in the section. Add brief notes on paragraphs that contain the most review-critical content.

**Search Terms** — specific strings that appear verbatim in the source PDF. Useful for Bluebeam search or PDF text search when the reviewer needs to confirm exact wording. Include: spec-required values (material designations, ratings, standards), product-category terms, and trigger phrases that control applicability. Do not include generic terms that would return hundreds of hits.

**Keep it light** — the pointer should be quick to write and quick to read. It is a navigation aid, not another full extraction. If a paragraph has nothing review-relevant, a row with no notes is fine.
