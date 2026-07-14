# Field-Validated Constraints

These are extraction behaviors confirmed by running a full drawing set end-to-end,
not hypotheses. A full 46-sheet set (a plant-rehab project with a mix of
disciplines) was processed to 100% coverage, and the constraints below held
consistently across the set.

Treat them as **defaults on a new set until source validation proves otherwise
for that specific set.** They are phrased in drawing-engine terms: they point at
`machine/*.json`, `source_type`, `crop_region.py`, and `coverage_status.json` —
the actual namespace this skill writes to.

Origin: these findings were validated in the `drawing-library` Beta 1 effort and
merged here so drawing-engine carries the same field knowledge.

---

## L-001 — Bluebeam `save_as_text` returns title block only on vector CAD

**Finding:** On every vector-CAD sheet in the set, `mcp__Bluebeam__save_as_text`
returned the title block only — sheet number, title, date. Body content
(schedules, key notes, equipment tags, dimensions, table rows) was absent.
Visual reading of the rendered PNG captured the full content in every case where
text extraction returned only the title block.

**Impact on drawing-engine:** `bluebeam_text` is a valid `source_type` in
`provenance_contract.md`, but on vector-CAD sheets it is **not a viable primary
source.** Do not classify a vector-CAD sheet from `bluebeam_text` and rate it
`high` — the text you got is the title block, not the sheet.

**Rule:** On vector-CAD sheets, go straight to the rendered PNG (and crops).
Record `source_type: image_visual`. If a sheet was read this way because text
extraction only yielded the title block, note it in the classification `notes`
(e.g. `"L-001: bluebeam/pdf text returned title block only; read visually"`).

**Scope / exception:** Does not apply to scanned/raster sheets, where OCR may
recover body content. Bluebeam `search_and_markup` (string tag-hunting) is a
different operation and remains useful.

---

## L-002 — P&ID balloon interiors do not render

**Finding:** P&ID balloon interiors (the instrument loop identifiers inside the
circles) did not render at any zoom — not in the full-sheet PNG, not in a
`crop_region.py` crop at any DPI. Balloons appear as empty circles.

**Rule:** A P&ID loop tag read from a balloon alone is `confidence: low` and must
be marked for cross-verification. Confirm the tag against, in order:
1. The sheet's own instrument schedule / loop list (summary block)
2. Mechanical plan key notes
3. Conduit-schedule FROM/TO designations
4. Other P&ID sheets in the same zone

Until one of these confirms it, keep the tag's `confidence: low` and raise it as
an open question rather than presenting it as fact.

**Scope:** Confirmed on I-200–I-203; expected on any P&ID from the same CAD export.

---

## L-003 — Equipment schedule sheets govern over plan-view inference

**Finding:** The equipment schedule (E-101) carried zone assignments that
contradicted what plan-view reading suggested. The schedule was correct.

**Rule:** When a dedicated schedule sheet (equipment schedule, valve schedule,
instrument schedule) conflicts with a value inferred from a plan view, **the
schedule governs.** Do not silently overwrite — record both values and the
resolution ("schedule governs over plan-view inference") in the sheet's
classification `notes` and, if it affects a quantity or spec, raise it as an RFI
candidate per `rfi_candidate_protocol.md`.

---

## L-004 — "Illustration only" / "by manufacturer" notes strip quantity authority

**Finding:** A general note on the diffuser plan sheets (M-205–M-208) stated the
layouts were "illustration only" and that the manufacturer sets final diffuser
count, pipe sizes, and lateral arrangement. Counts taken off those sheets are not
valid takeoff or procurement quantities.

**Rule:** Scan every sheet's general notes before treating any count off it as a
quantity. Language like "illustration only," "by manufacturer," "typical,"
"field verify," or "NTS" strips quantity authority for the affected items. When a
count comes off such a sheet, mark it `confidence: low`, note the disclaimer in
the record's `evidence`, and never feed it to a takeoff or RFQ as a confirmed
count. This is directly relevant to the `takeoff-to-rfq` pipeline — a
"by manufacturer" item is an open question, not a line quantity.

---

## L-005 — Control architecture is distributed across disciplines

**Finding:** The control system spanned E-200, E-201, E-202, E-302, I-105, I-107,
and I-200–I-203. No single sheet showed the full architecture; instrument
signals, power sources, and control logic were only visible by correlating across
all of them.

**Rule:** For any set with instrumented/actuated valves, flow meters, DO probes,
PLCs, MCCs, VFDs, or SCADA, build the control map as a dedicated analytical view:
`views/control_system_relationships.md`, mapping instrument → signal path →
controller → power source → actuator for each loop. See
`references/control_system_relationships_protocol.md`. This is an analytical
output built by Claude from the indexed database — not a raw-PDF re-read.

---

## L-006 — The manifest must exist before any sheet record

**Finding:** In the original run, sheets were processed before the manifest
existed, forcing a reconciliation pass afterward — avoidable rework.

**Status in drawing-engine:** **Already enforced architecturally.**
`init_namespace.py` creates `machine/manifest.json` and a `coverage_status.json`
stub before any processing, and the router routes an unfinished run to
BUILD (resume) rather than a fresh rebuild. Keep it that way: never write a
`classification.json`, tag entry, or view before `init_namespace.py` has run for
the set. If you ever hand-bootstrap a set, initialize the manifest all-`pending`
first.

---

## L-007 — Read dense content from a high-DPI crop, not the full-sheet PNG

**Finding:** A full-sheet render was fine for layout and overview, but dense
regions — notes columns, equipment/conduit schedules, FROM/TO fields, instrument
tables — required a much higher effective resolution to read individual labels
reliably. On the original run that meant a 5× crop versus a 3× full sheet.

**Mapping to drawing-engine:** The full-sheet PNG here is capped at
`--max-edge 2000` px (overview resolution) — deliberately low, because detail is
meant to be read via `crop_region.py`. So the finding becomes a hard habit:
**never transcribe a schedule, notes column, or dense table off the full-sheet
PNG.** Crop it. For dense content, render the crop at **`--dpi 360`** (the
validated-equivalent of the 5× read); `crop_region.py`'s 300 default is fine for
a title block but marginal for a packed schedule.

```
python scripts/crop_region.py --set-dir <…/drawing-db/<set>> --sheet E-101 --region right --dpi 360
```

---

## L-008 — Cross-discipline alias pairs must be deduped for counts

**Finding:** Mechanical labeled a motorized butterfly valve `VAL-24.Bxxx`;
electrical/instrumentation labeled the same physical valve `EMV-24.Bxxx`. Counted
naively, the valve appears twice.

**Rule:** When a set uses cross-discipline alias pairs (VAL/EMV, PMP/MTR, etc.),
keep **both** tag strings in `machine/tag_index.json` so a search for either
resolves to the asset — but record the alias relationship (e.g. in each tag's
`notes` or a dedicated `aliases` field) and **dedup before reporting a count.** A
takeoff or valve count must not double-count an aliased asset. Do not merge the
strings; only collapse the count.

---

## L-009 — Technology changes may not be flagged on the drawings

**Finding:** All existing magnetic flow meters were being replaced with thermal
mass flow meters. Nothing on any sheet said "TECHNOLOGY CHANGE" — it was visible
only by comparing demolished-equipment labels on D-series sheets against new
installation details on I-series sheets.

**Rule:** For equipment/instruments being replaced, compare the demolition-sheet
labels (D-series) against the new installation details (I-series/detail sheets)
to detect a technology change. A change of type affects procurement spec,
commissioning, and O&M — call it out explicitly as an RFI/coordination candidate;
do not let it pass silently because no sheet announced it.

---

## L-010 — Higher revision supersedes; do not extract from the superseded sheet

**Finding:** Both Rev 0 and Rev 1 of M-104 were present in the set. Rev 1 governs.

**Rule:** Check the revision block on every sheet. When two revisions of the same
sheet number exist, the higher revision governs for all content; flag the lower
as superseded in `sheet_index.json` (`notes: "superseded by Rev N"`) and do not
extract from it. This is exactly what UPDATE mode
(`incremental_update_protocol.md`) handles for revised/addendum sets — record the
delta in the changelog.

---

## L-011 — "CONDUIT EXISTING" means wire-pull scope, not new conduit

**Finding:** Conduit runs on E-302 labeled "CONDUIT EXISTING" are existing runs;
the scope is to pull new wire through them, not install new conduit.

**Rule:** Classify conduit labeled "CONDUIT EXISTING" / "EXIST. CONDUIT" as
wire-pull scope, not new-conduit installation. Do not include it in new-conduit
procurement quantities. Capture the distinction in the sheet record and, if it
touches a takeoff, note that existing conduit capacity must be verified before
pulling additional circuits.

---

## L-012 — Spare conduit stubs are future infrastructure, not active runs

**Finding:** E-302 showed spare conduit stubs (2" at 12" AFG at the basin)
installed new but with no current wire — future-use infrastructure.

**Rule:** Record spare/stub conduit separately from active runs. It **is** new
conduit for procurement (it gets installed) but it is **not** an active circuit.
Keep the two scopes distinct so counts and circuit lists stay honest.

---

## L-013 — Distinguish modulating vs. discrete actuators

**Finding:** The EMV actuators are ELECTRIC MODULATING (proportional, 4-20mA),
confirmed on the I-105 detail sheet. An earlier open/close assumption was wrong.

**Rule:** For every actuated valve/damper, state the actuator type explicitly —
ELECTRIC MODULATING, ELECTRIC DISCRETE, PNEUMATIC MODULATING, PNEUMATIC DISCRETE,
or MANUAL — and only after confirming it on an instrument detail or control
schematic. These types carry different procurement specs and commissioning/O&M
requirements. Never assume the type; if unconfirmed, mark `confidence: low`.

---

## L-014 — Instrument clearance requirements live in section/detail notes, not P&IDs

**Finding:** Flow-meter straight-run clearances (15D upstream / 5D downstream
general; 9D/5D at specific locations) were in the I-107 detail (M295) and M-202
key notes — not on the P&IDs. The P&IDs showed connectivity, not the physical
constraint.

**Rule:** For instruments with clearance requirements (flow meters, level
sensors, DP transmitters), read the referenced installation detail sheet **and**
the mechanical plan key notes. P&IDs give connectivity; details give physical
constraints. Both are needed before a clearance can be treated as known.

---

## L-015 — PyMuPDF (`fitz`) is the validated render path

**Finding:** PyMuPDF (`fitz.open()` + `page.get_pixmap(matrix=…, alpha=False)`)
produced reliable high-resolution renders across all 46 sheets at both overview
and crop resolution.

**Status in drawing-engine:** Already the standard. `process_drawing.py` renders
full sheets with `fitz` at `--max-edge 2000`; `crop_region.py` renders high-DPI
crops with `fitz`. No change needed — this constraint confirms the existing
render path is the validated one. When adding any new render step, use `fitz`,
not a Bluebeam text/raster export.

---

*Validated: a full 46-sheet plant-rehab set, 2026-06-19 — 46/46 sheets to full
coverage. Merged into drawing-engine from drawing-library Beta 1, 2026-07-13.*
