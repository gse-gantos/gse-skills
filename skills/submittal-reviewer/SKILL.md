---
name: submittal-reviewer
description: Review a construction submittal as the GC before forwarding it to the EOR. Use when the user points at a submittal package (product data, shop drawings, mix design, test reports, equipment/O&M) and wants it checked, reviewed, or vetted against the specs, contract drawings, wiki, and project memory. Classifies the submittal, routes each piece to the authoritative source, runs a check-lens verification swarm with an adversarial QC pass, and writes one markdown file of issues ranked by severity then confidence. Also trigger on "review submittal", "check this submittal", "vet this shop drawing", "is this submittal compliant", or a submittal number (e.g. "review 525"). Step 2 of the spec-library / submittal-review system — consumes the spec review-cards, drawing-db, and wiki that those skills produce.
---

# Submittal Reviewer

Review a submittal the way a GC does: catch everything GSE should fix, clarify with the sub,
or RFI to the engineer **before** the package leaves GSE's hands — so it comes back clean and
GSE isn't the reason for a rejection. This skill does **not** stamp "Approved." The approving
authority is the design engineer (EOR). Every finding is framed as "resolve before forwarding."

The full rationale, decisions, and background are in
`../../Platform/skill_proposals/submittal-reviewer/DESIGN.md`. This file is the operating
procedure. Read the referenced file before each phase — do not run from memory of the template.

---

## Core principles

- **Read, don't re-derive.** The specs, drawings, and wiki are already processed into retrieval
  layers. Read those layers. Only open a raw PDF when a layer is missing or a value must be
  verified at the source.
- **Cite everything.** No finding survives without a source it points to (spec §paragraph,
  sheet number + detail, wiki page, memory entry). A finding with no citation gets cut in QC.
- **Be honest about what you can't check.** "No governing spec," "value not defined,"
  "drawing value is inferred" are real, useful answers. Never invent a requirement or assert a
  dimension above its confidence ceiling.
- **Spec gaps are the engineer's, not the sub's.** Where the spec defines no measurable
  criterion, flag it to the EOR — do not penalize the sub.
- **Human-in-the-loop.** Always produce a draft for a person to act on. Never auto-submit or
  auto-respond in Procore.

---

## Step 0 — Orient: locate the submittal and the retrieval layers

Everything here is **discovery-based** — paths vary by subproject and job. Find what exists;
degrade gracefully when a source is absent (say so in the output rather than guessing).

1. **Identify the submittal.** Get the raw package (folder or PDFs). Typical home:
   `Submittals/<subproject>/…`, but **consult `Claude/Map/` first** (`views/FILE_MAP.md` /
   `machine/manifest.json`) — submittal-relevant docs can sit in odd folders and the map
   knows where. Capture number, title, and which subproject (`_spNN-name`).
   **Revision rule (AGENTS.md §4):** submittal foldering is free-form — the current revision
   is the LATEST revision in the package folder by transmittal/rev metadata, not folder
   position; anything superseded or `_archive`-style is off-limits for review. Unsure which
   rev is current? Ask.
2. **Detect the retrieval layers** for that subproject (see `references/retrieval_interfaces.md`):
   - **Specs** — find the subproject's `SPEC_INDEX.md` (e.g.
     `Claude/Specifications/<subproject>/specs-md/SPEC_INDEX.md`, or a shared
     `Claude/Specifications/`). Read it first; it points to review-cards, full-sections, raw-pointers,
     and the Missing/Undefined registries.
   - **Drawings** — find the subproject's drawing data under `Claude/Drawings/<subproject>/`.
     If it's in current drawing-engine form (`drawing-db/<set>/machine`), use drawing-engine
     QUERY mode. If it's an older `drawings-md` form, read the sheet cards / text directly.
   - **Wiki** — query `Claude/_Memory/` via the **gse-wiki-query** skill (plugin
     `gsewiki:query` acceptable until the fork is validated). Check `_Memory/AGENTS.md`
     §3 FIRST — this job's binding owner/engineer clarifications override spec text and
     must never be re-flagged as discrepancies.
   - **Memory** — RETIRED (AGENTS.md §9): do NOT look for MEMORY.md files. `_Memory/` (via
     the wiki query above) is the single memory system; `Claude/CLAUDE.md` is the boot file.
   - **Prior reviews / RFIs / COs** — `Claude/Submittals/<subproject>/reviews/`,
     `RFIs/`, `Change Orders/` — to avoid re-flagging resolved items and catch resubmittal deltas.
3. **Report what you found** in one line before proceeding, e.g.:
   > Reviewing Submittal 525 (headworks-bypass). Specs: SPEC_INDEX found (1 section). Drawings:
   > drawing-db present. Wiki: not available. Memory: none in mount. Prior reviews: none.

---

## Step 1 — Choose the review mode (ALWAYS ASK)

Do not auto-pick. Present the choice and wait:

- **Standard** — one reviewer works the lenses in sequence. Faster/cheaper. Good for a small,
  single-product package.
- **Deep** — a parallel agent swarm (one subagent per check-lens) plus an adversarial QC loop.
  Slower/more thorough. Use for large, multi-product, or high-stakes packages (structural,
  equipment, anything where a miss is expensive).

State a recommendation with the ask (based on package size/complexity), but let the user decide.

---

## Phase 0 — Intake, classification, routing (the "brain")

Read `references/type_detection.md` and `references/routing_matrix.md` first.

1. **Intake.** Read the transmittal/cover. Capture: submittal no., title, claimed spec
   section(s), revision, sub/vendor, date. If the claimed section doesn't match the content,
   that mismatch is itself a finding.
2. **Classify the type** (product/material · shop-drawings-vs-drawings · mix-design/test-report ·
   equipment · fallback) using the rubric in `type_detection.md`. Type drives which source is
   authoritative.
3. **Decompose.** If `Claude/Submittals/<subproject>/submittals-md/pieces/` already exists for
   this submittal, **reuse it**. Otherwise build it: one piece file per product/component with
   extracted technical values, each tagged with source page + extraction confidence (match the
   existing piece format). Never re-extract what's already decomposed.
4. **Write the verification plan.** For each piece, state *what must be verified, against which
   source, and where that source lives* — using `routing_matrix.md`. This is where the
   "can't fully verify on specs — check the drawings" routing becomes explicit (e.g. rebar →
   contract drawings for size/spacing/development; spec for material/standards only).
   Where the routing matrix has no row for the detected type, use the fallback and say so.

---

## Phase 1 — Verification (check-lens swarm)

Read `references/lens_swarm.md` and `references/checklist_library.md` first.

Five lenses. In **Deep mode**, spawn one subagent per lens (Task tool), in parallel, each with
its checklist, the pieces, the verification plan, and pointers to the retrieval layers. In
**Standard mode**, work the five lenses yourself in sequence.

1. Materials & standards
2. Dimensions / config / quantities vs drawings
3. Required-documents completeness
4. Substitutions / or-equal / deviations
5. Project context (memory + wiki + prior RFIs/COs)

Each finding uses the schema in `lens_swarm.md` (id, lens, piece, description, evidence,
severity, confidence, action, verifiable). No citation → not a finding.

---

## Phase 2 — Adversarial QC

Read `references/qc_loop.md` first.

Challenge every Phase-1 finding: is it real (re-check the cited source)? is the citation valid?
is severity/confidence calibrated? what did the lenses miss? Kill false positives, adjust
severity/confidence, add any missed items. Loop until stable (1–2 passes). This pass is what
makes the ranking trustworthy.

In **Standard mode**, still do one honest self-challenge pass over your own findings.

---

## Phase 3 — Output

Read `references/output_format.md` and `references/severity_confidence.md` first.

Write **one** markdown file:
`Claude/Submittals/<subproject>/reviews/<num>-<slug>-review.md`

- Header (submittal, detected type, spec section(s), sources consulted, review mode).
- Recommended **GC disposition** (one line, from the vocabulary in `output_format.md`) + blocking issue(s).
- **Issues — ranked**: grouped Critical → Major → Minor; within each group sorted by confidence
  (High → Low). Columns: `# | Issue | Finding | Evidence | Severity | Confidence | Action`.
- **Unverifiable / needs EOR or RFI**.
- **Spec gaps** (engineer's undefined criteria).
- **Checked — no issue** (what passed — shows the review was thorough).
- **Memory applied** (which project rulings shaped the review).

Then append one line to `Claude/Submittals/<subproject>/reviews/REVIEW_LOG.md`.

**Output path ruling (F5a, 2026-07-10):** `Claude/Submittals/_spNN/reviews/` is canonical —
the old flat `Claude/Submittals/drafts/` is retired.

**Map-update contract (MANDATORY, `Claude/Map/machine/MAP_UPDATE_CONTRACT.md`):** mark the
submittal package's manifest record `processed` with `processed_home` → the review file; if
the package batch record covers more than what was reviewed, split the batch first. A
resubmittal supersedes the prior rev → register it (feeds `SUPERSEDED.md`). Regenerate map
views (`gse-cartographer/scripts/render_views.py`). Reviews carry `**Wiki:** [[hub-page]]`
backlinks (D9); log the run in `_Memory/log.md` (house format).

Finish by telling the user the disposition and the blocking issues in one or two sentences, and
present the review file.

---

## Reference files

Read the relevant reference at the phase noted — don't rely on memory.

- `references/retrieval_interfaces.md` — how to find and drive specs / drawings / wiki / memory. **Step 0.**
- `references/type_detection.md` — submittal type rubric (expandable). **Phase 0.**
- `references/routing_matrix.md` — type → authoritative source. **Phase 0.**
- `references/lens_swarm.md` — the five lenses, subagent contracts, finding schema. **Phase 1.**
- `references/checklist_library.md` — everything the lenses look for (universal / by lens / by type). **Phase 1.**
- `references/qc_loop.md` — adversarial pass rules + convergence. **Phase 2.**
- `references/severity_confidence.md` — severity & confidence definitions + ranking. **Phase 3.**
- `references/output_format.md` — review file schema + disposition vocabulary. **Phase 3.**

---

## Expanding to new submittal types

The skill is built to grow. To add a type: add a row to `routing_matrix.md` (type → source),
a detection signal to `type_detection.md`, and a checklist block to `checklist_library.md §7.3`.
No other file needs to change.
