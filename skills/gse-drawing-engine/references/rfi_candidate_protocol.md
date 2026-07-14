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

---

## Register handoff, string completeness, and provenance (added 2026-07-02)

1. **Every drawing-derived RFI candidate must reach the project register.** The
   drawing-db JSON is not a register. After the views render, append/merge the
   candidates into the project's `Registers/rfi_candidates_register.md` (or the
   project's equivalent) with a `Source` column (`drawing-db <set-name>` vs
   `spec`). In one audit, six drawing candidates lived only in the JSON and were never
   tracked. Use a distinct ID scheme `RFI-D01, RFI-D02, ...` so drawing
   candidates can never collide with formal RFI numbers or spec-derived
   candidate IDs (RFI-C##).
2. **No truncated strings.** Write every `evidence`, `description`, and
   `suggested_action` as complete sentences, then re-read the JSON after writing
   and verify no value ends mid-word (see qc_protocol gate 1).
3. **Conflicts quote both sides.** A candidate asserting a conflict must quote
   BOTH conflicting values with their exact locations (sheet + callout, or spec
   section + paragraph), so a reviewer can verify without re-deriving it.
4. **Provenance fields.** Every candidate record carries
   `"ai_draft": true` and `"review_status": "PE review required"`. Views print
   the AI-GENERATED DRAFT banner line (render scripts now do this).
5. **Quantity conflicts between spec-derived and drawing-derived values are
   first-class RFI candidates.** If a schedule total disagrees with a
   spec-derived register quantity (e.g. covers 10 per spec-derived registers vs
   12 per Sheet D-1), that is not merely a data-sync chore — raise it as a
   candidate immediately, then reconcile the registers.
