"""Fix the en dashes whose surrounding spaces were eaten by the repair regex."""

import re
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "build_srs_docx.py"

text = TARGET.read_text(encoding="utf-8")

# "Figure 2 –Login" -> "Figure 2 – Login";  "Dashboard –daily" -> "Dashboard – daily"
text = re.sub("\u2013(?=[A-Za-z0-9])", "\u2013 ", text)
# "Mon 23 –Tue" keeps a space before the dash already; guard double spaces
text = re.sub("\u2013  +", "\u2013 ", text)

TARGET.write_text(text, encoding="utf-8")

for index, line in enumerate(text.splitlines(), 1):
    if "\u2013" in line or "\u2022" in line or "\u2264" in line:
        print(index, line.strip()[:120])
