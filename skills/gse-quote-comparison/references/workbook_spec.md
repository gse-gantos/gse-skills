# Workbook Spec (N-vendor, 4-tab)

The canonical cell-by-cell build spec for the quote-comparison workbook. A future session
follows this literally, in whichever engine `tooling.md` selects. Every derived number is an
**Excel formula referencing real cells** — never a value typed in after doing the arithmetic
in your head. The worked columns below use a 3-vendor example (Vendor A / Vendor B /
Vendor C); each step states how it generalizes to N vendors. The 2-vendor case is the N=2
reduction, not a separate mode.

## Global rules

- **Never hide rows to declutter — use outline grouping** (`tooling.md` gives the openpyxl
  call). Hidden rows get forgotten and silently drop scope from a reader's view; a collapsed
  outline group is visibly collapsed.
- **A visible legend near the top of every tab that uses conditional formatting** — the band
  meanings (`flags_and_metrics.md`) travel with the tab, not in a reader's memory.
- **Every derived number is a formula.** The only permitted hardcode in the whole workbook is
  a source-quote stated total in the reconciliation bridge (Hit-List & Award), and it carries
  a cited provenance note; the integrity gate checks it.
- **N-vendor throughout.** Formulas are written as contiguous ranges so adding a vendor is
  inserting a column into a block, not rewriting logic.
- **Header on row 1, data from row 2, freeze `A2`** on the Data tab (analysis tabs freeze
  their own header row).
- **Tab order:** `Data`, `Scope Check`, `Grouping Analysis`, `Hit-List & Award`. `Scope Check`
  reads first after `Data` on purpose — a price comparison is not apples-to-apples until the
  scope-completeness picture is on the table.

## Number formats & styling (apply on every tab)

- **Currency** (all `$` cells — Data `Unit $`/`Ext $`/`Best Ext $`, and every `$` cell on the
  analysis tabs): `$#,##0.00;($#,##0.00);-`
- **Percent** (Unit % spread, premium-% columns): `0.0%` — use `0.0%;;"—"` to blank true
  zeros where a 0.0% would read as a false "no spread."
- **Header row:** bold white text on dark navy fill (`FF1F3864`), centered.
- **Freeze panes:** `A2` on Data; header row on each analysis tab.
- **Projected values:** italic font on the projected unit cell + a cell comment stating the
  basis + `Projected? = Yes`. The projection method, ratio choice, sensitivity range, and the
  exact comment wording are owned by `projection_method.md` — do not restate them here.
- **Corrections:** the fix goes in the input cell + a cell comment citing the correction
  (e.g. "vendor quoted per-link $36.75; ×10 links/seal = $367.50 to match BOM basis"). The
  correction protocol is owned by `alignment_rules.md` / `gotcha_library.md`.

---

## Tab 1 — Data

One flat row per master-list item (the master item list is built in `scope_check.md`).
Everything downstream reads from here; nothing downstream re-hardcodes a Data value.

### Column map (3-vendor example)

| Col | Header | Notes |
|-----|--------|-------|
| A | Item Key | normalized key from `scope_check.md` |
| B | Description | |
| C | Qty | |
| D | Unit | unit of measure |
| E | Material Family | grouping dimension 1 (one column per selected dimension) |
| F | Functional Class | grouping dimension 2 |
| G | Vendor A Unit $ | raw input, blank if unquoted — **unit input block starts here** |
| H | Vendor B Unit $ | raw input |
| I | Vendor C Unit $ | raw input — **unit input block ends here** |
| J | Vendor A Ext $ | **ext calc block starts here** |
| K | Vendor B Ext $ | |
| L | Vendor C Ext $ | **ext calc block ends here** |
| M | Comparable | strict flag |
| N | Match Confidence | exact / keyed / judgment / unmatched (text) |
| O | Projected? | Yes / No / No basis |
| P | Unit % spread | helper |
| Q | Best Ext $ | helper — powers dollars-at-risk and coverage % |
| R | Notes | corrections, added-item provenance, etc. |

**Contiguity rule (why the blocks are grouped, not interleaved).** All `<Vendor> Unit $`
columns sit contiguously (the input block), then all `<Vendor> Ext $` columns sit
contiguously (the calc block) — type-major, not vendor-major. Two reasons:
1. It lets `Comparable = COUNT(unit-block range) = N` be a true contiguous-range formula that
   generalizes to any N with no rewrite.
2. It makes the pending-price input cells one contiguous block — the natural "yellow cells"
   region for a live Claude-for-Excel model, where prices drop in and everything reflows.

Per-vendor `Unit $` / `Ext $` naming is preserved so a reader still sees each vendor's pair.

**Generalization to N vendors.** The unit input block occupies the N columns starting at `G`;
the ext calc block occupies the next N columns; then `Comparable`, `Match Confidence`,
`Projected?`, `Unit % spread`, `Best Ext $`, and `Notes` follow in that order. In the
3-vendor example that puts the unit block at `G:I`, the ext block at `J:L`, and `Comparable`
at `M`. For N vendors, replace the literal `3` in the Comparable formula with N and extend
every range across the block.

### Row-2 formulas (fill down)

- **`J2` (Vendor A Ext $):** `=IF(G2="","",$C2*G2)` — `K2` → `H2`, `L2` → `I2`, one per
  vendor, same shape. A blank unit yields a blank extended, never a `$0` that would read as a
  free line.
- **`M2` (Comparable):** `=IF(COUNT($G2:$I2)=3,1,0)` — `COUNT` over the contiguous unit block;
  change the `3` to N for N vendors. `Comparable = 1` only when **every** vendor priced the
  line (decision #12); anything less is gap exposure for `Scope Check`, never a price signal.

  > **Interlock note.** `flags_and_metrics.md` writes Comparable as
  > `IF(COUNTBLANK(unit range)=0,1,0)`. For input columns that hold only numbers or blanks,
  > `COUNTBLANK(range)=0` and `COUNT(range)=N` are **equivalent** — both fire only when no
  > cell is empty. Use the `COUNT($G2:$I2)=3` form here because it is blank-safe **and**
  > text-safe: a stray text entry (`"TBD"`, `"incl"`, `"see note"`) in a unit cell makes
  > `COUNT` fall short of N, so the line correctly reads non-comparable, whereas `COUNTBLANK`
  > counts a text cell as non-blank and would wrongly mark the line comparable.

- **`N2` (Match Confidence):** text, entered during alignment — `exact` / `keyed` /
  `judgment` / `unmatched` (see `scope_check.md`). Not a formula.
- **`O2` (Projected?):** `Yes` / `No` / `No basis` — set by the projection layer
  (`projection_method.md`). Not a formula.
- **`P2` (Unit % spread, helper):** `=IFERROR((MAX($G2:$I2)-MIN($G2:$I2))/MIN($G2:$I2),"")`
  — a per-line spot-check of how far apart the unit prices are; `MIN`/`MAX` ignore blanks.
- **`Q2` (Best Ext $, helper):** `=IF(COUNT($G2:$I2)=0,"",$C2*MIN($G2:$I2))` — the extended
  value of this line at the best (lowest) available unit price across whoever priced it.
  This is the engine for dollars-at-risk and coverage % on `Scope Check`; pricing every line
  at best-available isolates completeness from price level. Blank when nobody priced the line.
- **`R2` (Notes):** free text — corrections, added-item provenance
  ("Added by Vendor B; not in <authority> — confirmed 2026-07-16"), and anything a reader
  must see to trust the row.

**Two permitted helper columns** beyond the literal Data contract: `Unit % spread` (P) and
`Best Ext $` (Q). Both are clearly labeled helpers. `Best Ext $` is the addition beyond the
column contract; it is justified because dollars-at-risk and coverage % both need a
best-available extended value and it must be a live formula, not a re-hardcode.

### Added items

An item a vendor quoted that is **not** in the authority (see `alignment_rules.md`) is
appended as a Data row **after user confirmation**, with `Notes` reading
"Added by <Vendor>; not in <authority> — confirmed <date>". Its `Comparable` is `0` (not
every vendor priced it), so it stays out of trend math and surfaces as an "added" item on
`Scope Check`. Appending it as a real Data row (rather than parking it off-sheet) keeps the
rule intact that every `Scope Check` number references a Data cell.

---

## Tab 2 — Scope Check

`scope_check.md` owns the **method** (authority cascade, matching, confirm-fuzzy protocol,
coverage-% definition, the recommendation gate). This section owns only the **cell layout**.
Every value on this tab is a reference into `Data` — no re-hardcoding.

- **Authority used (top of tab, e.g. `B1`):** a stated cell naming the authority the master
  list was built from (RFQ item list / governing takeoff / union of quotes) and its file
  provenance (name, date). A reader must know the baseline before trusting any "missed"/"added"
  count.
- **Per-vendor block (one per vendor):**
  - **Items MISSED** table — the master rows where that vendor's `Unit $` is blank. Columns
    reference Data cells: Item Key `='Data'!A5`, Description `='Data'!B5`, Qty `='Data'!C5`,
    best-available unit, and dollars-at-risk `='Data'!Q5` (Best Ext $). **Dollars-at-risk
    subtotal** = `SUM` of the referenced `Q` cells. Where no vendor priced a miss (so `Q` is
    blank), price it via `projection_method.md` and mark it explicitly — do not leave a hole.
  - **Items ADDED** table — the appended Data rows flagged not-in-authority for this vendor;
    reference the Data cells; note "not requested — confirm scope."
  - **Coverage %** — Vendor A: `=SUMPRODUCT(--('Data'!$G$2:$G$100<>""),'Data'!$Q$2:$Q$100)/`
    `SUM('Data'!$Q$2:$Q$100)`. Swap the unit column per vendor (`$H` for Vendor B, `$I` for
    Vendor C). Numerator = Σ Best Ext $ over lines this vendor priced; denominator = Σ Best
    Ext $ over all master lines — both at best-available price, so the ratio measures pure
    scope completeness, not price level.

**Build note:** list the actual missed/added rows by explicit reference (e.g. `='Data'!A5`,
`='Data'!A9`, …). Explicit references are robust across engines and avoid a dependence on
dynamic-array spill behavior that not every engine recalculates the same way.

---

## Tab 3 — Grouping Analysis

One ranked block per **selected** grouping dimension (`grouping_taxonomy.md` decides which
dimensions apply). Each block reads its own group-tag column on `Data` (Material Family = `E`,
Functional Class = `F`, and so on). Put the vendor names in a header row for the block —
e.g. row 4: `B4` = "Vendor A", `C4` = "Vendor B", `D4` = "Vendor C". Group label in column A.

### Per group row (example: label in `A5`, Material Family block reading column `E`)

- **Vendor subtotals** — `B5` = `=SUMIFS('Data'!J:J,'Data'!$E:$E,$A5,'Data'!$M:$M,1)`
  (`C5` → column `K`, `D5` → column `L`). The `'Data'!$M:$M,1` criterion restricts the
  subtotal to `Comparable = 1` lines only, so every vendor's subtotal sums the **same** set
  of lines — the only way a group premium means anything.
- **Low bidder** — `=INDEX($B$4:$D$4,MATCH(MIN(B5:D5),B5:D5,0))` (returns the vendor name).
- **Premium $** — `=MAX(B5:D5)-MIN(B5:D5)`.
- **Premium over low bidder %** — `=IF(MIN(B5:D5)=0,"",(MAX(B5:D5)-MIN(B5:D5))/MIN(B5:D5))`.
  This is the banded metric (`flags_and_metrics.md`): 0-10% green / 10-20% yellow / >20% red.
- **% of total spread this group explains** —
  `=IF(SUM(<premium-$ col>$5:<premium-$ col>$N)=0,"",<this row's premium $>/SUM(<premium-$ col>$5:<premium-$ col>$N))`.
  Scope the denominator to **this dimension's block only** — never mix dimensions in one
  denominator (each dimension gets its own 100%).
- **Line count** — `=COUNTIFS('Data'!$E:$E,$A5,'Data'!$M:$M,1)` (comparable lines in the group).
- **GAP flag** —
  `=IF(COUNTIFS('Data'!$E:$E,$A5)>COUNTIFS('Data'!$E:$E,$A5,'Data'!$M:$M,1),"GAP","")` —
  fires when the group holds more lines than are comparable, i.e. some vendor hasn't priced
  part of the group. GAP is amber and is **never** a point on the premium-% scale; it means
  "no honest percentage exists here yet," not "a big/small price gap."

### Rules for the block

- **Include empty / zero-count groups** (SUMIFS returns 0; the `MIN=0` and `SUM=0` guards
  prevent `#DIV/0!`) so the block auto-populates the moment those lines get priced.
- **Escape wildcard characters in group labels** used as SUMIFS/COUNTIFS criteria — a label
  containing `~`, `*`, or `?` must be escaped, `~` first:
  `SUBSTITUTE(SUBSTITUTE(SUBSTITUTE($A5,"~","~~"),"*","~*"),"?","~?")`.
- **Rank rows by `|Premium $|` descending** — dollar magnitude, not percentage (a small % on
  a high-qty line can outweigh a huge % on a $50 one-off). Ranking is presentational; re-sort
  after the values land.
- **Conditional formatting** (native `CellIsRule`) on the premium-% column: `<0.10` green,
  `0.10–0.20` yellow, `>0.20` red. GAP rows get amber via a rule keyed to the GAP-flag column.
  Visible legend at the top of the tab.

---

## Tab 4 — Hit-List & Award

- **Negotiation hit-list** — per vendor, a curated "where <Vendor> is overpriced vs. the low
  bidder" table, ranked by `$` premium, one-line negotiation angle each. Every number is a
  reference into `Grouping Analysis` (e.g. `='Grouping Analysis'!E7`) — never re-hardcoded, so
  the hit-list reflows when a price changes.
- **Split-award best case** — per group, `=MIN('Grouping Analysis'!B5:D5)`; blended split
  total = `SUM` of those group minimums; each single-vendor total = `SUM` of that vendor's
  group column (comparable scope); savings per vendor = single-vendor total − blended split
  total. All formulas.
- **Reconciliation bridge** — as formulas referencing real cells:
  source stated total (the one permitted hardcode — a documented input with cited provenance;
  the integrity gate checks it) → **−** exclusions (Σ ext of non-comparable scope) → **±**
  corrections (Σ correction deltas) → **=** analysis comparable total (which ties to the
  vendor comparable SUMIFS). Show the arithmetic; don't just assert the number.
- **Findings callout** — per dimension, trend vs. noise in plain language, led by the dollar
  figure then the premium %, referencing that dimension's top premium `$` / `%` cells.
- **Recommendation cell** — governed by the recommend-only-when-clean gate (decision #8).
  First build a small gates table: `GapCount`, `VendorUnconfirmed` (Y/N),
  `ProjectionsInTotals` (Y/N). Then:

  ```
  =IF(OR(GapCount>0,VendorUnconfirmed="Y",ProjectionsInTotals="Y"),
     "RECOMMENDATION WITHHELD — resolve: "&TEXTJOIN(", ",TRUE,
        IF(GapCount>0,"open scope gaps",""),
        IF(VendorUnconfirmed="Y","confirm vendor identity",""),
        IF(ProjectionsInTotals="Y","replace projected prices with real quotes","")),
     "Scope clean — see findings for award/negotiation guidance")
  ```

  The recommendation appears **only** when scope is clean; otherwise it names exactly what
  must resolve first. See `scope_check.md` (gap gate) and `projection_method.md`
  (projections-in-totals gate).

  > **Engine note:** when this workbook is authored via openpyxl, `TEXTJOIN` (and any
  > `MINIFS`/`MAXIFS` used at line level) must be written with the `_xlfn.` prefix or Excel
  > shows `#NAME?` — see `tooling.md`'s openpyxl practicals. Verified against a live Excel
  > recalc during the skill's build.

---

## What good looks like

The bar is the pipe-package worked example. Two quotes came in **$5,476 apart on paper**, and
that gap was an illusion — the lower quote was lower only because one vendor left nine lines
unpriced. Once those blanks were projected and the other vendor's data-entry issues were
corrected, the two totals landed **about $110 apart, under 0.2%** — a coin flip on price. The
workbook led with scope coverage, ranked the real spread by dollars, caught a per-link price
that was a 10× understatement at the assembly level, folded one vendor's bundled line to match
the other's itemized lines, and — because scope gaps were still open — withheld the award
recommendation and listed what to close first. Build the workbook so it does the same: the
price delta is usually the least important thing on the page.
