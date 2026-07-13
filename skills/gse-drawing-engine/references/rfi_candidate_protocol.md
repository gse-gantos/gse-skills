# RFI Candidate Protocol (Phase 2 — the D3 contract)

RFI candidates are the first downstream output this whole database is designed to
feed (PRD D3). They are projected from three sources: coordination issues, open
questions, and unresolved cross-references. Per D5, **Claude writes the judgment
as JSON; the script assembles and projects.** You author two files;
`build_rfi_candidates.py` does the rest.

GC perspective throughout: severity reflects **cost/schedule/safety impact, not
how interesting it is**. Never manufacture an issue — if the set is clean, write
zero issues. Every item must cite evidence (sheet + location). Distinguish a spec
gap (engineer's undefined criteria) from a sub deficiency. Flag safety/code/
contractual concerns briefly (`flag` field), don't elaborate.

## 1. `<set>/machine/coordination_issues.json` (you author)

```json
{
  "schema_version": "1.0",
  "generated": "2026-06-22",
  "issues": [
    {
      "id": "CI-001",
      "title": "Influent invert conflicts between civil plan and process profile",
      "type": "conflict",
      "severity": "high",
      "sheets": ["C-101", "M-401"],
      "disciplines": ["Civil", "Process"],
      "issue": "C-101 shows 24\" influent INV 92.50; M-401 hydraulic profile shows 92.05 at the same point.",
      "evidence": "C-101 callout 'INV 92.50 STA 12+50'; M-401 profile node at headworks inlet '92.05'.",
      "suggested_action": "RFI to engineer to confirm controlling invert before pipe layout.",
      "confidence": "high",
      "flag": null,
      "is_rfi": true,
      "rfi_type": "cross-discipline-conflict"
    }
  ]
}
```

- `type` (coordination taxonomy): `conflict | gap | ambiguity | missing-reference | coordination`.
- `is_rfi` (optional): force-promote (`true`) or hold back (`false`) from the RFI
  list. If omitted, the assembler promotes `conflict`/`gap`/`ambiguity`/
  `missing-reference` and holds back pure `coordination`.
- `rfi_type` (optional): the §5.4 RFI type to use when promoted —
  `drawing-spec-conflict | cross-discipline-conflict | missing-reference |
  ambiguity | gap | field-verification`. **Set it on every `conflict`**, since
  conflict→RFI-type needs your judgment (spec vs. cross-discipline). If omitted,
  the assembler falls back (conflict→cross-discipline-conflict when >1 discipline,
  else gap).
- `flag`: `safety | code | contractual | null`.

## 2. `<set>/machine/open_questions.json` (you author)

```json
{
  "schema_version": "1.0",
  "generated": "2026-06-22",
  "questions": [
    {
      "id": "OQ-001",
      "question": "Is the 24\" influent line ductile iron or PVC? Material not called out on C-101.",
      "category": "rfi-candidate",
      "severity": "medium",
      "sheets": ["C-101"],
      "disciplines": ["Civil"],
      "evidence": "C-101 shows line size/invert but no material callout or spec reference.",
      "confidence": "high",
      "flag": null,
      "rfi_type": "ambiguity"
    }
  ]
}
```

- `category`: `engineering | field-verification | rfi-candidate | spec-drawing-conflict | cross-discipline-conflict | procurement-risk | commissioning-risk`.
- Promotion: by default everything **except** `engineering`, `procurement-risk`,
  and `commissioning-risk` becomes an RFI candidate (override with `is_rfi`). Those
  three are tracked as questions but aren't auto-RFIs.
- `rfi_type` optional override; otherwise mapped from category.

## 3. Unresolved cross-references (automatic)

`build_rfi_candidates.py` turns every unresolved **structural** callout
(`to_sheet: null`, no `external_ref`, `ref_type` in detail/section/continuation/
match_line/key_plan) into a `missing-reference` RFI candidate automatically —
deterministic, no judgment needed. A callout pointing to a sheet not in the set
is a real coordination gap.

## 4. Assemble + project

```
python scripts/build_rfi_candidates.py --set-dir "<set>" --date YYYY-MM-DD
```

Writes the source-of-truth `machine/rfi_candidates.json` (§5.4 records, sorted by
severity, IDs `RFI-001…`) and renders three projections under `views/`:
`rfi_candidates.md`, `coordination_issues.md`, `open_questions.md` — each with the
FS-4 coverage banner. The RFI record carries: `id`, `title`, `type`, `severity`,
`sheets`, `disciplines`, `evidence`, `suggested_action`, `confidence`, `flag`,
`source` (the originating CI/OQ id or `cross_reference`). This is the exact shape
the downstream RFI generator consumes — don't parse raw sheets to build an RFI.
