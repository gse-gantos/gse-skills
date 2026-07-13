# Retrieval interfaces — how to find and drive each source

Read at **Step 0**. Everything is discovery-based: locate what exists for *this* subproject,
then drive it. When a source is absent, say so in the output and continue — a missing source is
a caveat, never a guess.

Convention below: `<sub>` = the subproject namespace folder, following the `_spNN-<name>`
pattern (e.g. `_sp01-<name>`, `_sp02-<name>`).

---

## 1. Specs (usually the authoritative source)

**Find the index first.** Look for the subproject's spec index:
```
Claude/Specifications/<sub>/specs-md/SPEC_INDEX.md      (per-subproject — preferred)
Claude/Specifications/SPEC_INDEX.md                     (shared/legacy)
```
Glob for `SPEC_INDEX.md` under `Claude/Specifications/` if the exact path isn't obvious.

**Then follow the ladder — cheapest first:**
1. **Review card** — `review-cards/<section>_CARD.md`. Read this first. It has the
   Approval-Critical Checks, Required Submittal Documents, Applicability Rules, Substitution
   criteria, "Usually Do Not Flag," Spec Gaps, and an **"Escalate To Full Section When"** block.
2. **Full section** — `full-sections/<section>_<date>.md`. Open only when the card's Escalate
   block says to (reject/revise decisions, welded-splice procedures, or-equal not on the named
   list, ambiguous criteria).
3. **Raw pointer** — `raw-pointers/<section>_POINTER.md`. Points into the source PDF for
   high-stakes verification of exact wording.

Resolve card/section/pointer paths **relative to the SPEC_INDEX** (it stores them as relative
links). Don't assume a fixed folder — the index is the source of truth for where they live.

**Two registries in the index you must use:**
- **Missing Sections Registry** — if the governing section for a piece is listed here, the honest
  answer is "**no governing spec** — route to drawings/contract or RFI," not a fabricated check.
- **Undefined Criteria Registry** — a required submittal with no measurable acceptance value is a
  **spec gap** (engineer's, not the sub's).

**Verbatim rule:** when a check involves a number, material, grade, or standard, pull it verbatim
from the card/section and cite the paragraph (e.g. `§2.01.A.1`).

---

## 2. Drawings (authoritative for dimensions, sizes, layout, quantities)

Drawing data lives under `Claude/Drawings/<sub>/`. Two formats exist — detect which:

### Format A — current drawing-engine (`drawing-db/<set>/machine` present)
Use **drawing-engine QUERY mode**. Either invoke the `drawing-engine` skill for the query, or
run its query script directly against the set:
```
python <drawing-engine>/scripts/query_drawing.py --set-dir "Claude/Drawings/<sub>/drawing-db/<set>" \
    "natural language question"  [--equipment TAG] [--tag "RAS"] [--discipline Structural] [--json]
```
`<drawing-engine>` = the installed drawing-engine skill's folder (its `scripts/` dir). The script
returns candidate sheets; it does **not** answer. Then follow the **source-of-truth ladder**:
1. `views/drawings.md` (master summary — read first; check the coverage banner)
2. `views/cards/<sheet>.md` (curated sheet summary)
3. `sheets/page_NNNN/page_NNNN.txt` (unfiltered text)
4. `sheets/page_NNNN/page_NNNN.png` (when geometry / what-points-to-what matters)
5. `crop_region.py --set-dir <set> --sheet <SN> --region title-block` (or `--bbox`) for fine print

**Coverage & confidence contract:** if the target sheet is pending/failed, the query returns a
`coverage_gap` — treat the item as **unverifiable**, name the missing sheet, do not rebuild.
Never state a dimension/tag/material above its sheet's **confidence ceiling**; surface anything
marked `[inferred]` as an inference, not a fact.

### Format B — older `drawings-md` (registers / sheet-cards / sheets, no machine dir)
No query script. Orient from the set's sheet index / `registers/` (e.g. `SUBMITTAL_CANDIDATES.md`),
open the relevant `sheet-cards/` or `sheets/*.txt`, and go to the `.png` when geometry matters.
Same honesty rules: cite the sheet number; don't assert what you can't see.

**Always cite sheet number (and detail callout) for every drawing-based finding.**

---

## 3. Wiki (institutional context)

Attempt the **`gsewiki:query`** skill for prior decisions, vendor history, and standard
practices ("has this manufacturer been approved before?", "did we already RFI this?").

If no wiki is configured or reachable in this session, **skip it** and record
"wiki not available" under sources consulted. Do not fabricate institutional history.

---

## 4. Project rulings (via _Memory — the MEMORY.md hierarchy is RETIRED)

*(Updated 2026-07-10, ultraplan 4.3/D2 — do not look for MEMORY.md files.)*

Sources, in authority order:
```
Claude/_Memory/AGENTS.md §3         (binding owner/engineer clarifications — override spec text)
Claude/_Memory/AGENTS.md §9         (project rulings: naming, revision rule, design-firm rule)
Claude/_Memory/wiki/ topic pages    (via gse-wiki query: gaskets, waterstop, valves, coatings…)
Claude/CLAUDE.md                    (boot rules)
```
Rulings can **suppress** a flag (e.g. "GSE self-performs this scope — don't flag it"; "the
Owner owns this equipment selection — don't flag a product substitution") or **add** a rule. Apply in
Phase 1 and cite the ruling's source (AGENTS.md §3 row / wiki page) in the "Rulings applied"
output section. `meta/contradictions.md` and `meta/open-questions.md` tell you what is
genuinely unsettled — don't present a known open question as a new finding.

---

## 5. Prior reviews / RFIs / change orders

Before flagging, check:
```
Claude/Submittals/<sub>/reviews/         (and REVIEW_LOG.md)
RFIs/                                    (open + answered)
Change Orders/ , Change Events/
```
Purpose: don't re-flag something already resolved; catch when this is a **resubmittal** (review
only the deltas vs. the prior review); catch scope **superseded by an addendum or CO**.
