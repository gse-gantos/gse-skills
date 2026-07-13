# Output format — the review file

Read at **Phase 3**. Produce **one** markdown file. Nothing else (no Bluebeam markups, no
separate Procore/RFI files in v1 — a single ranked issues file is the deliverable).

**Path:** `Claude/Submittals/<subproject>/reviews/<num>-<slug>-review.md`
(e.g. `525-headworks-bypass-rebar-review.md`). Then append one line to the subproject's
`Claude/Submittals/<subproject>/reviews/REVIEW_LOG.md`.

---

## Disposition vocabulary (GC-forward — pick exactly one)

- **Forward to EOR — no GSE-side issues** — clean; nothing for GSE or the sub to fix first.
- **Fix before forwarding** — GSE/sub corrects the package first (missing docs, wrong product).
- **Clarify with sub before forwarding** — sub must state intent or add items before it goes up.
- **Forward with RFI to EOR** — technically forwardable but needs an engineer decision (or-equal,
  spec gap, missing design value).
- **Return to sub — non-compliant** — fundamentally wrong; don't forward.

The disposition follows the worst unresolved item: any open Critical → *Fix before forwarding* or
*Return to sub*; or-equal/spec-gap as the top item → *Forward with RFI*; only Minors → usually
*Forward*.

---

## File template

```markdown
# Submittal Review — <No.> <Title>

**Submittal:** <no.> — <title>
**Subproject:** <_spNN-name>
**Type:** <detected type family>
**Spec section(s):** <e.g. 03 20 00 Concrete Reinforcing>
**Review mode:** <Standard | Deep>
**Sources consulted:** Specs <✓/index found> · Drawings <✓ set / n/a> · Wiki <✓/not available> · Memory <levels/none> · Prior reviews <✓/none>
**Reviewer:** Claude (GSE) · **Date:** <YYYY-MM-DD>

## Recommended GC disposition
**<disposition phrase>.** Blocking: <one line naming the item(s) that set the disposition, or "none">.

## Issues — ranked (severity, then confidence)

### Critical
| # | Issue | Finding | Evidence | Confidence | Action |
|---|---|---|---|---|---|
| 1 | … | … | <spec §/sheet no./wiki/memory> | High/Med/Low | Fix before forwarding / Clarify / RFI to EOR |

### Major
| # | Issue | Finding | Evidence | Confidence | Action |
|---|---|---|---|---|---|

### Minor
| # | Issue | Finding | Evidence | Confidence | Action |
|---|---|---|---|---|---|

## Unverifiable / needs EOR or RFI
| # | Item | Why it can't be verified | What would resolve it | Severity if true |
|---|---|---|---|---|

## Spec gaps (engineer's undefined criteria — not the sub's fault)
| # | Item | The gap | Recommended treatment |
|---|---|---|---|

## Checked — no issue
- <requirement checked and passed, with citation> ✓
- …

## Memory applied
- <entry> — <how it shaped the review (suppressed/added a flag)>

---
*QC: <n entered → n cut / n added / n re-rated>. Layers read: <specs/drawings/wiki>.*
```

Notes:
- Omit a severity subsection if it has no findings (don't print an empty table) — but always keep
  the Unverifiable, Spec gaps, and Checked sections even if short; their emptiness is meaningful.
- Every issue row **must** carry a citation in Evidence. A row without one should have been cut in QC.
- Keep findings in plain construction language — a PM should act on it without decoding jargon.

## REVIEW_LOG line
Append (create the log if absent):
```
| <date> | <no.> | <title> | <mode> | <disposition> | C:<n> M:<n> Mn:<n> Unver:<n> Gaps:<n> | reviews/<file> |
```
