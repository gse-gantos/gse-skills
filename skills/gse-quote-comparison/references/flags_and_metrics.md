# Flags & Metrics (N-vendor)

Canonical metric definitions for the quote-comparison workbook. Every derived
number described here is an **Excel formula referencing real cells** — never a
hand-computed value typed into a cell. All formulas below are written for an
arbitrary vendor count N; the 2-vendor case (§4) is what they reduce to, not a
separate mode.

## 1. Per-line metrics

**Extended $ per vendor**
For each vendor column pair (`<Vendor> Unit $`, `<Vendor> Ext $`), blank-guarded:

    <Vendor> Ext $ = IF(<Vendor> Unit $ = "", "", Qty * <Vendor> Unit $)

One formula per vendor column, same shape for all N vendors. The blank guard
matters: a blank unit must yield a blank extended — never a `$0` that reads as
a free line and silently understates nothing-was-quoted as cheapest.
(`workbook_spec.md` is the single source of truth for the cell form.)

**Comparable (strict — decision #12)**

    Comparable = IF(COUNTBLANK(<Vendor1 Unit $>:<VendorN Unit $>) = 0, 1, 0)

`Comparable = 1` only when **every** vendor priced the line — not "at least two,"
not "the two vendors I care about." Anything less than all-N-priced is a scope
gap, not a price comparison, and must never enter trend math.

**Why strict, not "any 2":** the moment a group rollup sums Vendor A's and
Vendor B's extended totals over different sets of lines (because a third
vendor's blank silently excluded a line for one comparison but not another),
the rollup is comparing apples to a different orchard. Group subtotals are
only honest when every vendor's subtotal sums over the **same lines**. Anything
looser turns into gap exposure attributed to whichever vendor(s) didn't price
it — that's a `Scope Check` tab concern (see `scope_check.md`), not a price
delta.

**Low bidder (line)** — vendor with the MIN extended $ among vendors who
actually priced the line (this lookup itself doesn't require full-N
comparability; it just needs at least one priced vendor to name a low bidder):

    Low Bidder $ (line) = MINIFS(<Vendor Ext $ range>, <Vendor Ext $ range>, "<>")
    Low Bidder Name     = INDEX(<VendorNameHeaderRange>,
                                 MATCH(Low Bidder $ (line), <Vendor Ext $ range>, 0))

`MINIFS(..., "<>")` excludes blank cells from consideration so an unpriced
vendor is never mistaken for a $0 low bid.

**Premium $ (line)**

    Premium $ = MAXIFS(<Vendor Ext $ range>, <Vendor Ext $ range>, "<>")
              - MINIFS(<Vendor Ext $ range>, <Vendor Ext $ range>, "<>")

**Premium over low bidder % (line)** — see §2 for the full rationale; same
formula shape at line level:

    Premium % (line) = IFERROR(Premium $ / MINIFS(<Vendor Ext $ range>, <Vendor Ext $ range>, "<>"), "")

## 2. Group-level metrics

One rollup block per selected grouping dimension — see `grouping_taxonomy.md`.

Group rollups filter on `Comparable = 1` — never on "priced by the two vendors
in question." This is the strict-comparability rule (§1) applied at rollup
scope: a group's per-vendor subtotal must sum the identical set of lines for
every vendor, or the group premium is meaningless.

**Extended $ per vendor per group**

    <Vendor> Group Ext $ = SUMIFS(<Vendor Ext $ column>,
                                   <GroupTagColumn>, SUBSTITUTE(label,"*","~*"),
                                   Comparable, 1)

(Escape literal `*` in group labels — SUMIFS treats `*` as a wildcard.)

**Low bidder (group)** — vendor with MIN across the N `<Vendor> Group Ext $`
values for that group; same MINIFS/INDEX/MATCH pattern as the line level.

**Premium $ (group) = MAX − MIN**

    Premium $ (group) = MAX(<all N Vendor Group Ext $ cells for this group>)
                       - MIN(<all N Vendor Group Ext $ cells for this group>)

**Premium over low bidder % = (MAX − MIN) / MIN**

    Premium % (group) = Premium $ (group) / MIN(<all N Vendor Group Ext $ cells>)

**This is the metric — use it everywhere a "how far apart" percentage is
needed, line or group.** It explicitly **supersedes the naive two-term form
`(B − A) / A`** (pick an arbitrary vendor as the denominator). Why: it is
normalized to "how far apart are the bids," independent of which vendor
happens to be low — that is what makes the color-coding meaningful across
every group and every cut. `(B−A)/A` changes
meaning depending on which vendor you happened to label A — the same two
prices can read as +40% or −29% depending on labeling, and neither number
means "these two bids are 40%(ish) apart." `(MAX−MIN)/MIN` always means
exactly that, for any N, regardless of vendor order or which one is cheapest
this time.

**% of total spread this group explains**

    % of Total Spread = ABS(Premium $ (group)) / SUM(ABS(<Premium $ for every group in THIS dimension's rollup block>))

Scope the denominator to the **current dimension's block** — material-family
groups sum against material-family groups, functional-class groups sum
against functional-class groups. Don't mix dimensions in one denominator; each
selected dimension (see `grouping_taxonomy.md`) gets its own rollup block and
its own 100%.

**Rank by |Premium $|, not by %.** Dollar magnitude is the ranking key for
hit-lists and "where does the real money sit" — never the percentage alone.

Why: a small per-unit gap on a high-quantity line can dwarf a huge percentage
gap on a one-off. Example — Item X: qty 1,000, Vendor A $10.00/ea, Vendor B
$10.30/ea → only a 3% premium, but $300 total premium. Item Y: qty 1, Vendor A
$50, Vendor B $75 → a 50% premium, screams "outlier," but $25 total. Ranked by
`|Premium $|`, Item X (3%, $300) outranks Item Y (50%, $25) — because it is
the one worth negotiating. Ranking by % alone would put the immaterial
50%-of-$50 item at the top and bury the real signal. (A live worked example
showed the same shape: a small, consistent spread on cheap hardware kits
repeated across sections was worth flagging on dollar-total grounds even
though another family showed bigger % spreads on individual lines.)

## 3. Bands (color-code by magnitude of the gap, never by vendor direction)

Apply native conditional formatting to **Premium over low bidder %**, at
whichever level (line or group) is being displayed:

| Band | Range | Meaning |
|---|---|---|
| 🟩 Green | 0–10% | Competitive — normal quoting noise |
| 🟨 Yellow | 10–20% | Worth a look |
| 🟥 Red | >20% | Negotiation target |

Conditional formatting rules: `cellValue LessThan 0.10` (green),
`cellValue Between 0.10, 0.20` (yellow), `cellValue GreaterThan 0.20` (red).
Keep a visible legend near the top of every tab that uses these bands.

**GAP is a fourth, separate flag — amber — and it is NOT a point on this
percentage scale.** At **line level**, GAP fires whenever `Comparable = 0`
(one or more vendors missing/blank): the line has no honest percentage, shows
amber and a note, and never shows a percentage computed as if a missing price
were $0. At **group level**, GAP fires whenever the group contains **any**
non-comparable line (total line count > comparable line count — the
`workbook_spec.md` GAP-flag formula). A group can legitimately show both: its
premium % is real but computed **over the comparable subset only**, and the
amber GAP flag warns that unpriced lines exist in the group which that
percentage does not reflect. GAP is never folded into the green/yellow/red
scale either way — it is a completeness warning, not a price signal.

**No dollar floor.** There is no minimum-$ gate that suppresses small-dollar
red/yellow flags. The `|Premium $|`-based ranking (§2) already does that job
structurally — a $25 premium on a $50 item may band red at 50%, but it will
rank at the bottom of any hit-list sorted by dollar magnitude, so it never
crowds out material findings. Adding a dollar floor on top would just hide
data the ranking already demotes correctly.

## 4. N=2 reduction

Every formula above is written for arbitrary N and works unmodified at N=2.
Concretely, when there are exactly two vendors A and B:

- `MAX(...) − MIN(...)` reduces to `ABS(B − A)`.
- `MIN(...)` in the denominator reduces to `MIN(A, B)`.
- `Premium % = (MAX−MIN)/MIN` reduces to `ABS(B−A)/MIN(A,B)` — the familiar
  2-vendor form.
- `Comparable = IF(COUNTBLANK(range)=0,1,0)` reduces to
  `IF(AND(UnitA<>"", UnitB<>""), 1, 0)` — the familiar 2-vendor helper.
- Low bidder reduces to a simple two-way IF/comparison.

Treat the 2-vendor forms as the N=2 special case of what's written here, not
as the primary spec with N-vendor as an afterthought. Never write a formula,
column layout, or sentence in this workbook that only works for exactly two
vendors.
