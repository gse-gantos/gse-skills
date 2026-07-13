# Drawing Types — Taxonomy & Classification Guidance

This file is the reference Claude reads when classifying each sheet during the
processing pipeline (Step 5). GSE Construction is a GC on **water/wastewater
(W/WW) infrastructure**, so the taxonomy is optimized for those sets but kept
generic enough for any commercial/industrial drawing package.

**Core principle:** classify from the **content of the sheet**, not from the
filename or your assumptions. The sheet number prefix is a strong hint, but the
title block and what's actually drawn are the truth. When they disagree, trust
the drawing.

---

## 1. Controlled Vocabulary (use these exact values)

Every sheet gets exactly one **`discipline`** from this list. This is a closed
set — do not invent new values, so downstream tools can rely on it.

| `discipline` value | Covers |
|---|---|
| `General` | Cover sheets, sheet index, project info, abbreviations, general notes, legends/symbols, code summaries, vicinity/location maps, survey control |
| `Civil` | Grading, paving, site/yard piping, site utilities, earthwork, erosion control, demolition, roads, drainage, plans & profiles, site layout |
| `Structural` | Concrete, steel, foundations, slabs, walls, rebar, structural details, framing plans, structural notes |
| `Architectural` | Building plans, elevations, sections, roofing, doors/windows, finishes, room layouts (where buildings exist) |
| `Mechanical` | HVAC, plumbing (building), building mechanical systems |
| `Process` | Process piping, equipment, pumps, valves, P&IDs, process flow diagrams, hydraulic profiles, yard process mechanical — the heart of most W/WW jobs |
| `Electrical` | Single-line/one-line diagrams, power plans, panel schedules, lighting, grounding, conduit, duct bank, electrical site plans |
| `Instrumentation` | I&C, loop diagrams, control schematics, PLC/SCADA, network architecture, instrument index, control panel layouts |
| `Landscape` | Planting, irrigation, hardscape (rare on W/WW) |
| `Other` | Anything that genuinely doesn't fit above — use sparingly and explain in notes |

A second field, **`document_type`**, captures what *kind* of document the sheet
is, independent of discipline:

| `document_type` value | Meaning |
|---|---|
| `contract_drawing` | A sheet from the issued-for-construction (or bid) design set |
| `addendum` | A drawing issued via addendum during bidding |
| `as_built` | A record/as-built sheet, or a contract sheet marked up with field changes |
| `shop_drawing` | Contractor/fabricator shop or fabrication drawing |
| `cut_sheet` | Manufacturer equipment cut sheet / product data acting as a drawing |
| `sketch` | An SK / clarification sketch (often attached to an RFI or ASI) |

Default to `contract_drawing` unless the title block, revision cloud, stamp, or
notes clearly indicate otherwise.

---

## 2. Sheet Numbering Conventions (a hint, not a rule)

Most US drawing sets prefix the sheet number with a discipline letter. Common
ones on W/WW work:

| Prefix | Typical discipline |
|---|---|
| `G`, `GN`, `T`, `0`-`series` | General |
| `C`, `CG`, `CU`, `CD` | Civil |
| `S`, `SD` | Structural |
| `A` | Architectural |
| `M`, `H`, `P` | Mechanical / Plumbing (building) |
| `D`, `PR`, `M` (process), `Y` (yard) | Process / Mechanical-process |
| `E` | Electrical |
| `I`, `IC`, `N` | Instrumentation & Controls |
| `L` | Landscape |

**Cautions specific to W/WW:**
- `M` is overloaded — it may mean building HVAC (`Mechanical`) or process
  mechanical/piping (`Process`). Read the sheet: equipment, pipe, valves,
  process flow → `Process`; ductwork, diffusers, building HVAC → `Mechanical`.
- `D` sometimes means "Demolition" (Civil) and sometimes "Detail" or process
  "Drawings." Confirm by content.
- P&IDs and process flow diagrams are almost always `Process`, even when filed
  under an `M` or `I` prefix.
- Some agency/municipal sets use a continuous numbering scheme with no
  discipline letter — rely entirely on content and the title block.

---

## 3. Discipline Notes — what each looks like on the sheet

Use these cues to classify confidently.

**General** — Sheet index/drawing list table; abbreviation & symbol legends;
general notes paragraphs; vicinity map; no scaled technical drawing of work.

**Civil** — Contours/spot elevations; north arrow + site boundary; stationing
and plan-and-profile views; yard piping with slopes and inverts; paving/grading
hatches; erosion control symbols; demolition keynotes.

**Structural** — Rebar callouts (`#5 @ 12" O.C.`); concrete sections; footing
and foundation plans; steel shapes (`W12x26`); structural general notes citing
ACI/AISC; slab and wall reinforcing details.

**Architectural** — Room names/numbers; wall types; door/window schedules;
finish schedules; building elevations and sections.

**Mechanical** — Ductwork; air devices; HVAC equipment schedules; building
plumbing fixtures and risers.

**Process** — Process equipment (pumps, blowers, clarifiers, screens, UV,
chemical feed); process piping with line numbers and sizes; valves and
specialties; **P&IDs** (instrument bubbles + equipment + piping logic);
**process flow diagrams**; hydraulic profiles. This is the dominant discipline
on treatment plant work.

**Electrical** — One-line / single-line diagrams; panelboard and MCC schedules;
power and lighting plans; grounding plans; conduit/cable schedules; duct bank
sections.

**Instrumentation** — Loop diagrams; control/wiring schematics; PLC I/O and
network architecture; instrument index; control panel layouts; ISA-style tag
bubbles dominating the sheet (vs. supporting a P&ID).

> P&ID vs. Instrumentation judgment call: if the sheet shows the **process**
> (equipment + piping with instrument bubbles overlaid), it's `Process`. If it
> shows the **control system itself** (loops, wiring, I/O, networks), it's
> `Instrumentation`.

---

## 4. Special Document Types

These can appear inside a merged PDF and must be flagged via `document_type`:

- **Equipment cut sheets** — manufacturer product data, dimensional drawings,
  performance curves. Often image-heavy, branded, tabular. `cut_sheet`.
- **Manufacturer / shop drawings** — fabrication-level detail, fabricator title
  block, weld/bolt callouts, "FOR APPROVAL" stamps. `shop_drawing`.
- **Addendum drawings** — title block or notes reference an addendum number;
  revision clouds with addendum deltas. `addendum`.
- **As-built / record markups** — "AS-BUILT" / "RECORD DRAWING" stamp,
  handwritten or clouded field changes, redline markups. `as_built`.
- **Sketches (SK/ASI)** — small clarification sketches, often tied to an RFI or
  architect's supplemental instruction. `sketch`.

---

## 5. Handling Ambiguity

- **Multi-discipline sheets** — pick the discipline of the *primary* content for
  `discipline`, and list the secondary disciplines in the classification notes
  (Step 3 schema provides a field for this). Example: a structural plan with
  embedded electrical conduit is `Structural`, note "contains electrical conduit
  routing."
- **Title block vs. drawn content disagree** — trust the drawn content; note the
  discrepancy.
- **Illegible / image-only / scanned sheet** — classify from whatever is
  readable (title block, sheet number) and flag low confidence; the index schema
  carries a confidence field.
- **Truly unclassifiable** — use `Other` and explain why in notes. Never force a
  bad fit.
- **Never pattern-match mechanically.** Do not classify on a single keyword
  ("contains 'electrical' → Electrical"). Read enough of the sheet to be sure.

---

## 6. Confidence

When classifying, assign a confidence level the index schema can store:

- `high` — sheet number prefix, title block, and drawn content all agree.
- `medium` — content is clear but the prefix/title is missing, generic, or
  slightly inconsistent.
- `low` — sheet is illegible, image-only, or genuinely ambiguous; flag for human
  review.
