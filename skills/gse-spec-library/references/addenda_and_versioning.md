# Addenda and Versioning

Read this file when processing an addendum or when a section already exists in `specs-md/` and a newer version has arrived.

---

## Addendum processing rules

An addendum outranks the project manual for every section it revises. When processing an addendum:

1. **Identify which sections the addendum revises.** Read the addendum cover sheet or table of contents. Only process sections the addendum actually changes — do not reprocess unaffected sections.

2. **Write new artifacts for each revised section.**
   - New full section: `specs-md/full-sections/[section-hyphenated]_[addendum-date].md`
   - Replace review card in place: `specs-md/review-cards/[section-hyphenated]_CARD.md` (after confirming with user)
   - Update raw pointer in place: `specs-md/raw-pointers/[section-hyphenated]_POINTER.md`

3. **Never overwrite the old full section file.** The prior version stays in `specs-md/full-sections/` as archive. The index `Supersedes` column records the old filename.

4. **Update `SPEC_INDEX.md`:**
   - Set `Current Full Section` to the new file.
   - Set `Current Review Card` to the (now updated) card path — same path, new content.
   - Set `Issue Date` to the addendum date.
   - Set `Source` to `Addendum N`.
   - Set `Supersedes` to the prior full section filename.
   - Add a row to the `Addenda / Supersession Notes` table.

5. **Confirm the review card replacement with the user before overwriting.** The card is the primary lookup — replacing it silently could break an in-progress review.

---

## Version conflicts

If the user provides a spec section that conflicts with an existing one and it is unclear which governs:

1. Check the issue dates. The later date governs.
2. If both claim to be current or dates are unclear, flag the conflict to the user before processing. Do not guess.
3. If one is an addendum and one is a project manual section, the addendum governs for the sections it covers.

---

## Partial addenda

Some addenda revise only a paragraph or two within a section, not the whole section. In that case:

1. Write the full revised section `.md` anyway — extract the whole section from the updated source (combining project manual base with addendum changes if needed).
2. Update the review card only for fields affected by the addendum revision. Note the change in the `Memory applied` field.
3. Note in the `Addenda / Supersession Notes` table that the addendum was partial and which paragraphs changed.

If the addendum text is a redline/strikethrough version, apply the changes and produce clean output — do not transcribe redline formatting into the `.md` files.

---

## Reprocessing a section

If the user asks to reprocess a section that already has artifacts:

1. Read the existing card, full section, and pointer first.
2. Check whether the source PDF has changed (different date, addendum, or correction).
3. If no source change — inform the user and offer to update only specific fields rather than regenerating everything.
4. If source changed — process as a new version per the addendum rules above.
