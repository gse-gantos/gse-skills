# Scoping Gate

Five minutes of scoping decides whether you build a static snapshot or a live negotiation
model — get this wrong and you burn effort on the wrong artifact. This gate
runs as **Step 1**, immediately after Step 0 orientation, and before any workbook exists.

## Rule 1: Inspect every file before asking anything

Open and read **every** quote file in full — not a prior summary, the actual source
(Excel/PDF) — before you ask the user a single scoping question. Most of what the old
manual process asked as questions is answerable by looking:

- **Same-BOM vs. independent bids** — compare line ordering, line counts, and item
  descriptions across the files. Matching order, matching counts, matching descriptions =
  same BOM. Divergent structure = independent bids (see Rule 2b — this is the one fork you
  still may need to ask about).
- **Vendor identity** — check filename, document metadata/author, and letterhead/header
  text first. Neither quote may name its own vendor internally (seen on a real job —
  inferred from filename + editor metadata + the preferred-vendor list). An
  inferred identity is **always flagged for confirmation** in the deliverable, no matter how
  confident the inference — never silently assume a vendor name.
- **Candidate grouping dimensions** — look at what the BOM actually contains (pipe/fittings/
  valves? misc metals? pumps?) and propose the dimensions from `grouping_taxonomy.md` that
  fit this BOM's nature — not the full menu by default.
- **Whether prices are still arriving** — blank/unpriced lines, a vendor's own note ("balance
  to follow"), or the user's framing tells you if this is a final snapshot or a live-in-
  progress set.

Only what you cannot resolve by inspection becomes a question.

## Rule 2: One batched round of fork questions

Ask everything you still need in a **single batched round** — never a back-and-forth
drip. Each fork below has a documented default; state the default when you ask so "yes,
that's fine" is a one-word answer.

**(a) What decision does this feed?**
Straight award / negotiation leverage / split-award / just understand the spread. Sets
depth and which outputs to build.
→ **Default: negotiation + split-award best case.** (Matches the common real case: GSE is
comparing to negotiate and/or divide the buy, not merely rubber-stamping one vendor.)

**(b) Same BOM or independent bids?**
The biggest fork in the whole method — a shared BOM means a true line-by-line **price**
comparison; independent bids mean scope reconciliation comes first, before any price talk
(the independent-bids misc-metals case). **Ask this only if Rule 1's inspection didn't already
resolve it with high confidence** — if line order/counts/descriptions clearly matched or
clearly diverged, state your conclusion instead of asking, and let the user correct you if
wrong.
→ No default (this fork changes the entire deliverable shape — if genuinely ambiguous after
inspection, it must be asked).

**(c) How to handle blanks/gaps?**
Real-price-trends only (analyze items every vendor actually priced) vs. also projecting the
blanks into a full-scope estimate.
→ **Default: trends analysis, plus clearly-flagged projections** (italic + cell note +
sensitivity range, per `projection_method.md`) so both a conservative and a full-scope view
exist without ever blending a projection into real-quote math unlabeled.

**(d) Static snapshot or live template?**
A one-time comparison vs. a workbook built so new prices drop in and everything reflows.
→ **Default: live template if any vendor has prices still outstanding**; static snapshot
only when every vendor's pricing is final. (If Rule 1 already established prices are still
arriving, state this default is in effect rather than asking.)

**(e) Confirm or adjust the proposed groupings.**
Present the grouping dimensions inferred under Rule 1 (from `grouping_taxonomy.md`'s menu)
and ask for a thumbs-up or edits — don't re-derive the taxonomy from scratch with the user
each time.
→ **Default: proposed groupings as inferred**, confirmed or adjusted in the same batched
round.

**(f) Confirm scope authority.**
Is there an RFQ document defining the required item list? A governing takeoff/BOM? If
neither, the master item list falls back to the union of all quotes (the authority
cascade: RFQ > governing takeoff > union of quotes). Ask which authority document exists
and where — this decides what "missing" and "added" mean in Scope Check.
→ **Default: authority cascade applied automatically** — RFQ if found, else takeoff/BOM if
found, else union of quotes, stated explicitly in the deliverable so the user can correct
if a document exists that inspection missed.

## Rule 3: "Just run it" — the defaults table

If the user says "just run it" / gives no scoping answers, apply every default below and
state clearly in the deliverable that defaults were used (so a wrong default is cheap to
catch and correct later):

| Fork | Default applied |
|---|---|
| (a) Decision fed | Negotiation + split-award best case |
| (b) Same BOM vs. independent | Whatever Rule 1 inspection concluded, flagged as inferred |
| (c) Blanks handling | Real-price trends + clearly-flagged projections |
| (d) Snapshot vs. live | Live template if any prices outstanding, else static |
| (e) Groupings | Dimensions inferred from the BOM's nature (grouping_taxonomy.md menu) |
| (f) Scope authority | Authority cascade: RFQ > governing takeoff > union of quotes |
| Vendor identity | Best inference from filename/metadata/letterhead, always flagged |

None of these defaults suppress a flag — "just run it" changes what gets assumed, never
what gets disclosed.
