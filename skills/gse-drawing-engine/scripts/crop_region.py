"""
crop_region.py — Phase 4, high-resolution crop utility (no AI)

Renders a high-DPI crop of a region of one sheet so fine detail (title block, a
callout, a schedule cell) can be read at a resolution the full-sheet PNG can't
show — the bottom rung of the source-of-truth ladder. Repointed at the
drawing-db namespace. Pure Python.

A sheet is addressed by its page folder (--page page_0007) or by sheet number
(--sheet C-101, resolved via machine/sheet_index.json). The region is a named
preset or an explicit fractional bbox.

Usage:
    python crop_region.py --set-dir <…/drawing-db/<set>> --sheet C-101 [--region title-block]
    python crop_region.py --set-dir <…> --page page_0007 --bbox 0.6,0.85,1.0,1.0 [--dpi 300]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REGIONS = {
    "full": (0.0, 0.0, 1.0, 1.0),
    "title-block": (0.60, 0.82, 1.0, 1.0),
    "top-left": (0.0, 0.0, 0.5, 0.5), "top-right": (0.5, 0.0, 1.0, 0.5),
    "bottom-left": (0.0, 0.5, 0.5, 1.0), "bottom-right": (0.5, 0.5, 1.0, 1.0),
    "top": (0.0, 0.0, 1.0, 0.5), "bottom": (0.0, 0.5, 1.0, 1.0),
    "left": (0.0, 0.0, 0.5, 1.0), "right": (0.5, 0.0, 1.0, 1.0),
    "center": (0.25, 0.25, 0.75, 0.75),
}


def ensure_pymupdf():
    try:
        import fitz  # noqa: F401
    except ImportError:
        print("PyMuPDF not found - installing...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "PyMuPDF"])


def parse_bbox(s):
    try:
        parts = [float(x) for x in s.split(",")]
    except ValueError:
        sys.exit(f"--bbox must be four comma-separated numbers, got {s!r}")
    if len(parts) != 4:
        sys.exit("--bbox needs exactly 4 values: x0,y0,x1,y1")
    x0, y0, x1, y1 = parts
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        sys.exit("--bbox values must be fractions in 0-1 with x0<x1 and y0<y1.")
    return (x0, y0, x1, y1)


def resolve_pdf(set_dir, page, sheet):
    sheets_dir = set_dir / "sheets"
    if page:
        pdf = sheets_dir / page / f"{page}.pdf"
        if not pdf.exists():
            sys.exit(f"Page PDF not found: {pdf}")
        return pdf, page
    idx_path = set_dir / "machine" / "sheet_index.json"
    if not idx_path.exists():
        sys.exit("machine/sheet_index.json not found; use --page instead of --sheet.")
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    for s in idx["sheets"]:
        if s["sheet_number"] == sheet:
            rel = s["paths"].get("pdf")
            if not rel:
                sys.exit(f"No PDF path recorded for sheet {sheet}.")
            pdf = set_dir / rel
            if not pdf.exists():
                sys.exit(f"PDF for {sheet} not found on disk: {pdf}")
            return pdf, sheet
    sys.exit(f"Sheet {sheet!r} not found in sheet_index.json.")


def main():
    p = argparse.ArgumentParser(description="Crop a region of a sheet at high DPI (Phase 4).")
    p.add_argument("--set-dir", required=True, help="drawing-db/<set>/ folder.")
    p.add_argument("--page", help="Page folder name, e.g. page_0007.")
    p.add_argument("--sheet", help="Sheet number, resolved via sheet_index.json.")
    p.add_argument("--region", default="title-block", choices=sorted(REGIONS),
                   help="Named region preset (default: title-block).")
    p.add_argument("--bbox", help="Explicit fractional bbox x0,y0,x1,y1 (overrides --region).")
    p.add_argument("--dpi", type=int, default=300, help="Render DPI for the crop.")
    p.add_argument("--out", help="Output PNG path (default: alongside the sheet).")
    args = p.parse_args()

    if not args.page and not args.sheet:
        sys.exit("Specify --page or --sheet.")

    ensure_pymupdf()
    import fitz

    set_dir = Path(args.set_dir).expanduser().resolve()
    pdf_path, label = resolve_pdf(set_dir, args.page, args.sheet)
    frac = parse_bbox(args.bbox) if args.bbox else REGIONS[args.region]
    region_name = "custom" if args.bbox else args.region

    doc = fitz.open(str(pdf_path))
    page = doc.load_page(0)
    r = page.rect
    clip = fitz.Rect(r.x0 + frac[0] * r.width, r.y0 + frac[1] * r.height,
                     r.x0 + frac[2] * r.width, r.y0 + frac[3] * r.height)
    pix = page.get_pixmap(matrix=fitz.Matrix(args.dpi / 72.0, args.dpi / 72.0), clip=clip, alpha=False)
    out_path = Path(args.out).expanduser().resolve() if args.out else pdf_path.parent / f"crop_{region_name}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(out_path))
    doc.close()
    print(f"Cropped {label} [{region_name}] @ {args.dpi}dpi -> {out_path} ({pix.width}x{pix.height}px)")


if __name__ == "__main__":
    main()
