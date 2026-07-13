# Type detection rubric

Read at **Phase 0**. Classify the submittal into one type family. The type decides which source
is authoritative (see `routing_matrix.md`). A package can be **mixed** — if so, classify each
piece and route each to its own authority; the package's overall type is the dominant one.

Work top-down; the first family whose signals clearly match wins. When genuinely ambiguous,
pick the family whose authoritative source is the *hardest* to verify (fail safe toward more
checking), and note the ambiguity.

---

## Product / material data
**What it is:** a manufactured product being submitted for approval against a material spec.
**Signals:** manufacturer brochures, product data sheets (PDS), cut sheets, catalog profile
pages, physical-property tables (tensile, elongation, thickness, class), NSF/ANSI or ASTM
citations, "requested for approval" product lists. CSI Div 03/05/09/40/etc. material sections.
**Authority:** spec review-card (primary). Drawings only to confirm *where/whether* the product
is used.
**Examples here:** waterstops (03 01 50), coatings/painting (09 90 00), pipe/valves (40 05 xx).

## Shop drawings vs contract drawings
**What it is:** contractor/fabricator-produced drawings that must match the design drawings.
**Signals:** bar bending schedules, placing/placement drawings, bar marks, dimensioned
fabrication or layout drawings, detailer/fabricator title block, weld/connection details,
embed/anchor-bolt layouts, "shop drawing" in the title.
**Authority:** **contract drawings** for sizes / spacing / geometry / development / location
(query the drawing-db); spec for material grade and standards (e.g. 03 20 00 for rebar material,
05 12 00 for structural steel). *This is the family that cannot be closed on specs alone.*
**Examples here:** cast-in-place rebar / placing drawings, structural steel, embeds.

## Mix designs / test reports
**What it is:** a designed mixture or a test/certification result submitted for acceptance.
**Signals:** concrete mix-design tables, w/c ratio, aggregate gradation, admixture dosages,
trial-batch data; mill test reports (MTRs) with heat numbers; compressive-strength breaks,
lab reports, calibration/certification sheets.
**Authority:** spec acceptance criteria (strength, w/c max, air, chlorides) + **design values on
drawings** (which strength class goes where). Mill certs verify against the material spec grade.

## Equipment packages
**What it is:** a piece of process/mechanical/electrical equipment with performance data.
**Signals:** pump/blower/mixer performance curves, motor & nameplate data, dimensional
drawings, weight, seismic/vibration anchorage calcs, O&M manuals, spare-parts lists,
factory test reports. CSI Div 40/43/46, or an equipment schedule reference.
**Authority:** spec + **scheduled duty point on the drawings** (flow/head/HP) + wiki/PO history
for what was actually bought.
**Note:** on some projects certain equipment is Owner-preselected (check the spec's Div 46 /
procurement sections and AGENTS.md) — if memory/spec says the Owner owns the selection, review
for completeness/coordination, not for product approval.

## Fallback (everything else)
Samples, mock-ups, color/finish selections, welding procedures (WPS/PQR), coordination drawings,
design calculations, certifications (welder quals, NSF listings), closeout/O&M-only submittals.
**Authority:** best-available source named in the governing spec's submittal paragraph; apply the
universal checklist plus whatever type-specific checks the spec spells out. Say explicitly that
the type used the fallback path.

---

## Output of this step
A one-line classification per piece and for the package, e.g.:
> Package type: **Shop drawings vs contract drawings** (rebar placing drawings, 4 structures).
> Pieces: RM1/RM2 manholes, RW1–RW3 weir structure. Material spec 03 20 00; geometry authority =
> contract structural drawings (query drawing-db).
