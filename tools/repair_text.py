"""Restore the typography a PowerShell round-trip mangled, by damage pattern.

Every non-ASCII glyph in the builders became the two characters "鈥?" (en dash or
bullet) or "鈮?" (less-or-equal) plus one byte eaten by the lossy decode.  Matching the
damage pattern instead of the quoting keeps the repair independent of the context.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

RULES = [
    # bullets: either a lone "鈥" or the damaged "鈥?" pair
    (re.compile("\u201d?\u9225\\?(?=\\s?\\+\\s?item)"), "\u2022"),
    (re.compile("\u9225\\?\\s(?=item)"), "\u2022 "),
    (re.compile("(\u9225\\?)(?=\\s?[A-Za-z0-9\\\"])"), "\u2013"),
    (re.compile("\u922e\\?"), "\u2264"),
]


def repair(path: Path) -> None:
    """Apply the pattern rules and report whatever they miss."""
    text = path.read_text(encoding="utf-8")
    before = text
    for pattern, replacement in RULES:
        text = pattern.sub(replacement, text)
    path.write_text(text, encoding="utf-8")
    changed = sum(
        1 for a, b in zip(before.splitlines(), text.splitlines()) if a != b
    )
    leftover = [
        (index + 1, line.strip()[:130])
        for index, line in enumerate(text.splitlines())
        if "\u9225" in line or "\u922e" in line or "\ufffd" in line
    ]
    print(f"{path.name}: {changed} lines changed")
    for line in leftover:
        print("  LEFT:", line)


if __name__ == "__main__":
    for name in ("build_srs_docx.py",):
        repair(ROOT / name)
