# Tooling (build-engine detection & recalc verification)

Decide the build engine at **Step 0(b)**, before writing a single formula, and verify recalc
at **Step 10**. The workbook is only trustworthy if its formulas were actually evaluated by an
engine — a formula written but never recalculated is an unverified claim.

## Step-0 detection order

### (a) Claude for Excel available / connected → preferred

Use it for live negotiation models. Formulas are verified in Excel's own engine; the
contiguous unit-price input block (`workbook_spec.md`) becomes the "yellow cells" where
pending prices drop in, and every rollup reflows as prices land. This is the ideal engine when
more prices are still arriving.

### (b) Otherwise → openpyxl via the xlsx skill

Write **formulas, not values** — then **verify by recalculation**. openpyxl does not evaluate
formulas; it only writes them, so you must hand the file to something that recalculates:

- **Windows with Excel installed → Excel COM automation via PowerShell:**

  ```powershell
  $xl = New-Object -ComObject Excel.Application
  $xl.Visible = $false
  $xl.DisplayAlerts = $false
  $wb = $xl.Workbooks.Open("C:\path\to\analysis.xlsx")
  $xl.CalculateFull()
  $wb.Save()
  $wb.Close($true)
  $xl.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
  ```

- **Else LibreOffice headless recalc, if available:**

  ```bash
  soffice --headless --convert-to xlsx:"Calc MS Excel 2007 XML" \
          --outdir <out-dir> "C:\path\to\analysis.xlsx"
  ```

  This recalculates on load only if "recalculate on file load" is set to *Always* (Tools →
  Options → Calc → Formula → Recalculation on File Load, or the equivalent registry/config
  key) — set it before relying on the conversion to refresh cached values.

- **If no recalc path works** (e.g. a sandbox mount locks the file, no Excel, no LibreOffice):
  compute every derived value independently in Python, write the **formulas** into the cells
  anyway (so the workbook stays live for the user), and **DISCLOSE in the summary**: "formulas
  unverified by an engine; values cross-checked in Python." Never present engine-unverified
  numbers as verified.

### (c) Integrity gate (non-negotiable, whichever engine)

Extracted section and grand totals **must tie to each source quote's stated totals BEFORE any
analysis.** If they don't tie, the extraction or alignment is wrong — stop and fix it, don't
analyze a workbook whose inputs don't reconcile to the quotes they came from.

## openpyxl practicals (just enough to prevent the known failure modes)

- **Round-trip formulas:** `load_workbook(path, data_only=False)`. `data_only=True` drops the
  formulas and returns only cached values — never load with it when you intend to keep the
  model live.
- **`_xlfn.` prefix for post-2007 functions (engine-verified gotcha):** openpyxl writes
  formula strings verbatim, and Excel resolves any function newer than Excel 2007 —
  `TEXTJOIN`, `MINIFS`, `MAXIFS`, `IFS`, `SWITCH` — only if the openpyxl-written string uses
  the `_xlfn.` prefix (e.g. `=_xlfn.TEXTJOIN(...)`, `=_xlfn.MINIFS(...)`). Written bare, the
  cell shows `#NAME?` after recalc. This bites the per-line low-bidder/premium formulas
  (`flags_and_metrics.md` uses MINIFS/MAXIFS) and the recommendation cell (TEXTJOIN,
  `workbook_spec.md`). Excel displays the function normally — the prefix is invisible to the
  user. Claude for Excel does not need the prefix; only openpyxl-authored files do.
- **Cell comments** (corrections, projection basis):
  `from openpyxl.comments import Comment; cell.comment = Comment(text, author)`.
- **Conditional formatting** (the premium-% bands, `flags_and_metrics.md`):
  `from openpyxl.formatting.rule import CellIsRule` — three rules on the premium-% range:
  `lessThan 0.10` green, `between 0.10 0.20` yellow, `greaterThan 0.20` red; a separate amber
  rule keyed to the GAP-flag column.
- **Italic projected flags:** `from openpyxl.styles import Font; cell.font = Font(italic=True)`.
- **Freeze panes:** `ws.freeze_panes = "A2"`.
- **Outline grouping (never hide rows):**
  `ws.row_dimensions.group(a, b, outline_level=1)` /
  `ws.column_dimensions.group('X', 'Y', outline_level=1)`.
- **Error sweep after every formula write:** scan the recalculated values for `#VALUE!`,
  `#REF!`, `#N/A`, `#NAME?` (and `#DIV/0!`) and fix them before presenting anything.
