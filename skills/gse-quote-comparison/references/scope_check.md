# Scope Check (authority cascade, matching, dollars-at-risk, coverage %)

This file owns the **method** for turning raw quotes into an honest scope-completeness
picture: what the master item list is built from, how vendor lines are matched onto it, how
misses and adds are priced, and the gate that withholds a recommendation while scope is open.
The `Scope Check` **tab's cell layout** lives in `workbook_spec.md` (single source of truth
for cells) — this file references it rather than restating it. Everything here works for any
number of vendors (N ≥ 2); never write a rule that only holds for exactly two.

## 1. Authority cascade — what "complete" is measured against

Build the master item list from the highest authority available:

**RFQ item list > governing takeoff / BOM > union of all quotes.**

- **RFQ item list** — GSE's own request defines exactly what was asked for. Highest authority.
- **Governing takeoff / BOM** — a quantity takeoff both vendors priced against. Use when
  there is no RFQ line list.
- **Union of all quotes** — every distinct item any vendor quoted, when neither of the above
  exists. Weakest baseline: it can only find items *some* vendor thought of, never an item
  everybody forgot.

**Always STATE which authority was used and its file provenance (name, date)** in the output
and in the `Scope Check` tab's "Authority used" cell. Why: the master list's completeness is
only as good as its authority, and a reader who doesn't know the baseline can't judge a
"missed" count. If inspection missed an RFQ or takeoff that actually exists, stating the
authority lets the user correct it cheaply.

## 2. Building the master item list

From the chosen authority, create one canonical entry per authorized line — each becomes one
`Data` row. On the union fallback, every distinct item any vendor quoted is one entry. This
list is the backbone every later tab reads from.

## 3. Matching — deterministic tier first

Map each vendor's lines onto the master list. Try the deterministic tiers in order before any
judgment call:

1. **Shared BOM row order** — cleanest when all vendors priced the identical takeoff in the
   same sequence.
2. **Manufacturer part numbers** — exact, when present on both sides.
3. **Normalized `size + material + type` key** — for independent bids. Build the key with this
   **normalization recipe:**
   - **Uppercase** everything; **strip** punctuation and extra whitespace.
   - **Canonicalize sizes/units:** `8"` = `8 IN` = `8-inch` → `8IN`; fractions `½` → `0.5`.
   - **Canonicalize materials:** `DI` = ductile iron; `SS`/`SST`/`316SS` → stainless; `HDPE`;
     `PVC`; etc.
   - **Apply the synonym table:** `ELL` = `elbow` = `bend` = `EL`; `TEE` = `T`;
     `RED` = `reducer`; `MJ` = mechanical joint; `FLG` = `flange` = `FL`.
   - **Assemble the key:** `SIZE + MATERIAL + TYPE (+ class/rating)`.
   The recipe is **extensible per job** — add canonicalizations and synonyms as new material
   families appear (like the gotcha library, it accretes).

## 4. Judgment tier and the Match Confidence column

Whatever the deterministic tiers don't resolve goes to judgment matching. Record every line's
tier in the `Data` `Match Confidence` column: **`exact`** (part number or identical BOM row) /
**`keyed`** (matched on the normalized key) / **`judgment`** (a human-judgment match) /
**`unmatched`** (no counterpart found).

## 5. Confirmation protocol — the core rule

**Every below-high-confidence match AND every claimed missing item is surfaced to the user for
a yes/no BEFORE it is reported as a scope gap.** Batch these into one confirmation round, not a
drip. Why: a false "vendor missed this" in a deliverable is worse than a question — it accuses
a vendor of a gap that may just be a matching miss on our side. `exact` matches don't need
confirmation; `judgment` matches and every claimed miss do.

## 6. Both directions — missed and added

Check scope in both directions against the authority:

- **Items MISSED** — in the master list, absent or unpriced in a vendor's quote.
- **Items ADDED** — quoted by a vendor but not in the authority (nobody asked for it).

`alignment_rules.md` routes extras and misses here; both populate the `Scope Check` tab.

## 7. Dollars-at-risk — pricing the misses

Price each miss at the **best available competing price** — `MIN` across the vendors who did
price it, i.e. the line's `Best Ext $` helper (`workbook_spec.md`). Where **no** vendor priced
it, estimate via the projection method and mark it explicitly — do not leave a blank that
reads as "$0 at risk." See `projection_method.md` for the anchor-vendor rule, the
group-vs-overall ratio choice, the sensitivity range, and the "no basis to project" case; that
file is the single source of truth for projected dollars-at-risk — do not re-derive a ratio
here.

## 8. Coverage % per vendor

Per vendor: **Σ Best Ext $ over the lines that vendor priced ÷ Σ Best Ext $ over all master
lines.** Both numerator and denominator are valued at best-available price, so the ratio
isolates **completeness** from price level — a vendor isn't penalized in coverage for being
expensive, only for leaving scope unpriced. This feeds the `Scope Check` tab (formula in
`workbook_spec.md`).

## 9. The gate — recommendation withheld while scope is open

Any unresolved scope gap ⇒ the award recommendation is withheld (decision #8). The
`Scope Check` tab is where the gap count comes from; the recommendation cell that reads it
lives on `Hit-List & Award` (`workbook_spec.md`), and the GAP semantics are defined in
`flags_and_metrics.md` (GAP is amber, never a price signal). The skill's posture is
recommend-only-when-clean: the deliverable leads with the scope-coverage verdict, and no award
is recommended until misses are confirmed-resolved, vendor identities confirmed, and no total
backing the recommendation still contains a projection.
