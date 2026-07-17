# Projection Method (decision #7)

## Purpose

Answer "what would full-scope totals look like if this vendor priced
everything?" — **an estimate, never a price.** Projections exist so an
incomplete quote can be sanity-checked against a complete one before real
prices arrive; they are never a substitute for the vendor actually pricing
the line, and they never get treated as if they were a quoted number.

## Method

**Matched-item ratio** — for a vendor with unpriced (blank) lines, compute:

    ratio = <missing vendor>'s comparable ext total / <anchor vendor>'s comparable ext total

computed over whichever lines both the missing vendor and the anchor vendor
actually priced (`Comparable = 1` on that pair, at minimum).

**Choosing the anchor vendor (N > 2):** when more than one other vendor is
priced on the blank line, anchor on the vendor with the most jointly-priced
comparable lines against the missing vendor, group-wide; if tied, use the
left-most vendor column in the Data tab. State which vendor was used as the
anchor in the cell note (§"Always present" below) — this keeps the choice
auditable. (This tie-break was adopted as the default in the skill's final
design review; the original worked examples only ever had two vendors, so it
extends the locked decisions rather than restating one. Override it at the
scoping gate if a job has a better anchor.)

**Compute at GROUP level when the group has enough data, else fall back to
the overall ratio.** Defaults (user may override at the scoping gate):

- **≥3 comparable lines** in the group, OR
- **≥$2,000 comparable ext $** in the group (anchor vendor's side)

Either condition qualifies the group for its own ratio. Below both
thresholds, use the **overall ratio** (computed across all comparable lines
in the whole Data tab for that vendor pair) instead — a 1- or 2-line group
ratio is too thin to trust on its own.

**Apply the ratio** to the anchor vendor's actual extended $ for that specific
blank line:

    Projected <Missing Vendor> Ext $ (line) = <Anchor Vendor> Ext $ (line) * ratio

## Always present as: italic + cell note + sensitivity range

Every projected value, with no exception:

1. **Italic font** — visually distinct from a real quoted number at a glance.
2. **Cell note stating the basis** — which ratio was used (group or overall),
   its numeric value, which vendor was the anchor, and why (e.g., group had
   only 2 comparable lines / $995 comparable ext, below the 3-line/$2k
   default, so the overall ratio was used instead).
3. **A sensitivity range** — the two ends are the group ratio and the overall
   ratio (whichever one wasn't used as primary still bounds the estimate).
   Present as low–high, e.g. "$995–$1,000 (group ratio to overall ratio)."

## No-anchor items: flagged blank, never a number

A specialty/engineered item where the missing vendor has **no comparable
data point anywhere** to build a ratio from (no other line in that vendor's
quote overlaps with anything the anchor vendor priced in a comparable
family) gets **"no basis to project"** — a flagged blank cell, not a
fabricated number. Never force a ratio from an unrelated group onto an item
with nothing to anchor it.

## Projections never blend into real-price trend math

Projected values live in **the projection layer and full-scope estimates
only** — they never enter the real-quoted trend/negotiation math in
`flags_and_metrics.md` or the `Grouping Analysis` tab's Comparable-gated
rollups by pretending to be a real price. Any total that contains even one
projected value must be **labeled as such wherever that total appears** — tab
headers, summary markdown, hit-list entries, everywhere. This is what feeds
the recommend-only-when-clean gate (decision #8): a recommendation can't
appear while any total backing it still contains a projection.

## The self-healing mechanism (once a real price lands)

Once a **real** price replaces a projected value in a vendor's unit-price
cell, the strict `Comparable` flag (see `flags_and_metrics.md` §1) recalculates
to 1 for that line automatically, and the line is pulled into every SUMIFS
rollup, every group premium, every hit-list entry that filters on
`Comparable = 1` — **with no formula edits anywhere in the workbook.** The
projection was never a separate code path; it was always just a value sitting
in the same `<Vendor> Unit $` input cell the real price will eventually
occupy, flagged `Projected? = Yes` until it isn't. That's the whole point of
building the model as formula-driven rather than hardcoded: filling in one
blank cell for real is the only edit required to promote a line from
"projection layer" to "real-price trend."

## Worked micro-example (3 vendors, one with 2 blanks)

Vendors A, B, C. Vendor C left two Valves-group lines unpriced.

**Group: Fittings** (3 comparable lines — qualifies for its own ratio; ≥3
lines default met even though dollar total is modest):

| Line | Qty | A Ext $ | B Ext $ | C Ext $ |
|---|---|---|---|---|
| F1 | 10 | 100.00 | 105.00 | 102.00 |
| F2 | 5 | 100.00 | 95.00 | 105.00 |
| F3 | 8 | 120.00 | 124.00 | 118.40 |
| **Total** | | **320.00** | | **325.40** |

Group ratio (C anchored on A, the left-most jointly-priced vendor) =
325.40 / 320.00 = **1.0169×**. Fittings has no blank C lines in this example,
but this ratio is what would apply if it did.

**Group: Valves** (4 lines; C is blank on 2 of them):

| Line | Qty | A Ext $ | B Ext $ | C Ext $ |
|---|---|---|---|---|
| V1 | 2 | 1,000.00 | 1,040.00 | *blank* |
| V2 | 1 | 300.00 | 310.00 | *blank* |
| V3 | 3 | 600.00 | 615.00 | 585.00 |
| V4 | 5 | 400.00 | 390.00 | 410.00 |

Only V3 and V4 are comparable for the A–C pair: 2 lines, $995.00 comparable
ext — below **both** the 3-line and $2,000 defaults. Valves does **not**
qualify for its own ratio; fall back to the **overall** ratio.

- Group ratio (Valves only, C/A): (585+410) / (600+400) = 995/1000 = **0.9950×**
- Overall ratio (all comparable A–C lines, Fittings + Valves):
  C total = 325.40 + 995.00 = 1,320.40; A total = 320.00 + 1,000.00 = 1,320.00
  → **1.0003×** — this is the one used as primary, since Valves alone didn't
  qualify.

**Projected values for V1 and V2** (anchor = Vendor A, since A was the
left-most vendor jointly priced with C on every comparable line):

| Line | A Ext $ (anchor) | Projected C Ext $ (primary = overall ratio) | Sensitivity range (group ↔ overall) |
|---|---|---|---|
| V1 | 1,000.00 | *1,000.30* | $995.00 – $1,000.30 |
| V2 | 300.00 | *300.09* | $298.50 – $300.09 |

Both cells: italic, `Projected? = Yes`, cell note reads e.g. *"Projected —
Vendor C did not price this line. Basis: overall matched-item ratio C/A =
1.0003× (Valves group has only 2 comparable lines / $995 comparable ext,
below the 3-line/$2k default, so the overall ratio was used instead of a
group-specific one). Sensitivity range $995.00–$1,000.30 (Valves-only ratio
to overall ratio). Anchor vendor: A."*

**No-anchor example:** suppose a fifth line, "Custom SS Spool (Specialty),"
qty 1, only Vendor A priced it ($2,000.00 ext), and no other Specialty-family
line exists anywhere in the Data tab that both A and C (or B and C) priced.
There is nothing to build a C/A or C/B ratio from for that family. Vendor C's
cell for this line gets **"no basis to project"** — a flagged blank, `Projected?
= No basis`, cell note explaining why — never a fabricated dollar figure.
