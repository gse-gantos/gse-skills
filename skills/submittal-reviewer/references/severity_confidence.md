# Severity, confidence & ranking

Read at **Phase 3** (and referenced by QC in Phase 2). Two independent axes. Severity = how much
it matters. Confidence = how sure we are it's a *real* issue (not a false positive). They never
collapse into one number — the file groups by severity, then sorts by confidence within the group.

---

## Severity (from the GC-forward view)

| Severity | Meaning | Typical action |
|---|---|---|
| **Critical** | Would be rejected by the EOR, **or** produces non-conforming / unsafe / out-of-code work if built as submitted, **or** the wrong product entirely. | Must resolve before forwarding |
| **Major** | A real spec/drawing deviation, or a missing required document the EOR will bounce. | Sub action or engineer decision before approval |
| **Minor** | Administrative or low-impact; doesn't threaten conformance. | Note it; fix in resubmittal; generally still forward |
| **Spec Gap** | The engineer defined no measurable criterion. **Not the sub's fault.** | Route to EOR; do not penalize the sub |

Bar confirmed with GSE: *Critical = the EOR would reject it / it yields non-conforming work.*

## Confidence (that it's a real issue)

| Confidence | Meaning |
|---|---|
| **High** | Directly evidenced by a spec/drawing citation + the submittal content; unambiguous. |
| **Medium** | Strong indication but depends on interpretation or an unstated assumption (e.g. intended use not declared). |
| **Low** | Possible issue flagged for human eyes; plausibly a false positive. |

Confidence is about the *existence* of the problem, not its size. A certainly-present typo is
High confidence / Minor severity. A probably-short development length you couldn't fully confirm
on a partially-covered sheet is Medium/Low confidence even though it'd be Critical if true.

## Ranking rule (the output order)

1. Group by severity: **Critical → Major → Minor**.
2. Within each group, sort by **confidence: High → Low**.
3. **Unverifiable** items and **Spec gaps** are *not* force-ranked with checkable findings — they
   get their own sections so a "we couldn't check this" never masquerades as a graded defect.

*Why severity-first (per GSE's call): a Critical must never be buried beneath a high-confidence
Minor. Grouping by severity guarantees the showstoppers are read first; confidence ordering
inside the group tells the reviewer which to trust most.*

## Calibration examples
- Submitted rebar Grade 40 where drawings/spec require Grade 60 → **Critical / High**.
- Required non-moving-joint waterstop profile absent from the approval request → **Major / High**.
- Or-equal coupler with test data, not on the named list → **Major / Medium**, action RFI to EOR.
- Data sheet to 1/8" where spec says "nearest inch" → **Minor / High** (or Do-Not-Flag if the
  card permits it).
- Development length possibly short but the governing sheet is pending in coverage →
  **Unverifiable** (name the sheet), not a graded finding.
- Spec requires a post-installation test it never defines → **Spec Gap**, route to EOR.
