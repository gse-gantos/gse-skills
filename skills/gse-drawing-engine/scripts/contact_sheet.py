#!/usr/bin/env python3
"""contact_sheet.py — batch a region of many PDF pages into grid montages (2026-07-02).

Token economics: verifying one fact per sheet (title block, revision stamp,
a schedule row) across a 54-sheet set costs 54 full-page image reads the
naive way. This renders the SAME region of every requested page and tiles
them into labeled grid images, so the whole sweep costs a handful of image
reads at equal or better zoom. Accuracy-neutral: same pixels, larger relative
scale, each tile labeled with its page number.

Usage:
  python contact_sheet.py --pdf "<set.pdf>" --out-dir "<dir>" \
      [--pages 1-54] [--region 0.60,0.85,1.0,1.0] [--cols 3] [--rows 4] [--dpi 150]

--region is x0,y0,x1,y1 as fractions of page size. Default = bottom-right
title-block corner. Common presets:
  title block:  0.60,0.85,1.0,1.0   (default)
  full bottom:  0.0,0.85,1.0,1.0
  full page:    0.0,0.0,1.0,1.0     (use small grids + high dpi)
Writes out-dir/contact_NNN.png files, never overwrites (numbered uniquely).
"""
import argparse
from pathlib import Path

def parse_pages(spec, n):
    if not spec:
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [p for p in out if 1 <= p <= n]

def main():
    import fitz
    from PIL import Image, ImageDraw
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pages", default="")
    ap.add_argument("--region", default="0.60,0.85,1.0,1.0")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    pages = parse_pages(a.pages, doc.page_count)
    x0f, y0f, x1f, y1f = [float(v) for v in a.region.split(",")]
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    tiles = []
    for pno in pages:
        pg = doc[pno - 1]
        r = pg.rect
        clip = fitz.Rect(r.x0 + x0f * r.width, r.y0 + y0f * r.height,
                         r.x0 + x1f * r.width, r.y0 + y1f * r.height)
        pix = pg.get_pixmap(dpi=a.dpi, clip=clip)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        d = ImageDraw.Draw(img)
        label = f"p{pno}"
        d.rectangle([0, 0, 8 * len(label) + 10, 18], fill=(190, 30, 45))
        d.text((5, 3), label, fill=(255, 255, 255))
        tiles.append(img)

    per, sheets = a.cols * a.rows, []
    existing = {p.name for p in out.glob("contact_*.png")}
    idx = 1
    for i in range(0, len(tiles), per):
        batch = tiles[i:i + per]
        w = max(t.width for t in batch); h = max(t.height for t in batch)
        cols = min(a.cols, len(batch)); rows = (len(batch) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * w + (cols + 1) * 4, rows * h + (rows + 1) * 4), (65, 64, 66))
        for j, t in enumerate(batch):
            cx, cy = j % cols, j // cols
            sheet.paste(t, (4 + cx * (w + 4), 4 + cy * (h + 4)))
        while f"contact_{idx:03d}.png" in existing:
            idx += 1
        name = f"contact_{idx:03d}.png"; existing.add(name); idx += 1
        sheet.save(out / name)
        first, last = pages[i], pages[min(i + per, len(pages)) - 1]
        sheets.append((name, first, last))
        print(f"{name}: pages {first}-{last} ({len(batch)} tiles, {sheet.width}x{sheet.height})")
    print(f"done: {len(tiles)} regions -> {len(sheets)} contact sheet(s)")

if __name__ == "__main__":
    main()
