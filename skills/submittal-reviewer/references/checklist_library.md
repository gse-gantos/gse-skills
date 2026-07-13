# Checklist library — everything the lenses look for

Read at **Phase 1**. This is the tuned knowledge. Organized as **universal** (every submittal) +
**by lens** + **by type family**. It's a starting baseline — extend it as GSE learns what tends
to bite. Each lens pulls the slices relevant to it.

The governing spec/drawing always wins over this list. Where the spec's review-card is more
specific (its Approval-Critical Checks, Required Documents, Applicability Rules), follow the card
— this library is the backstop for what the card doesn't spell out and for cross-source checks.

---

## 7.1 Universal — check on every submittal
- Claimed spec section matches the actual content (a mislabeled section is a finding).
- Transmittal complete: submittal number, spec section, revision, date, sub/vendor.
- **GC's own review present** — GSE must review before forwarding; an un-reviewed/un-stamped
  package going up is itself a flag. *Why: forwarding an unreviewed submittal puts GSE's name on
  the sub's errors and invites an EOR rejection GSE could have caught.*
- Deviations disclosed by the sub? Anything off the basis-of-design called out in writing?
- Current revision — not superseded by an addendum or a prior approval.
- Pages legible and complete (scan/OCR quality; no dropped pages).
- Applies to *this* project's scope (not boilerplate carried from another job).
- Not already reviewed/approved. If it's a resubmittal, review only the deltas against the prior
  review and confirm prior comments were addressed.

## 7.2 By lens

**L1 Materials & standards**
- Every physical property meets the spec minimum **verbatim** (tensile, elongation, thickness,
  class, grade). *Why: "close" isn't compliant; the EOR checks the number.*
- Referenced standard is the exact one the spec names (ASTM/AWWA/AISC/AWS edition where stated).
- NSF/ANSI 61 required where the product contacts **potable** water; not required for wastewater
  — don't flag its absence on a wastewater item.
- Composition matches (e.g. a bentonite hydrophilic waterstop is not interchangeable with a
  polyurethane sealant, even if both "swell").

**L2 Dimensions/config vs drawings**
- Sizes / quantities / spacing match the drawings and schedules.
- Shop-drawing geometry reconciles with the contract drawing (detailer scaling/typo errors).
- Locations / patterns match; the submitted item goes where the drawing shows it.
- Anything resting on an `[inferred]` or uncovered drawing value → mark unverifiable, don't assert.

**L3 Required-docs completeness**
- Every document the review-card "Required Submittal Documents" table and the spec submittal
  paragraph require is present.
- Required companion products included (primers, adhesives, grout, fasteners called out with the
  main product).
- Test reports / certs / calcs / O&M present when the spec conditions them on this product.

**L4 Substitutions/or-equal**
- Product is the named/basis-of-design item, or a disclosed or-equal **with the supporting data
  the spec requires** (test reports, certifications).
- Or-equals and anything not on the named list route **RFI to EOR** — GSE doesn't approve subs.
- Undisclosed substitution (sub quietly swapped a product) is at least Major.

**L5 Project context**
- Memory rulings applied (they can suppress a flag or add a requirement).
- Item not already resolved by a prior RFI/CO; scope not superseded by an addendum.
- Consistent with prior approvals and vendor history in the wiki.
- Matches what was actually purchased where PO/scope data is reachable.

## 7.3 By type family (deep guidelines)

### Product / material data
- Every named product accounted for; **all required models/profiles for all applications
  present** (classic miss: waterstops submitted for moving joints but not the required
  non-moving/construction-joint profile — a whole application left uncovered).
- Physical minimums met verbatim; standard matches; potable-vs-wastewater certification correct.
- Or-equals and required companions handled (L4/L3).
- Physical samples submitted where the spec requires them (not just data sheets).

### Shop drawings vs contract drawings — *cannot be closed on specs alone*
- Bar/member **size, grade, spacing, quantity** vs structural drawings & schedules.
- **Development / lap-splice lengths** vs structural general notes (and ACI where referenced).
- Bar marks / placement vs member geometry & dimensions on the contract drawings.
- **Cover / clearances** per drawings (critical in water-retaining/wastewater structures).
- Splice & coupler locations permitted per notes (some locations disallowed).
- Embeds / anchor bolts: size, projection, pattern, location vs drawings.
- Structural steel: member sizes, connection details, bolt grade, weld size vs design.
- Overall geometry reconciles shop-dwg ↔ contract-dwg.
- **Always** query the drawing-db; never assert a dimension above its confidence ceiling.

### Mix designs & test reports
- f'c meets the specified strength for that placement's **class/location** (drawings show which
  mix goes where — a 4000 psi mix in a 4500 psi location is a real fail).
- w/c ratio ≤ spec max; cement type; SCM % (fly ash/slag) within limits; aggregate size/gradation;
  slump range; air-content range.
- Admixtures approved; **chloride limits** (critical for reinforced/prestressed — corrosion).
- Trial batch or field strength history per spec.
- Mill certs: heat numbers tie to the delivered material; yield/tensile meet the grade; chemistry
  within limits.
- Test reports: sampling frequency, lab certification/accreditation, pass/fail vs acceptance.

### Equipment packages
- Performance vs the **scheduled duty point** (flow / head / efficiency) — cross-check the
  equipment schedule on the drawings; a curve that misses the duty point is Critical.
- Motor: HP, voltage/phase, service factor, enclosure (TEFC/etc.), efficiency per spec.
- Materials of construction (wetted parts, coatings/liners) per spec.
- Dimensions/weight vs available space, foundation, and anchorage on the drawings (will it fit
  and can it be anchored as shown?).
- Seismic/vibration anchorage calcs where required (e.g. 40 05 96).
- Electrical/controls coordination (starter/VFD/controls) — often spans sections; note cross-refs.
- O&M, spare-parts list, warranty, factory test reports present per spec.
- If the equipment is **Owner-preselected** (per spec/memory), review for completeness and
  coordination, not product approval.

### Fallback types
Apply 7.1 universal + whatever the governing spec's submittal paragraph enumerates. If no
governing spec exists, say so and check only completeness against the transmittal's own claims.
