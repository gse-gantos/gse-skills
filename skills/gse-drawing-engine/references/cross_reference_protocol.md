# Cross-Reference Protocol (Phase 2)

Builds the navigation graph of the set — which sheet points to which, and which
callouts point nowhere (the unresolved ones become RFI candidates). Claude finds
the references; `build_cross_references.py` resolves and assembles them.

## Per-page contract — `<set>/sheets/page_NNNN/refs.json`

For each page that references other sheets or external docs, write the **outgoing**
references only (`from_sheet` is stamped by the script from the page's
classification):

```json
{
  "references": [
    {
      "to_sheet": "C-501",
      "external_ref": null,
      "ref_type": "detail",
      "label": "3/C-501",
      "context": "Trench section for 24\" influent main called out at STA 12+50.",
      "confidence": "high"
    },
    {
      "to_sheet": null,
      "external_ref": "Spec 33 05 13",
      "ref_type": "spec",
      "label": "SEE SPEC 33 05 13",
      "context": "Pipe bedding per spec.",
      "confidence": "medium"
    }
  ]
}
```

- `ref_type`: `detail | section | continuation | schedule | note | spec | match_line | key_plan | other`.
- `to_sheet` is a `sheet_number` in this set, or `null` if the target is external
  or can't be resolved. Set `external_ref` instead when it points outside the set
  (spec section, standard detail, vendor doc).
- `label` is the callout text exactly as printed (`"3/C-501"`, `"SIM"`,
  `"SEE 5/S-201"`). `confidence` per `provenance_contract.md`.

Read the page's `.txt` (and the `.png` when geometry matters) for callouts like
`3/C-501`, `SEE S-201`, match lines, `SEE SPEC 33 05 13`. Pages with no references
need no `refs.json`.

## Assembly

```
python scripts/build_cross_references.py --set-dir "<set>" --date YYYY-MM-DD
```

The script stamps `from_sheet`, resolves `to_sheet` against the known sheet set,
and **demotes any target not in the set to `to_sheet: null`** with a note in
`context` — these are kept as coordination signals, never dropped. Output:
`<set>/machine/cross_references.json`.

## Detail index

```
python scripts/build_detail_index.py --set-dir "<set>" --date YYYY-MM-DD
```

Catalogues each detail from the `details_defined` fields and stamps `referenced_by`
from the cross-references whose label cites that detail number into the defining
sheet. Output: `machine/detail_index.json` + `views/detail_index.md`.

After this, re-run `build_tag_index.py` so tags pick up their `referenced_by`
links from the now-present `cross_references.json`.
