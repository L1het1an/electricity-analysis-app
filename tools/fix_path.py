"""Repair the template path in build_srs_docx.py without shell quoting."""

from pathlib import Path

TARGET = Path(__file__).resolve().parent / "build_srs_docx.py"
NEW_LINE = (
    'TEMPLATE_DIR = Path.home() / "Pictures" / "Technical Project" '
    '/ "Technical Project" / "Technical Project" / "Templates"'
)

lines = TARGET.read_text(encoding="utf-8").splitlines()
changed = False
for index, line in enumerate(lines):
    if line.startswith("TEMPLATE_DIR = "):
        lines[index] = NEW_LINE
        changed = True
TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("repaired:", changed)
print(lines[22])
print(lines[23])
