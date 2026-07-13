# Routing matrix — type → authoritative source

Read at **Phase 0**. For each piece, this table says *what to verify, against which source, and
where that source lives.* The output of this step is the **verification plan** the lenses execute.

To expand the skill to a new submittal type: add a row here, a signal in `type_detection.md`,
and a checklist block in `checklist_library.md §7.3`.

| Type | Verify | Primary authority | Secondary | Common failure modes |
|---|---|---|---|---|
| **Product / material** | Material properties, grade, composition, standards, certifications; all required models/profiles present | Spec **review-card** (§ paragraphs) | Drawings (does the product's application exist on this job?); wiki (prior approvals) | Missing profile/model for an application that exists; property below spec min; wrong certification (potable vs wastewater); or-equal not called out |
| **Shop drawings vs contract drawings** | Bar/member **size, grade, spacing, quantity, development/lap, location, cover**; connection & embed details | **Contract drawings** (sizes/geometry/spacing) via drawing-db | Spec for material & standards (03 20 00 rebar, 05 12 00 steel; ACI/AWS where referenced) | Detailer scaling error; bar size/spacing ≠ design; development/lap short; embed pattern/location off; splice in a disallowed location |
| **Mix design / test report** | f'c for the placement class/location; w/c max; cement type; SCM %; aggregate; slump; air; chlorides; MTR grade/chemistry; test pass/fail | Spec **acceptance criteria** | **Drawings** (which strength class goes where); material spec (mill cert grade) | Mix strength below the location's class; w/c over max; chloride over limit for reinforced; MTR heat doesn't tie to material; test frequency short |
| **Equipment** | Performance vs **scheduled duty point**; motor data; materials of construction; dimensions/weight vs space & anchorage; seismic calcs; O&M/warranty | Spec + **equipment schedule on drawings** | Wiki/PO (what was bought); memory (Owner-preselected?) | Curve misses duty point; motor/electrical mismatch; won't fit / anchorage not shown; seismic calc missing; O&M incomplete |
| **Fallback** | Whatever the governing spec's submittal paragraph requires | Governing spec section (or "no governing spec") | Drawings/wiki as applicable | Required item simply absent; criteria undefined (spec gap) |

## Routing rules

1. **Start at the spec index.** Map each piece to its CSI section via the SPEC_INDEX. If the
   section is in the **Missing Sections Registry**, the authority is "no governing spec" →
   route to drawings/contract, or RFI. Do not fabricate a requirement.
2. **Shop drawings always touch the drawings.** Never close a shop-drawing piece on the spec
   alone — the spec gives material/standards; the *design values* live on the contract drawings.
   Query the drawing-db for every dimensional/geometric check.
3. **Route to the cheapest sufficient layer.** Review-card or drawing view/card is usually
   enough; escalate to full-section / sheet `.txt` / `.png` / crop only when a value is
   uncertain or a decision hinges on it.
4. **Record unverifiable routes.** If the authoritative source is missing (no spec, drawing
   sheet not processed, wiki absent), the piece's checks in that lens are **unverifiable** —
   plan to report them as such, not as passes or fails.
5. **Name the plan.** Before Phase 1, write the plan as one bullet per piece:
   *piece → what to verify → source + location → known gaps.* The lenses execute this plan.

## Worked example — rebar placing drawing (headworks-bypass #525)

> Piece: RW1–RW3 weir structure placing drawing.
> - Bar size / grade / spacing / quantity → **contract structural drawings** for the weir
>   structure (query drawing-db `_sp02-headworks-bypass`), + spec 03 20 00 §2.01 for material.
> - Development / lap-splice lengths → structural **general notes** sheet (drawing-db) / ACI ref.
> - Cover & bar-support locations → drawings + 03 20 00 §3.03 applicability rules.
> - Mill certs present for all heats → 03 20 00 §1.03.B (required-docs lens).
> - Known gap: if the weir-structure sheet is `pending` in coverage → those geometry checks are
>   **unverifiable**; name the sheet and route to the EOR/RFI.
