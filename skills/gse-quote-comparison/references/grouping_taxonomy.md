# Grouping Taxonomy (adaptive menu)

## The menu framing

The dimensions below are a **menu the scoping gate proposes from — not a
mandate to tag every BOM on all six.** Which dimensions actually apply depends
on what's being quoted. Coating type means nothing on a misc-metals package
(no coated items in scope); vendor category code may not exist if a vendor's
quote never carried its own tags. The scoping gate (`scoping_gate.md`) looks
at the actual line items and proposes a subset of this menu for confirmation —
it does not blindly apply all six to every job.

**Rule: tag every line on every dimension that gets SELECTED** for this run —
not on the full menu, only on the confirmed subset. Untagged/inapplicable
dimensions are simply not built as rollup blocks.

**Rule: one rollup block per selected dimension.** Each selected dimension
gets its own ranked block on the `Grouping Analysis` tab (see
`workbook_spec.md`), with its own group tag column on `Data`, its own
per-vendor SUMIFS subtotals, its own low-bidder/premium/%-of-spread columns,
and its own 100% (see `flags_and_metrics.md` §2 on scoping the "% of total
spread" denominator to one dimension's block at a time — don't mix blocks).

## The six seed dimensions

1. **Material family** — HDPE, Ductile Iron, Stainless, Valve,
   Restraint/Hardware, Support, Box/Access, Specialty. *(The lead cut — start
   here on almost every BOM.)*
2. **Functional class** — Pipe / Fitting / Valve / Misc. *(The 4-bucket cut.)*
3. **Commodity vs. specialty** — off-the-shelf bulk items vs.
   engineered/spec'd items. Tests whether a vendor pads commodity pricing
   while matching closely on the engineered, harder-to-shop items (or vice
   versa) — a pattern a flat material-family cut can miss.
4. **Fabricated vs. manufactured** — shop-fabricated spools/supports vs.
   catalog/off-the-shelf parts.
5. **Coating type** — P401 lining, asphaltic, FBE/epoxy, primer, bare HDPE,
   PVC, HDG (hot-dip galvanized), none.
6. **Vendor category code** — the vendors' own tags on their quote lines
   (whatever scheme each vendor uses). Most granular of the six, and it's the
   **audit trail**: it lets you trace a rollup number back to exactly how the
   vendor itself organized the line, independent of how this workbook grouped
   it.

## Candidate additions (awaiting a real use case)

Not yet promoted to the seed menu — these came up in design review as
plausible future cuts but have no BOM yet that needed them. Don't propose
these at the scoping gate unless the job in front of you actually has the
relevant variation (e.g., don't offer "buried vs. above-grade" on a package
with no exposed piping):

- **Buried vs. above-grade** — could matter for coating/wrap or joint-type
  decisions.
- **Lead-time risk** — items with long or uncertain lead times vs. stock
  items; a dimension about risk, not price.
- **Who-supplies-it** — GC-furnished vs. owner-furnished vs. vendor-furnished
  scope boundary, relevant when scope split is itself in question (ties into
  `scope_check.md`'s missing-vs-added-scope logic).

## This menu grows

Like the gotcha library, this list is expected to grow one real job at a
time — not by speculation. When a future run needs a dimension not listed
here (seed or candidate), add it to this file with a short description and
example tags, note which job surfaced the need, and promote it out of
"candidate" status once it's been used for real. Don't invent dimensions
preemptively; wait for a BOM that actually needs the cut.
