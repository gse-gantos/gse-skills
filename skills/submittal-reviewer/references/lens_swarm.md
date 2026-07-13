# Lens swarm — the five verification lenses

Read at **Phase 1**. Each lens is an independent line of attack. In **Deep mode** each runs as a
parallel subagent (Task tool); in **Standard mode** the main reviewer runs all five in sequence.
Every lens pulls its checks from `checklist_library.md` and its severities from
`severity_confidence.md`.

---

## Finding schema (every finding, every lens)

```
- id:          L<lens#>-<n>            e.g. L2-3
- lens:        which lens produced it
- piece:       which decomposed piece / product it concerns
- description: what's wrong, plainly — one or two sentences
- evidence:    submittal location (file/page) + source citation
               (spec §paragraph | sheet no. + detail | wiki page | memory entry)
- severity:    Critical | Major | Minor | Spec Gap
- confidence:  High | Medium | Low   (that it is a REAL issue, not a false positive)
- action:      Fix before forwarding | Clarify with sub | RFI to EOR | Informational
- verifiable:  Yes | No (+ why, if No — e.g. "sheet S-3 pending in coverage")
```

**Hard rule: no citation → not a finding.** If a lens can't point to a source that establishes
the requirement, it either downgrades to an *observation* for QC to judge, or drops it.

---

## The five lenses

### L1 — Materials & standards
**Mandate:** does each product/material meet the spec's stated properties and named standards?
**Checks:** physical minimums verbatim (tensile, elongation, thickness, class, grade); the
referenced standard is the one the spec names (ASTM/AWWA/AISC/AWS/NSF); composition matches
(e.g. bentonite vs polyurethane); certification correct for service (NSF/ANSI 61 for potable
contact — *not* required for wastewater). Source: spec review-card, escalate to full section
for or-equal / borderline calls.

### L2 — Dimensions / config / quantities (vs drawings)
**Mandate:** does the submittal's geometry match the contract drawings?
**Checks:** sizes / spacing / quantities vs drawings & schedules; shop-drawing geometry
reconciles with the contract drawing (catch detailer scaling errors); development/lap lengths;
cover; locations/patterns; splice/coupler locations permitted. Source: drawing-db (see
`retrieval_interfaces.md`). **Honor the confidence ceiling:** an `[inferred]` or
coverage-gap value makes the finding `verifiable: No`, not a hard fail.

### L3 — Required-documents completeness
**Mandate:** did the package include everything the spec/procedures require to be reviewable?
**Checks:** every document listed in the review-card's "Required Submittal Documents" and the
spec's submittal paragraph — shop drawings, mill certs, test reports, physical samples, calcs,
O&M, warranties; required companion products (primers, adhesives, grout). A required item that
is simply absent is a finding even if everything present is fine.

### L4 — Substitutions / or-equal / deviations
**Mandate:** is every product the named/basis-of-design item, or a properly supported or-equal?
**Checks:** products not on the spec's named list flagged as or-equals needing engineer approval;
undisclosed deviations (sub didn't call out a difference from basis-of-design); or-equal
submitted without the supporting data the spec requires. These almost always route
**RFI to EOR** — GSE doesn't approve substitutions.

### L5 — Project context
**Mandate:** is this consistent with what the project already decided and bought?
**Checks:** apply memory rulings (suppress or add flags); item not already resolved by a prior
RFI/CO; scope not superseded by an addendum; product consistent with prior approvals and vendor
history in the wiki; matches what was purchased where PO data is reachable. Source: memory, wiki,
prior reviews/RFIs/COs. When wiki/memory aren't available, run what you can and mark the rest
unverifiable.

---

## Deep mode — subagent contract

Spawn the five lenses in parallel (one Task per lens). Give each subagent:

1. **Its mandate + its checklist slice** (the relevant part of `checklist_library.md`).
2. **The decomposed pieces** (paths to `submittals-md/pieces/`).
3. **The verification plan** (from `routing_matrix.md`) — which sources it must consult and where.
4. **Retrieval instructions** (`retrieval_interfaces.md`) — how to read specs/drawings/wiki/memory.
5. **The finding schema** above and the instruction: *return findings only, each with a citation;
   do not write to the review file; do not fix anything.*

Each subagent returns its findings list. The main reviewer collects all five, assigns global IDs,
and de-duplicates (same issue found by two lenses → merge, keep the strongest evidence and the
higher severity). Then Phase 2 (QC).

**Do not** let a lens agent open the raw submittal PDF page-by-page if a decomposed piece already
has the value — read the piece. Escalate to the raw PDF only to confirm a specific contested value.

---

## Standard mode — sequential

The main reviewer works L1→L5 itself against the pieces and plan, producing the same finding
list. Cheaper; use for small single-product packages. Still run the Phase 2 self-challenge.

---

## Anti-patterns (all lenses)

- Flagging something the review-card's **"Usually Do Not Flag"** list explicitly permits.
- Flagging above-minimum performance (exceeding a spec minimum is compliance, not a defect).
- Asserting a drawing dimension you did not see at or below its confidence ceiling.
- Reporting a spec gap as a sub deficiency.
- Producing a finding with no citation.
