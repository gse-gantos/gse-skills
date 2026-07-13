# Query Protocol (Phase 4 — QUERY mode)

The read interface. Loaded **alone** in QUERY mode (FS-2) — no write protocols.
Answer from the database, never by re-reading the raw PDF.

## Order of operations

1. **Orient.** Read `views/drawings.md` first — the compact master summary built
   to route a question to the right sheets. Check its coverage banner.
2. **Find candidates.**
   ```
   python scripts/query_drawing.py --set-dir "<set>" "natural language question"
       [--discipline Civil] [--equipment P-101] [--tag "RAS"] [--limit 8] [--json]
   ```
   - **Tag/equipment questions resolve through `tag_index.json` in one lookup**
     (`--equipment P-101`) — the precomputed inverted index, not a scan. It returns
     the sheets, the confidence ceiling, cheap attributes, and evidence paths.
   - NL questions are scored against classification fields, boosted by any tag the
     query names. Candidates are a first-pass filter, **not the answer.**
3. **Read the actual sheet — source-of-truth ladder.** A derived summary is enough
   only for an unambiguous, already-corroborated fact. The moment anything is
   uncertain — a dimension, tag, material, count, location, or whether a summary
   really reflects the sheet — go deeper, in order:
   1. `views/cards/[sheet].md` — curated summary + cleaned text (quick read)
   2. `sheets/page_NNNN/page_NNNN.txt` — unfiltered extracted text
   3. `sheets/page_NNNN/page_NNNN.png` — when geometry / what-points-to-what matters
   4. `crop_region.py --set-dir <set> --sheet <SN> --region title-block` (or a
      `--bbox`) — to read fine print sharply instead of guessing
   Reading one more file is cheap; a wrong number on a drawing is not.
4. **Answer** from the GC's perspective, **always citing sheet numbers** (and detail
   callouts where relevant) — only after seeing the evidence. State no dimension,
   tag, material, or count you haven't confirmed in the `.txt`, `.png`, or a crop.
   Respect the provenance contract: surface `[inferred]` items as inferences, and
   never state a value above its sheet's confidence ceiling.

## FS-1 — coverage gap, never a silent rebuild

`query_drawing.py` checks coverage before answering. If the question targets a
sheet that is **pending or failed** (a `--show` on it, or an explicit sheet number
in the query), the script returns a structured **`coverage_gap`** signal naming the
missing sheets and exits with code 4 — it does **not** process anything. Options
then: answer only from processed sheets with an explicit caveat, or run BUILD/
UPDATE deliberately to process the missing sheets. Heavy (re)processing is never
triggered inline by a query. Cheap reads of already-`complete` sheets are fine.

If overall coverage is partial, every result is prefixed with a PARTIAL banner so
the answer is caveated even when the specific candidates are processed.

## Refreshing the entry point

`views/drawings.md` is a projection — regenerate it (and it'll pick up current
coverage) with `python scripts/build_summary.py --set-dir "<set>" --date YYYY-MM-DD`
after any build/QC/update. Never hand-edit it.
