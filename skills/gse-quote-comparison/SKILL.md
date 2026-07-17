---
name: gse-quote-comparison
description: Compare, level, or analyze two or more priced vendor MATERIAL/EQUIPMENT quotes for the same or overlapping scope — pipe/fittings/valves, misc metals, pumps, and similar supply packages — into an honest apples-to-apples comparison plus an actionable output. Use whenever the user points at 2+ quote files and says "compare these quotes", "level these bids", "who's cheaper", "quote comparison", "split award", "is this quote complete", "normalize these quotes", "which vendor should we buy from", names two vendors with quote files, or wants gaps/substitutions/price spread found across supplier quotes for a common bill of materials. Produces a formula-driven Excel workbook (Data / Scope Check / Grouping Analysis / Hit-List & Award) and a summary markdown that leads with scope coverage, ranks findings by dollar impact, and recommends an award only when the comparison is clean. NOT for subcontractor bid leveling (labor + material, exclusions-heavy sub bids) — the skill detects a sub-bid package and declines it, explaining why, because that is a different checklist (a separate future skill).
---

# GSE Quote Comparison

> **Provenance:** built 2026-07-16 from a quote-comparison design proposal plus a grill-me design review that locked 17 decisions (the decision numbers cited throughout these files refer to that review). Generalized from two real worked comparisons: a shared-BOM pipe-package case (both vendors priced one identical takeoff) and an independent-bids misc-metals case (two vendors bidding different scopes). This is not a fork of an installed skill — it is new, built from that design review.

Turn two or more priced supplier quotes into a comparison a human can act on. GSE is the GC buying the material; the skill's job is to normalize the quotes to a true apples-to-apples basis, show where the money actually is, flag scope and substitution risk, and inform a human decision. It recommends an award only when the comparison is clean — and the final buy decision is always human.

---

## Purpose & posture

**Headline totals lie.** A lower grand total almost always means a *less complete* quote, not a cheaper vendor — a vendor that left lines blank looks cheapest precisely because it bid less scope. The entire value of this skill is refusing to be fooled by that:

- **Normalize to apples-to-apples** — same items, same quantities, same basis, corrections applied — before any total is compared.
- **Find where the money is by grouping** — roll the spread up by material family, functional class, and the other dimensions that matter, ranked by dollar impact, so a real trend is separated from quoting noise.
- **Flag scope and substitution risk** — the decision-changing findings live in missing lines, "or equal" swaps, and quantity mismatches, not in the price delta.
- **Recommend only when clean.** A recommended award appears *only* when there are no open scope gaps, no unconfirmed vendor identities, and no projection-dependent totals. Otherwise the skill explicitly withholds the recommendation and lists exactly what must resolve first. Every claim traces to a cell.

---

## Step 0 — Orient & detect

Run three detections before anything else; they set where inputs come from, how you build, and whether to proceed at all.

**(a) OS detection.** Check whether the job folder runs a GSE project OS: look for `Claude/CLAUDE.md` **and** a `Claude/Map/` directory.
- **Present →** read the boot file (`Claude/CLAUDE.md` → `_Memory/AGENTS.md`) and honor its operating contract (write boundary, never-delete rule, routing schema). Locate the quote files through the Map (`Claude/Map/views/FILE_MAP.md` / `UNPROCESSED.md`, `machine/manifest.json`) rather than guessing folders. Pull vendor history and prior quotes from the job wiki (query via gse-wiki-query). Outputs and filing follow Step 11.
- **Absent →** take the quote file paths directly from the user. Deliver outputs beside the quotes or wherever the user says. Skip Step 11 entirely.
- **Either way the core method (Steps 1–10) is identical.** The OS layer only changes discovery and filing, never the analysis.

**(b) Tool detection.** Decide the build engine before writing formulas — see `references/tooling.md`.
- **Claude for Excel connected →** preferred, for a live formula model verified in Excel's own engine (ideal when more prices are still arriving).
- **Otherwise →** openpyxl via the xlsx skill, with recalc verification; if recalc is blocked, write derived cells as verified static values and say so explicitly.

**(c) Scope-type detection.** Inspect the package. If it is a **subcontractor bid** (labor plus material, exclusions/qualifications letters, a scope-of-work narrative rather than a priced line-item BOM), **decline** — this skill covers material/equipment quotes only. Say so plainly and explain why: sub-bid leveling turns on exclusions, labor scope, and qualifications, which is a different checklist and a separate future skill. Do not force a sub bid through the material-quote method.

---

## Step 1 — Scoping gate

**Inspect the files FIRST, then ask only what you cannot infer.** Read the quotes before asking a single question. From the files themselves infer everything inferable: same-BOM vs. independent bids, vendor identities, natural grouping dimensions, whether prices are still arriving. Then ask the genuinely unresolvable forks — what decision this feeds, how to treat blanks, static vs. live model — in **one batched round**, not a drip of questions. "Just run it" is a valid answer: accept the documented defaults and proceed, noting which defaults you took.

Read `references/scoping_gate.md` before this step — it carries the inference checklist, the fork questions, and the default set.

---

## Steps 2–8 — The method

Each step is short; the reference file is the territory. Do not skip the reference.

**Step 2 — Extract raw line items.** Read the *actual source* quote (Excel/PDF), never a prior summary. Per line capture: quantity, unit price, extended, size, description, the vendor's own category tag if present, and every line note — substitutions and unit-of-measure traps hide in the notes. Capture each quote's date, terms (ex-tax? ex-freight?), and stated vendor identity (often absent from the file — infer and flag, never assume).

**Step 3 — Build the master item list.** Assemble one canonical line list using the **authority cascade: RFQ item list > governing takeoff/BOM > union of all quotes** (decision #15). Use the highest authority available and **state in the output which one you used.** The master item list is the backbone every later tab reads from. See `references/scope_check.md`.

**Step 4 — Align & match.** Map each vendor's lines onto the master list. Deterministic first — shared BOM order, part numbers, or a normalized size+material+type key — then judgment-matching for the rest, recorded in the `Match Confidence` column. Handle bundled-vs-itemized, sub-lines, extra lines, missing lines, and both-blank lines per `references/alignment_rules.md` (matching keys and the confirm-fuzzy protocol also in `references/scope_check.md`). Every below-high-confidence match is surfaced for confirmation, not silently reported.

**Step 5 — Scope-completeness check (before any price analysis).** A comparison is not apples-to-apples until missing and added scope is on the table. Per vendor, against the master list: which items each vendor **missed** and which it **added** that nobody asked for, each priced at the best available competing price (dollars-at-risk), plus a coverage % per vendor. **Confirm every claimed miss with the user BEFORE reporting it** (decision #16/#17) — no false missing-item alarms in the deliverable. This populates the `Scope Check` tab. See `references/scope_check.md`.

**Step 6 — Integrity gate, then flag gaps & data errors.** Integrity gate first: extracted section and grand totals **must tie to each source quote** before any analysis — if they don't, the extraction or alignment is wrong; stop and fix it. Then flag blanks, blank-quantity-with-a-unit-price, per-unit-vs-per-assembly pricing, and the rest of the watch-list in `references/gotcha_library.md`, each fixed in its input cell with a **cell note** citing the correction. Set the strict `Comparable` flag: `Comparable = 1` **only when every vendor priced the line** (decision #12); everything else is gap exposure, reported per missing vendor.

**Step 7 — Deltas, grouping rollups, and projection.** On Comparable lines only, compute the quantity-weighted extended-$ deltas and roll them up by each grouping dimension that applies to this BOM. The lead flag metric is **premium over low bidder %** = (high − low) / low across priced vendors, banded 0–10% green / 10–20% yellow / >20% red, ranked by |premium $|; a GAP is amber and never a price signal. See `references/flags_and_metrics.md` and `references/grouping_taxonomy.md`. Then add the projection layer for blanks — category-level matched ratio where the group has enough comparable data, else the overall ratio, always italic + cell note + sensitivity range, and "no basis to project" for no-anchor specialty items (decision #7). See `references/projection_method.md`.

**Step 8 — Substitution & quantity reconciliation.** Read every line note and product description against the spec and the governing takeoff: catch "or equal" and brand/material/length substitutions, ordered-vs-quoted mismatches, label-vs-product mismatches, and reconcile quoted quantities against the takeoff (a shared-BOM quantity delta is one reconciliation affecting all vendors, not one per vendor). Route spec deviations to the EOR. Watch-list in `references/gotcha_library.md`.

---

## Step 9 — Deliverables

Two artifacts.

**The workbook** — a 4-tab formula-driven model per `references/workbook_spec.md`, N-vendor throughout:
- `Data` — one flat row per master-list item; key columns `Item Key`, `Description`, `Qty`, `Unit`, the grouping/tag columns, per-vendor `<Vendor> Unit $` / `<Vendor> Ext $`, `Comparable`, `Match Confidence`, `Projected?`, `Notes`.
- `Scope Check` — per-vendor misses/adds priced at dollars-at-risk plus coverage %, per `references/scope_check.md`.
- `Grouping Analysis` — one ranked block per dimension (low bidder, premium $, premium over low bidder %, % of spread, count), banded and legended.
- `Hit-List & Award` — the negotiation hit-list, the split-award best case (per-group `MIN` across vendor subtotals, per `references/workbook_spec.md`), and the reconciliation bridge.

Every derived number is an Excel formula referencing real cells — never a hardcoded computation.

**The summary markdown** — scope-coverage verdict FIRST, then normalized (not raw) totals, findings ordered by dollar impact, a trend-vs-noise call per grouping dimension, and either a recommended award or an explicit withhold naming what must resolve first (decision #8).

---

## Step 10 — Verify

Before presenting any conclusion:
- **Totals tie from an independent angle** — every block/tab total reconciles to a source total (section subtotal, vendor's stated grand total) computed a different way.
- **Error-value sweep** — scan for `#REF!`, `#VALUE!`, `#N/A`, `#NAME?` after every formula write.
- **Re-read rendered formats**, not just formula results, before calling formatting done.
- **Recalc verification** — confirm formulas recalculated; if recalc was blocked, disclose that the derived cells are verified-static values.

---

## Step 11 — File & integrate (OS jobs only — MANDATORY when the OS is present)

Skip this entire step when Step 0 found no project OS. When the OS is present, all of the following are mandatory. Keep the routing generic — it ports to any GSE job running the OS by reading that job's schema, not by hardcoding paths:

- **Workbook →** the job's procurement analyses home (the `Claude/Procurement/quotes/analyses/`-style folder per its routing schema). Durable.
- **Summary markdown →** staged to the memory outputs folder (`Claude/_Memory/outputs/`-style) as the wiki-promotion *candidate*. Promotion itself is a separate, explicit approval step via the gse-wiki-promote skill — never promote here.
- **Quote records →** filed to the received-quotes home if the quotes are new to the job.
- **Procurement tracker →** add a row for this comparison.
- **Backlinks →** every output carries the D9 `**Wiki:** [[hub-page]]` backlink.
- **Open-questions →** log unconfirmed vendor identities, unapproved substitutions, and unreconciled quantities.
- **Run log →** record the run in `_Memory/log.md` (house format).
- **Map-update contract →** mark sources processed, register any supersessions, regenerate views per the cartographer contract.

---

## What good looks like

The pipe-package worked example is the bar. Two quotes came in **$5,476 apart on paper** — and that gap was an illusion. The lower quote was lower only because one vendor left 9 Section 3 lines unpriced; once those blanks were projected and the other vendor's data-entry issues corrected, the two totals landed **about $110 apart, under 0.2%** — a coin flip on price. Along the way the method caught what the totals hid: a link-seal priced *per link* at ~$37 that was really ~$367 per assembly (a 10× understatement if taken at face value); one vendor bundling three restraint fittings into an assembly line the other itemized (combine before comparing); and a scope check that found **9 unpriced lines and one dropped instrument** the headline never showed. The deliverable led with scope coverage, ranked the real spread by dollars, and — because scope gaps were still open — **withheld the award recommendation** and listed what to close first. That is a good run: the price delta turned out to be the least important thing on the page.

---

## Reference files

Read the relevant reference before its step — don't work from memory of the spec.

- `references/scoping_gate.md` — inference checklist, batched fork questions, default set. Read before Step 1.
- `references/alignment_rules.md` — bundled/itemized, sub-lines, extra/missing/both-blank handling. Read before Step 4.
- `references/scope_check.md` — authority cascade, matching keys + confirm-fuzzy protocol, dollars-at-risk, coverage %, recommendation gate (the `Scope Check` tab's cell layout lives in `workbook_spec.md`). Read before Steps 3, 4, and 5.
- `references/gotcha_library.md` — the watch-for list and the cell-note convention (grows per job). Read before Steps 6 and 8.
- `references/flags_and_metrics.md` — premium over low bidder %, the 10/20 bands, GAP-amber rule, dollar ranking. Read before Step 7.
- `references/grouping_taxonomy.md` — the adaptive menu of grouping dimensions and example tags (grows per job). Read before Step 7.
- `references/projection_method.md` — category-ratio-with-fallback projection, sensitivity range, no-anchor rule. Read before Step 7's projection layer.
- `references/workbook_spec.md` — the N-vendor 4-tab build spec: formulas, number formats, conditional-formatting bands, reconciliation bridge, legends. Read before Step 9.
- `references/tooling.md` — Claude for Excel vs. openpyxl detection and recalc verification. Read at Step 0(b) and Step 10.
