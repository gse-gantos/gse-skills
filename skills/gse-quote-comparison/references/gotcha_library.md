# Gotcha Library

The reusable "watch for these" list — seeded from two real worked comparisons (an
independent-bids misc-metals case and a shared-BOM pipe-package case; see SKILL.md's
provenance note), generalized to any number of vendors. Every entry below cost real time to
catch once; the point of this file is that it never costs that time again, on any job.

**This library grows.** When a new gotcha is caught on any job, **append it here** — this
skill lives in a shared repo (`gse-skills`), so a gotcha caught once protects every future
quote comparison across every GSE job, not just the one where it was found. Add the entry
in the same format as the ten below: name, what to watch for, what to do about it.

## The ten seed gotchas

1. **Vendor name absent from the file.** A quote frequently doesn't name its own vendor
   internally. Infer identity from filename, document metadata, and letterhead — but
   **always flag it for confirmation**, never assume it's settled just because the inference
   feels obvious. (Seen on a real job: neither vendor's spreadsheet named itself internally;
   both were inferred and flagged as an open item.)

2. **Bundled vs. itemized.** One vendor rolls sub-parts into a single line; another itemizes
   the same scope across several lines. Combine before comparing — never double-count a
   sub-part against both representations. (See `alignment_rules.md` for the megalug/MJ-tee
   worked example.)

3. **Per-unit vs. per-assembly pricing.** A vendor's unit price is quoted against a
   sub-unit-of-measure (per link, per foot, per 10-pack) that doesn't match the BOM's
   assembled unit. Read the unit-of-measure note on every line before trusting a unit price
   at face value. (Seen on a real job: a link seal priced per link at 1/10 the true assembly
   price — a 10× understatement if unread.)

4. **Blank quantity with a populated unit price.** A line has a real unit price but a blank
   quantity field, so its extended price silently computes to $0 — understating that
   vendor's total without any visible error. Always check for this pattern specifically; it
   does not throw a formula error, so nothing draws your eye to it.

5. **Missing instrumentation.** An instrumentation item (flow meter, gauge, sensor) dropped
   entirely from one or more quotes. Usually because it's owner- or GC-furnished and outside
   the vendor's scope — but **confirm this explicitly rather than assuming it**, so it
   doesn't fall through the cracks between the material PO and the instrumentation package.

6. **"Or equal" substitutions.** A vendor quotes a different product than the one specified,
   under an "or equal" clause — a plain unit swapped in for a specialty one (a flapper check
   valve against a spec'd surge check), a brand swap, or a material swap. These are
   engineering judgment calls, not pricing questions — **route every one to the EOR**, don't
   resolve them yourself.

7. **Length/joint substitutions.** A vendor quotes a different stick length or joint type
   than specified (e.g., 18' TJ pipe against a 20' spec'd length). Minor on its face, but
   still a scope deviation that needs explicit confirmation, not a silent pass-through.

8. **Extra or missing scope.** An item appears in one vendor's quote and not another's, with
   no clear correspondence — goes to Scope Check as an "added" item for the vendor that
   quoted it, or a "missed" item for the vendor(s) that didn't (see `alignment_rules.md` and
   `scope_check.md`).

9. **Label vs. product mismatch.** A line is labeled as one material or spec (e.g.,
   "stainless," SS2) but the quoted product is actually another (e.g., ductile iron,
   C110/P401 lined). This is a spec compliance question, not merely a grouping/tagging
   choice — flag it for EOR review, don't just tag it under whichever material the label
   says.

10. **Takeoff quantity deltas apply to ALL quotes sharing a BOM.** When multiple vendors
    priced against the same governing takeoff and a quantity turns out to be off (more or
    less footage, more or fewer fittings than the locked takeoff calls for), that discrepancy
    applies identically to every vendor who priced against that BOM. **Reconcile it once**,
    against the takeoff, not separately per vendor — treating it as vendor-specific wastes
    effort and risks a mismatched correction across vendors.

## The correction convention (applies to any gotcha above)

Every correction made because of one of these gotchas follows the skill's correction
protocol (also stated in `alignment_rules.md`):

> Document it (what's wrong, what the fix is, why). Fix it in the input cell with a cell
> note citing the correction (e.g., "vendor quoted per-unit-of-10, converted to per-each
> ×10").

Fix in the input cell. Note what was wrong, what the fix is, and why. Never fix silently.

## Growing this library

New gotcha discovered on a live job? Append a new numbered entry above, in the same
three-part shape (name — what to watch for — what to do). Note the job/example it came from
if useful, but write the entry itself in generalized, N-vendor language so it's immediately
reusable elsewhere. This file has no maximum length — it is meant to accrete.
