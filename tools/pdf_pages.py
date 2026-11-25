"""Render the pages of a PDF to PNG files so the layout can be inspected."""

from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

source = Path(sys.argv[1])
outdir = Path(sys.argv[2])
pages = [int(part) for part in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
outdir.mkdir(parents=True, exist_ok=True)

document = pymupdf.open(source)
print(f"pages: {document.page_count}")
for index in (pages or range(document.page_count)):
    page = document.load_page(index)
    image = page.get_pixmap(dpi=105)
    target = outdir / f"page_{index + 1:02d}.png"
    image.save(target)
    print(f"{index + 1}: {target} ({image.width}x{image.height})")
