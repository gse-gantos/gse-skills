# Alignment Rules

Once the master item list exists (authority cascade — see `scope_check.md`) and lines are
matched across vendors — 1:1 by **source line order** when all vendors priced a shared BOM
(cleanest case), or by a **normalized key** when bids are independent (key construction,
fuzzy-match tiers, and the Match Confidence column are `scope_check.md`'s job, not this
file's) — this file owns what happens **after** a line is matched: how to reconcile what
each vendor actually wrote against a common row in the Data tab.

This applies across **any number of vendors** (N ≥ 2). Never write a rule, a formula, or a
sentence here that only works for exactly two.

## The correction protocol (apply to every rule below)

Every fix made under these rules is made **in the input cell**, with a cell note. The
protocol:

> Document it (what's wrong, what the fix is, why). Fix it in the input cell with a cell
> note citing the correction (e.g., "vendor quoted per-unit-of-10, converted to per-each
> ×10").

Never silently normalize. A reader opening the workbook cold must be able to hover any
corrected cell and see what was wrong, what you changed it to, and why — without asking you.

## Bundled vs. itemized

One vendor rolls sub-parts into a single parent line; another itemizes the same scope as
separate lines. **Compare the combined assembly total, never double-count** a sub-part
against both the vendor who bundled it and the vendor who broke it out.

**Worked example (megalug / MJ-tee):** Vendor A prices one line — "6" MJ Tee w/ 3 megalugs"
— as a single extended price. Vendor B prices the MJ tee and each of the three megalugs as
four separate line items. To align: sum Vendor B's four lines into one combined figure
before comparing to Vendor A's single bundled price. Put a cell note on Vendor B's rolled-up
comparison cell: "Combined MJ tee + 3× megalug lines to match Vendor A's bundled line;
see rows [x–x] for itemized source."

## Sub-lines

A loose companion part (e.g., a flange quoted separately from the fitting it mates to) that
belongs conceptually with a matched line but wasn't priced as part of it. Treat like bundled
vs. itemized — fold the sub-line into the parent comparison with a cell note identifying
which row it was pulled from, rather than letting it float as an unmatched extra.

## Extra lines

An item **only one vendor quoted**, with no corresponding scope in the others (not a
sub-line of an existing match — genuinely additional scope). Do not silently drop or bury
it in the Data tab. **Send it to `Scope Check` as an "added" item** for that vendor, priced
at its own quoted extended value, so it surfaces as scope the others may be missing (or
scope nobody asked for) rather than distorting the price-trend math.

## Missing lines

A row present in the master item list that one or more vendors simply never quoted (absent,
not blank-priced). **Send it to `Scope Check` as a miss** for each vendor that lacks it,
priced at the best available competing price (dollars-at-risk) per decision #17 — do not
leave it silently out of both the Data tab and the deliverable.

## Both-blank lines

A line every vendor left unpriced. `Comparable = 0` for this row by definition (decision
#12 — strict, all-vendors-priced-or-not-comparable). It is gap exposure for everyone, not a
price signal for anyone. Keep the row in Data (don't delete it) so it's visible and ready to
populate the moment any vendor prices it.

## Per-unit vs. per-assembly basis

A vendor prices by sub-unit (e.g., "per link," "per foot," "per 10-pack") while the shared
BOM calls for the assembled unit. Left uncorrected, this silently understates that vendor by
the basis-conversion factor.

**Worked example (link seal):** A vendor's note says its $36.75 price is **per link**, and
10 links make one assembled seal — the true per-assembly price is $367.50, a 10×
understatement if taken at face value. Fix it in the input cell (replace $36.75 with
$367.50) and attach a cell note: "Vendor quoted per-link ($36.75); 10 links/seal per
vendor's own note; corrected to per-assembly ($367.50 = $36.75 × 10) to match BOM basis."

## Where this hands off

- Match mechanics (keys, fuzzy tiers, Match Confidence column) → `scope_check.md`.
- Extras and misses, once routed here, are priced and tallied on the `Scope Check` tab
  (coverage %, dollars-at-risk) → `scope_check.md`.
- Comparable flag mechanics and the Data-tab formula → `flags_and_metrics.md`.
- Projected-value flagging for blanks the user chooses to estimate → `projection_method.md`.
