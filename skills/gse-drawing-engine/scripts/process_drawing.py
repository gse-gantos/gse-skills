"""
process_drawing.py — Phase 1, deterministic split/extract/render (no AI)

Ported from read-drawing-beta and repointed at the drawing-engine canonical
namespace. For a merged drawing PDF (or a folder of PDFs) this script:
  1. Splits it into one single-page PDF per page.
  2. Extracts vector text from each page (PyMuPDF get_text — NOT OCR).
  3. Renders each page to a PNG sized for Claude Vision.
  4. Writes per-page files to  <set>/sheets/page_NNNN/  and a split manifest
     <set>/sheets/manifest.json  (page -> file paths, text density, source hash).
  5. Bootstraps the PROCESSING ledger  <set>/machine/manifest.json  with every
     page set to processing_state="pending" BEFORE any index row exists.

Resumable + idempotent (FS-7): a page whose pdf/png/txt already exist on disk is
skipped unless --force.

Usage:
    python process_drawing.py <input.pdf | drawings_dir> --set-dir <.../drawing-db/<set>>
        [--date YYYY-MM-DD] [--max-edge PX] [--min-text-chars N] [--force]
"""

import argparse
import hashlib
import json
import subprocess
import sys
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
    """Stable hash of a sheet's extracted text — feeds Phase 5 stale detection.

    Hashing the normalized TEXT (not raw PDF bytes) is stable across a re-export
    of the set: an unchanged sheet extracts identical text even when the parent
    PDF's bytes/metadata differ, while a revised callout/note/title-block changes
    the text. Limitation: a purely visual revision with no text-layer change isn't
    auto-detected (use --force) — noted in the incremental-update reference.
    """
    norm = "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def render_png(page, out_png: Path, max_edge: int):
    import fitz
    rect = page.rect
    longest_pt = max(rect.width, rect.height)
    zoom = (max_edge / longest_pt) if longest_pt > 0 else 1.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(str(out_png))
    return pix.width, pix.height


def _png_size(png_path: Path):
    import fitz
    pix = fitz.Pixmap(str(png_path))
    return pix.width, pix.height


def process(input_path, set_dir, date, max_edge, min_text_chars, force):
    import fitz

    pdfs = collect_pdfs(input_path)
    sheets_dir = set_dir / "sheets"
    machine_dir = set_dir / "machine"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    machine_dir.mkdir(parents=True, exist_ok=True)

    manifest_pages = []
    page_counter = 0
    skipped = 0

    for pdf_path in pdfs:
        doc = fitz.open(str(pdf_path))
        print(f"Processing {pdf_path.name} - {doc.page_count} page(s)")

        for page_index in range(doc.page_count):
            page_counter += 1
            folder_name = f"page_{page_counter:04d}"
            page_dir = sheets_dir / folder_name
            pdf_out = page_dir / f"{folder_name}.pdf"
            png_out = page_dir / f"{folder_name}.png"
            txt_out = page_dir / f"{folder_name}.txt"

            already = pdf_out.exists() and png_out.exists() and txt_out.exists()
            if already and not force:
                text = txt_out.read_text(encoding="utf-8", errors="ignore")
                text_chars = len(text.strip())
                try:
                    px_w, px_h = _png_size(png_out)
                except Exception:
                    px_w, px_h = 0, 0
                src_hash = content_hash(text)
                skipped += 1
                flag = "  [resumed — skipped]"
            else:
                page_dir.mkdir(parents=True, exist_ok=True)
                page = doc.load_page(page_index)

                single = fitz.open()
                single.insert_pdf(doc, from_page=page_index, to_page=page_index)
                single.save(str(pdf_out))
                single.close()

                text = page.get_text("text") or ""
                txt_out.write_text(text, encoding="utf-8")
                text_chars = len(text.strip())
                src_hash = content_hash(text)
                px_w, px_h = render_png(page, png_out, max_edge)
                flag = "  [LIKELY SCANNED]" if text_chars < min_text_chars else ""

            manifest_pages.append({
                "page": page_counter,
                "folder": folder_name,
                "source_pdf": pdf_path.name,
                "source_page": page_index + 1,
                "source_hash": src_hash,
                "paths": {
                    "pdf": f"{folder_name}/{pdf_out.name}",
                    "png": f"{folder_name}/{png_out.name}",
                    "txt": f"{folder_name}/{txt_out.name}",
                },
                "png_size": [px_w, px_h],
                "text_chars": text_chars,
                "likely_scanned": text_chars < min_text_chars,
            })
            print(f"  {folder_name}  ({px_w}x{px_h}px, {text_chars} chars){flag}")

        doc.close()

    split_manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated": date,
        "source_pdfs": [p.name for p in pdfs],
        "page_count": page_counter,
        "render_max_edge": max_edge,
        "pages": manifest_pages,
    }
    (sheets_dir / "manifest.json").write_text(json.dumps(split_manifest, indent=2), encoding="utf-8")

    bootstrap_processing_ledger(machine_dir, manifest_pages, pdfs, date)

    print(f"\nDone. {page_counter} page(s) ({skipped} resumed) -> {sheets_dir}")
    scanned = [p["folder"] for p in manifest_pages if p["likely_scanned"]]
    if scanned:
        print(f"WARNING: {len(scanned)} page(s) look scanned/image-only: {', '.join(scanned)}")


def bootstrap_processing_ledger(machine_dir, manifest_pages, pdfs, date):
    """Create or update machine/manifest.json with one pending entry per page.

    On a resume, preserve the state of pages already advanced; only reset a page
    to 'stale' if its source_hash changed since last run.
    """
    ledger_path = machine_dir / "manifest.json"
    prior = {}
    if ledger_path.exists():
        try:
            old = json.loads(ledger_path.read_text(encoding="utf-8"))
            for s in old.get("sheets", []):
                prior[s.get("page")] = s
        except json.JSONDecodeError:
            pass

    sheets = []
    for p in manifest_pages:
        old = prior.get(p["page"], {})
        state = old.get("processing_state", "pending")
        if old and old.get("source_hash") and old["source_hash"] != p["source_hash"]:
            state = "stale"
        sheets.append({
            "page": p["page"],
            "folder": p["folder"],
            "source_pdf": p["source_pdf"],
            "source_page": p["source_page"],
            "source_hash": p["source_hash"],
            "sheet_number": old.get("sheet_number"),
            "discipline": old.get("discipline"),
            "processing_state": state,
            "extraction_confidence": old.get("extraction_confidence"),
            "last_processed": old.get("last_processed", ""),
        })

    ledger = {
        "schema_version": SCHEMA_VERSION,
        "generated": date,
        "set_name": machine_dir.parent.name,
        "run_status": "building",
        "source_pdfs": [p.name for p in pdfs],
        "sheet_count": len(sheets),
        "sheets": sheets,
    }
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Split & extract a drawing PDF into the drawing-db namespace (Phase 1).")
    p.add_argument("input", help="Path to a merged PDF or a folder of PDFs.")
    p.add_argument("--set-dir", required=True, help="Target drawing-db/<set>/ folder.")
    p.add_argument("--date", default="", help="ISO generated date (passed in; not invented).")
    p.add_argument("--max-edge", type=int, default=2000, help="PNG longest edge in px.")
    p.add_argument("--min-text-chars", type=int, default=20, help="Scanned-page threshold.")
    p.add_argument("--force", action="store_true", help="Re-render pages even if outputs exist.")
    args = p.parse_args()

    ensure_pymupdf()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        sys.exit(f"Input not found: {input_path}")
    set_dir = Path(args.set_dir).expanduser().resolve()
    if not args.date:
        print("NOTE: no --date supplied; 'generated' will be empty.", file=sys.stderr)

    print(f"Set: {set_dir}")
    process(input_path, set_dir, args.date, args.max_edge, args.min_text_chars, args.force)


if __name__ == "__main__":
    main()
