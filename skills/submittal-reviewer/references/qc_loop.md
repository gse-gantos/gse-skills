# Adversarial QC loop

Read at **Phase 2**. The lenses over-produce on purpose — this pass is what makes the final
ranking trustworthy. In **Deep mode** run it as a dedicated QC agent that receives all merged
findings plus access to the same sources. In **Standard mode** the main reviewer does the same
challenge honestly against its own findings. Either way, treat every finding as guilty-until-proven.

---

## Challenge every finding on four axes

1. **Is it real?** Re-open the cited source and confirm the requirement and the deviation both
   exist. Kill it if:
   - the submitted value actually **meets or exceeds** the spec (a min was misread as a max, etc.);
   - the item is **out of scope** for this submittal (belongs to another section/package);
   - a **memory entry or prior RFI/CO already resolved** it;
   - the review-card's **"Usually Do Not Flag"** covers it;
   - it's a restatement of boilerplate, not a checkable requirement.
2. **Is the citation valid?** The evidence must actually establish the requirement. A finding
   citing the wrong paragraph, or "the spec probably requires," is downgraded or cut. No citation
   → cut.
3. **Is severity/confidence calibrated?** Apply `severity_confidence.md`. Downgrade over-flags
   (Minor dressed as Major); upgrade genuine showstoppers. Set confidence by how directly the
   evidence proves a *real* problem — interpretation-dependent findings are Medium at best;
   "possible, needs a human" is Low.
4. **What did the lenses miss?** One deliberate sweep for gaps: a required document no lens
   claimed; a piece that never got routed; an application (e.g. a joint type, a placement class)
   with no corresponding submitted item. Add any real misses as new findings (with citations).

---

## Verifiability discipline

Anything the sources can't settle — drawing sheet pending in coverage, `[inferred]` value, no
governing spec, wiki/memory unavailable, criterion undefined — is moved to
**Unverifiable / needs EOR or RFI** (or **Spec gaps**), *not* left as a pass or a hard fail.
State plainly *why* it can't be verified and what would resolve it.

---

## Convergence

- Run **one** full challenge pass. If it changed nothing material, stop.
- If it killed/added/re-rated several findings, run **one more** pass over just the changed set.
- Stop at 2 passes. Diminishing returns past that; remaining doubt belongs in the confidence
  rating and the Unverifiable section, not in another loop.

---

## Output of QC

A cleaned, de-duplicated finding list where every survivor has: a valid citation, a calibrated
severity and confidence, and a clear action. Hand this to Phase 3 for ranking and the file.
A short QC note (how many findings entered, how many were cut/added/re-rated) helps the reviewer
trust the result — include it in the review file's footer or the REVIEW_LOG line.
