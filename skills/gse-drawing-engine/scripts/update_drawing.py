"""
update_drawing.py — Phase 5, incremental update (no AI)

UPDATE mode: a catalogue exists and the source PDF changed (a revised/added/
removed sheet). This re-splits the new PDF, diffs it against the existing ledger
by per-sheet content hash, and reprocesses ONLY what changed — the token-control
guarantee. Unchanged sheets keep their files, classification, and state untouched.

Per page (by page position — the MVP assumption is revisions replace sheets in
place; see references/incremental_update_protocol.md for the add/remove caveat):
  - hash unchanged  → SKIP entirely (no re-render, classification preserved).
  - hash changed    → re-render pdf/png/txt, delete stale classification.json +
                      refs.json, set processing_state="stale" (router → UPDATE;
                      build_sheet_index advances stale→classified once reclassified).
  - new page        → render, processing_state="pending".
  - removed page     → dropped from manifest + ledger, logged in the changelog.

Writes the updated sheets/manifest.json + machine/manifest.json, appends a
changelog entry (machine/changelog.json + views/changelog.md), and sets
run_status="building" so the set is finalized by reclassify → QC. After this,
Claude reclassifies the stale/pending pages, then ALL derived artifacts are
regenerated (tag index, cross-refs, details, RFI, coverage, summary) so no
projection drifts (D5).

Usage:
    python update_drawing.py <new.pdf | drawings_dir> --set-dir <…/drawing-db/<set>>
        [--date YYYY-MM-DD] [--max-edge PX] [--min-text-chars N]
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA_VERSION = "1.0"


def ensure_pymupdf():
    try:
        import fitz  # noqa: F401
    except ImportError:
        print("PyMuPDF not found — installing...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "PyMuPDF"])


def collect_pdfs(input_path: Path):
    if input_path.is_dir():
        pdfs = sorted(p for p in input_path.iterdir() if p.suffix.lower() == ".pdf")
        if not pdfs:
            sys.exit(f"No PDF files found in directory: {input_path}")
        return pdfs
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    sys.exit(f"Input is not a PDF or a directory of PDFs: {input_path}")


def content_hash(text: str) -> str:
    """Must match process_drawing.content_hash — normalized extracted text."""
    norm = "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def render_png(page, out_png, max_edge):
    import fitz
    rect = page.rect
    longest = max(rect.width, rect.height)
    zoom = (max_edge / longest) if longest > 0 else 1.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(str(out_png))
    return pix.width, pix.height


def main():
    p = argparse.ArgumentParser(description="Incremental update by hash-diff (Phase 5).")
    p.add_argument("input", help="Path to the new merged PDF or folder of PDFs.")
    p.add_argument("--set-dir", required=True, help="Existing drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    p.add_argument("--max-edge", type=int, default=2000)
    p.add_argument("--min-text-chars", type=int, default=20)
    args = p.parse_args()

    ensure_pymupdf()
    import fitz

    set_dir = Path(args.set_dir).expanduser().resolve()
    sheets_dir = set_dir / "sheets"
    machine = set_dir / "machine"
    old_split_p = sheets_dir / "manifest.json"
    ledger_p = machine / "manifest.json"
    if not old_split_p.exists() or not ledger_p.exists():
        sys.exit(f"No existing catalogue in {set_dir}. Use process_drawing.py (BUILD) instead.")

    old_split = json.loads(old_split_p.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_p.read_text(encoding="utf-8"))
    old_hash_by_page = {pg["page"]: pg.get("source_hash") for pg in old_split.get("pages", [])}
    old_split_by_page = {pg["page"]: pg for pg in old_split.get("pages", [])}
    led_by_page = {s["page"]: s for s in ledger.get("sheets", [])}

    pdfs = collect_pdfs(Path(args.input).expanduser().resolve())

    new_pages = []
    changed, added, unchanged = [], [], []
    page_counter = 0

    for pdf_path in pdfs:
        doc = fitz.open(str(pdf_path))
        for page_index in range(doc.page_count):
            page_counter += 1
            folder = f"page_{page_counter:04d}"
            page_dir = sheets_dir / folder
            pdf_out = page_dir / f"{folder}.pdf"
            png_out = page_dir / f"{folder}.png"
            txt_out = page_dir / f"{folder}.txt"

            # hash the extracted TEXT (stable across re-export) — no overwrite yet
            page = doc.load_page(page_index)
            text = page.get_text("text") or ""
            new_hash = content_hash(text)
            old_hash = old_hash_by_page.get(page_counter)

            if old_hash is not None and old_hash == new_hash and pdf_out.exists():
                # UNCHANGED — do not touch files or classification
                meta = old_split_by_page.get(page_counter, {})
                new_pages.append({**meta, "page": page_counter, "folder": folder,
                                  "source_pdf": pdf_path.name, "source_page": page_index + 1,
                                  "source_hash": new_hash})
                unchanged.append(page_counter)
                continue

            # CHANGED or NEW — render fresh
            page_dir.mkdir(parents=True, exist_ok=True)
            single = fitz.open()
            single.insert_pdf(doc, from_page=page_index, to_page=page_index)
            single.save(str(pdf_out))
            single.close()
            txt_out.write_text(text, encoding="utf-8")
            px_w, px_h = render_png(page, png_out, args.max_edge)
            # clear stale derived per-page inputs so the sheet is reclassified
            (page_dir / "classification.json").unlink(missing_ok=True)
            (page_dir / "refs.json").unlink(missing_ok=True)

            new_pages.append({
                "page": page_counter, "folder": folder, "source_pdf": pdf_path.name,
                "source_page": page_index + 1, "source_hash": new_hash,
                "paths": {"pdf": f"{folder}/{pdf_out.name}", "png": f"{folder}/{png_out.name}",
                          "txt": f"{folder}/{txt_out.name}"},
                "png_size": [px_w, px_h], "text_chars": len(text.strip()),
                "likely_scanned": len(text.strip()) < args.min_text_chars})
            (changed if old_hash is not None else added).append(page_counter)
        doc.close()

    removed = sorted(set(old_hash_by_page) - {pg["page"] for pg in new_pages})

    # rewrite split manifest
    old_split.update({"generated": args.date, "source_pdfs": [p.name for p in pdfs],
                      "page_count": page_counter, "pages": new_pages})
    old_split_p.write_text(json.dumps(old_split, indent=2), encoding="utf-8")

    # rewrite processing ledger: preserve unchanged, reset changed/new, drop removed
    new_ledger_sheets = []
    for pg in new_pages:
        n = pg["page"]
        old = led_by_page.get(n, {})
        base = {"page": n, "folder": pg["folder"], "source_pdf": pg["source_pdf"],
                "source_page": pg["source_page"], "source_hash": pg["source_hash"]}
        if n in unchanged:
            base.update({"sheet_number": old.get("sheet_number"), "discipline": old.get("discipline"),
                         "processing_state": old.get("processing_state", "complete"),
                         "extraction_confidence": old.get("extraction_confidence"),
                         "last_processed": old.get("last_processed", "")})
        else:
            base.update({"sheet_number": None, "discipline": None,
                         "processing_state": "stale" if n in changed else "pending",
                         "extraction_confidence": None, "last_processed": ""})
        new_ledger_sheets.append(base)

    ledger.update({"generated": args.date, "source_pdfs": [p.name for p in pdfs],
                   "run_status": "building", "sheet_count": len(new_ledger_sheets),
                   "sheets": new_ledger_sheets})
    ledger_p.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    write_changelog(set_dir, args.date, changed, added, removed, unchanged,
                    [p.name for p in pdfs], led_by_page)

    print(f"UPDATE: {len(changed)} revised, {len(added)} new, {len(removed)} removed, "
          f"{len(unchanged)} unchanged (skipped).")
    print(f"  revised pages: {changed or '—'} · new: {added or '—'} · removed: {removed or '—'}")
    if changed or added:
        print("  → reclassify the stale/pending page(s), then regenerate all derived artifacts "
              "(build_sheet_index → build_tag_index → cross_refs → detail_index → "
              "build_rfi_candidates → qc_pass → build_summary).")
    else:
        print("  → no content changes; regenerate derived artifacts only if needed.")


def write_changelog(set_dir, date, changed, added, removed, unchanged, pdfs, led_by_page):
    machine = set_dir / "machine"
    views = set_dir / "views"
    views.mkdir(parents=True, exist_ok=True)

    def names(pages):
        out = []
        for n in pages:
            sn = led_by_page.get(n, {}).get("sheet_number")
            out.append(sn or f"page-{n}")
        return out

    log_p = machine / "changelog.json"
    log = json.loads(log_p.read_text(encoding="utf-8")) if log_p.exists() else \
        {"schema_version": SCHEMA_VERSION, "entries": []}
    entry = {"date": date, "source_pdfs": pdfs,
             "revised": names(changed), "added": [f"page-{n}" for n in added],
             "removed": names(removed), "unchanged_count": len(unchanged)}
    log["entries"].insert(0, entry)
    log_p.write_text(json.dumps(log, indent=2), encoding="utf-8")

    L = [f"# Changelog — {set_dir.name}", ""]
    for e in log["entries"]:
        L.append(f"## {e['date'] or '(no date)'}")
        L.append(f"- Source: {', '.join(e['source_pdfs'])}")
        if e["revised"]:
            L.append(f"- Revised: {', '.join(e['revised'])}")
        if e["added"]:
            L.append(f"- Added: {', '.join(e['added'])}")
        if e["removed"]:
            L.append(f"- Removed: {', '.join(e['removed'])}")
        L.append(f"- Unchanged (skipped): {e['unchanged_count']}")
        L.append("")
    (views / "changelog.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
