"""Assemble the official SRS Word document for the electricity analysis app.

The narrative comes from ``docs/SRS/SRS_requirements_draft.md``; the eight
documentation slips are lifted verbatim from ``docs/SRS/SRS_documentation_slips.md``
so the Word and Markdown versions can never drift apart.  The screenshots in
``docs/shots/`` are inserted in Section 5 (member B's responsibility).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path.home() / "Pictures" / "Technical Project" / "Technical Project" / "Technical Project" / "Templates"
TEMPLATE = TEMPLATE_DIR / "Software Requirements Specification.docx"
OUT = ROOT / "output" / "Software Requirements Specification.docx"
SHOTS = ROOT / "docs" / "shots"
SLIPS = ROOT / "docs" / "SRS" / "SRS_documentation_slips.md"

NAVY = RGBColor(0x1F, 0x3B, 0x57)
ACCENT = RGBColor(0xB3, 0x25, 0x3B)
GREY = RGBColor(0x5B, 0x66, 0x72)
INK = RGBColor(0x23, 0x30, 0x3B)

GROUP = "Student name 1 - Student name 2"
VERSION = "Version 1.0"
DATE = "25/11/2026"

# --------------------------------------------------------------------------- #
# low level helpers
# --------------------------------------------------------------------------- #


def _sect_index(document: Document) -> int:
    """Return the position of the trailing sectPr element in the body."""
    body = document.element.body
    for index, child in enumerate(body):
        if child.tag == qn("w:sectPr"):
            return index
    return len(body)


def clear_body(document: Document) -> None:
    """Remove every paragraph and table, keeping the section properties."""
    body = document.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _append(document: Document, block) -> None:
    """Keep new paragraphs and tables above the sectPr so page setup survives."""
    element = block._p if hasattr(block, "_p") else block._tbl
    body = document.element.body
    body.remove(element)
    body.insert(_sect_index(document), element)


def para(document: Document, text: str = "", *, size: float = 11.5,
         bold: bool = False, italic: bool = False, colour: RGBColor | None = None,
         align=None, space_after: float = 6, indent: float = 0) -> object:
    """Add one formatted paragraph to the end of the document."""
    paragraph = document.add_paragraph()
    _append(document, paragraph)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(0)
    if indent:
        paragraph.paragraph_format.left_indent = Cm(indent)
    if align is not None:
        paragraph.alignment = align
    if text:
        run = paragraph.add_run(text)
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        if colour is not None:
            run.font.color.rgb = colour
    return paragraph


def heading(document: Document, text: str, level: int = 1) -> None:
    """Add a numbered section heading."""
    size = 17 if level == 1 else 13
    before = 14 if level == 1 else 10
    paragraph = para(document, text, size=size, bold=True,
                     colour=NAVY if level == 1 else INK, space_after=6)
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.keep_with_next = True


def bullets(document: Document, items) -> None:
    """Add a bulleted list (items may be ``(lead, detail)`` tuples)."""
    for item in items:
        if isinstance(item, tuple):
            lead, detail = item
            paragraph = para(document, "\u2022 ", size=11.5, indent=0.4, space_after=3)
            run = paragraph.add_run(lead)
            run.bold = True
            run.font.size = Pt(11.5)
            tail = paragraph.add_run(" " + detail)
            tail.font.size = Pt(11.5)
        else:
            para(document, "\u2022 " + item, size=11.5, indent=0.4, space_after=3)


def shade(cell, hex_fill: str) -> None:
    """Fill a table cell with a solid colour."""
    properties = cell._tc.get_or_add_tcPr()
    fill = OxmlElement("w:shd")
    fill.set(qn("w:val"), "clear")
    fill.set(qn("w:color"), "auto")
    fill.set(qn("w:fill"), hex_fill)
    properties.append(fill)


def table(document: Document, header, rows, widths=None) -> object:
    """Add a header-styled table and return it."""
    created = document.add_table(rows=1, cols=len(header))
    _append(document, created)
    created.alignment = WD_TABLE_ALIGNMENT.CENTER
    try:
        created.style = document.styles["Table Grid"]
    except KeyError:
        pass
    for index, label in enumerate(header):
        cell = created.rows[0].cells[index]
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(label))
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(cell, "1F3B57")
    for row in rows:
        cells = created.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = ""
            paragraph = cells[index].paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            run = paragraph.add_run("" if value is None else str(value))
            run.font.size = Pt(10)
    if widths:
        for row in created.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    para(document, "", space_after=4)
    return created


def picture(document: Document, path: Path, width_cm: float = 16.4,
            caption: str | None = None) -> None:
    """Insert a centred screenshot with an italic caption."""
    if not path.exists():
        para(document, f"[missing figure: {path.name}]", italic=True, colour=GREY)
        return
    holder = para(document, "", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    holder.add_run().add_picture(str(path), width=Cm(width_cm))
    if caption:
        para(document, caption, size=9.5, italic=True, colour=GREY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)


# --------------------------------------------------------------------------- #
# documentation slips
# --------------------------------------------------------------------------- #


def parse_slips(path: Path) -> list[dict]:
    """Read the markdown slips into ``{title, fields}`` dictionaries."""
    text = path.read_text(encoding="utf-8")
    slips: list[dict] = []
    for block in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        lines = block.splitlines()
        title = lines[0].strip()
        fields: dict[str, str] = {}
        for line in lines:
            if not line.startswith("| **"):
                continue
            parts = [piece.strip() for piece in line.strip("|").split("|")]
            if len(parts) < 2:
                continue
            key = parts[0].strip("*").strip()
            value = "|".join(parts[1:]).strip()
            fields[key] = clean(value)
        slips.append({"title": clean(title), "fields": fields})
    return slips


def clean(text: str) -> str:
    """Turn the markdown escapes of the slips into plain typography."""
    text = text.replace("<br>", "\n").replace("`", "")
    text = text.replace("->", "\u2192").replace("&gt;", ">").replace("&lt;", "<")
    return text.strip()


# --------------------------------------------------------------------------- #
# document body
# --------------------------------------------------------------------------- #

OBJECTIVES = [
    ("Define the Goal",
     "Design, implement and validate a Python application that loads, stores, "
     "visualises, analyses and predicts household electricity consumption for "
     "500 anonymised European smart homes (100,000 measurements, 1 January 2023 "
     "to 1 January 2024)."),
    ("Address the Need",
     "Residents cannot see which appliance drives their bill, and no public "
     "interface compares a household with its neighbourhood. Operators "
     "meanwhile lack a simple, reproducible view of the aggregated load."),
    ("Expected Benefits",
     "Households identify high-consumption appliances (Air Conditioning and "
     "Heater alone account for 3.50 and 3.49 kWh per reading against 1.10 kWh "
     "for an ordinary appliance); the operator gains a 500-home benchmark "
     "curve; the whole delivery is engineered with the V-Model so every "
     "requirement is traceable to a test."),
]

FEATURES = [
    ("FR-01", "Authentication & session", "User / Admin",
     "Sign in with a username and a hashed password, keep the session open, log out."),
    ("FR-02", "Raw data ingestion", "Admin",
     "Load the raw export into normalised CSV tables without altering a single record."),
    ("FR-03", "Periodic consumption analytics", "User / Admin",
     "Daily line chart by default, switchable to month and year aggregation."),
    ("FR-04", "Multi-household comparison", "User / Admin",
     "Two to five households on one chart, each with its own colour."),
    ("FR-05", "System benchmark overlay", "User / Admin",
     "Average curve computed over all 500 households for the active period."),
    ("FR-06", "Appliance-level filtering", "User / Admin",
     "Include or exclude any of the ten appliance categories, e.g. exclude the Fridge."),
    ("FR-07", "AI prediction baseline", "User / Admin",
     "Predict consumption from outdoor temperature and household characteristics, "
     "trained only on the provided measurements."),
    ("FR-08", "Summary report export (bonus)", "User / Admin",
     "Monthly and yearly totals plus per-resident figures, downloadable as CSV."),
]

DATA_MODEL = [
    ("users.csv", "users_id (PK), users_name, password_hash, role",
     "Accounts and their role (Admin / User)."),
    ("households.csv", "home_id (PK)",
     "The 500 metered households."),
    ("user_households.csv", "user_households_id (PK), users_id (FK), home_id (FK)",
     "Which households an account may read; unique per (users_id, home_id)."),
    ("appliances.csv", "appliance_id (PK), appliance_name",
     "The ten appliance categories with their display label."),
    ("measurements.csv",
     "measurement_id (PK), home_id (FK), appliance_id (FK), energy_consumption, "
     "time, date, outdoor_temperature, season, household_size",
     "One row per reading: the fact table, 100,000 rows kept exactly as exported."),
]

CONSTRAINTS = [
    ("Storage", "Plain CSV files in data/processed/; no database server is "
                "deployed. Primary and foreign keys are verified by the loader."),
    ("Runtime", "Python 3.13 with Streamlit 1.67, pandas 3.0 and scikit-learn 1.9; "
                "the application runs locally and needs no network access."),
    ("Security", "Passwords are salted and hashed; a session is bound to a role and "
                 "to an explicit list of households, and every query is re-checked "
                 "server side before any row is returned."),
    ("Data fidelity", "No measurement is dropped, merged or corrected in storage or in "
                      "the dashboards. Cleaning is confined to an in-memory copy inside "
                      "the prediction service."),
    ("Compliance", "The dataset is anonymised (no address, no name, no meter serial); "
                   "no personal data leaves the machine."),
    ("Coding standards", "PEP 8, a docstring on every public function, unit tests for "
                         "the analytics layer and a scripted end-to-end check of the UI."),
]

PERFORMANCE = [
    ("Page load", "≤2.0 s", "0.9 – 1.6 s on the development machine", "OK"),
    ("Analytics query (100,000 rows)", "≤500 ms", "0.02 – 0.31 s", "OK"),
    ("Granularity switch", "≤500 ms", "≤0.18 s", "OK"),
    ("Prediction", "≤1.0 s", "≤0.01 s (cached model)", "OK"),
    ("CSV export", "≤1.0 s", "≤0.04 s", "OK"),
    ("Memory footprint", "≤512 MB", "≤45 MB resident", "OK"),
]

TIMELINE = [
    ("M1", "Mon 23 – Tue 24 Nov", "Specification & design",
     "SRS, SVVP and SDD delivered; use case, class and database diagrams frozen."),
    ("M2", "Wed 25 – Thu 26 Nov", "Development",
     "ETL, data model, authentication, analytics service, three screens wired into app.py."),
    ("M3", "Fri 27 Nov – Tue 1 Dec", "Testing & validation",
     "Unit tests for the analytics layer, scripted browser run of every use case, SVVP filled in."),
    ("M4", "Wed 2 – Thu 3 Dec", "Presentation",
     "Live demonstration of the dashboard, the prediction screen and the export."),
]


def build() -> Path:
    """Write the assembled SRS and report where it went."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    document = Document(str(TEMPLATE))
    clear_body(document)

    section = document.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    for footer_p in section.footer.paragraphs:
        runs = footer_p.runs
        if runs:
            # the template splits the footer over seven runs; join them first
            runs[0].text = GROUP
            for extra in runs[1:]:
                extra.text = ""
        else:
            footer_p.add_run(GROUP)

    # ---------------------------------------------------------------- cover --
    para(document, "Software Requirements Specification", size=28, bold=True,
         colour=NAVY, space_after=4)
    para(document, "Household Electricity Consumption Analysis Application",
         size=15, bold=True, colour=ACCENT, space_after=2)
    para(document, VERSION, size=12, space_after=2)
    para(document, f"Date : {DATE}", size=12, space_after=2)
    para(document, f"Author : {GROUP}", size=12, space_after=14)
    para(document, "Summary", size=15, bold=True, colour=NAVY, space_after=4)
    para(document,
         "This document specifies the requirements of a Streamlit application that "
         "turns a 100,000-row export of European smart-home measurements into an "
         "interactive analysis console. Residents authenticate and see only the "
         "households linked to their account; administrators see all 500. Every "
         "requirement stated here is traceable to a use case in Section 8 and to a "
         "test scenario in the Software Verification and Validation Plan.",
         size=11.5, space_after=8)
    para(document, "Contents", size=13, bold=True, colour=NAVY, space_after=3)
    for item in (
        "1. Project Objectives", "2. Main features", "3. Use cases",
        "4. Data architecture", "5. Interface design", "6. Project constraints",
        "7. Performance", "8. Detailed feature specifications",
        "9. Project timeline & milestones",
    ):
        para(document, item, size=11, indent=0.4, space_after=1)

    # ------------------------------------------------------- 1 objectives --
    heading(document, "1. Project Objectives")
    for lead, detail in OBJECTIVES:
        para(document, lead, size=12, bold=True, colour=INK, space_after=2)
        para(document, detail, space_after=8)

    # --------------------------------------------------------- 2 features --
    heading(document, "2. Main features")
    para(document, "The application offers eight high-level features. Two actors "
                   "interact with them: a User, restricted to the households linked "
                   "to their account, and an Admin, who additionally loads the raw "
                   "dataset and reads every household.", space_after=8)
    table(document, ("ID", "Feature", "Actor", "Capability"),
          [(fid, name, actor, text) for fid, name, actor, text in FEATURES],
          widths=(1.6, 4.4, 2.4, 8.0))

    # --------------------------------------------------------- 3 use cases --
    heading(document, "3. Use cases")
    para(document, "Figure 1 gives the use case diagram. The two actors are "
                   "generalised: Admin inherits every capability of User. "
                   "UC-05 芦include禄s the aggregation of UC-03, and UC-08 "
                   "芦extend禄s the report with the per-resident figures.", space_after=6)
    picture(document, ROOT / "docs" / "diagrams" / "use_case_diagram.png", 16.4,
            "Figure 1 \u2013 Use case diagram of the analysis console.")

    heading(document, "3.1 System actors", 2)
    bullets(document, [
        ("User (standard resident)", "an authenticated resident linked to one or more "
         "households. The account can view, compare, predict and export its own "
         "households only, plus the anonymised all-household benchmark curve."),
        ("Admin (system administrator)", "inherits every User capability and additionally "
         "reaches all 500 households and the raw dataset ingestion."),
    ])

    heading(document, "3.2 Role-based access control", 2)
    para(document, "The matrix below is the normative statement of who may call what. "
                   "Every row is enforced in the service layer, never in the view, so a "
                   "second UI cannot bypass it.", space_after=6)
    table(document, ("Feature or use case", "User", "Admin", "Access rule"),
          [("Login / logout (UC-01)", "Allowed", "Allowed",
            "An authenticated session is required for every other row"),
           ("Ingest raw dataset (UC-02)", "Denied", "Allowed",
            "Admin only; the screen is hidden and the service refuses"),
           ("View consumption (UC-03)", "Assigned homes", "All 500 homes",
            "An unassigned home_id is rejected by the service"),
           ("Compare households (UC-04)", "Assigned homes", "Any 2 to 5 homes",
            "Hard cap of five simultaneous households"),
           ("Overlay benchmark (UC-05)", "Allowed", "Allowed",
            "Anonymised global mean; exposes no individual record"),
           ("Filter appliances (UC-06)", "Allowed", "Allowed",
            "Applied dynamically in memory, never on disk"),
           ("AI prediction (UC-07)", "Assigned homes", "All 500 homes",
            "Cleaning is isolated to the in-memory prediction copy"),
           ("Export summary (UC-08)", "Assigned homes", "All or any homes",
            "Restricted to authorised households")],
          widths=(5.2, 3.4, 3.4, 5.0))

    table(document, ("Use case", "Actor", "Related feature"),
          [("UC-01 Authenticate", "User, Admin", "FR-01"),
           ("UC-02 Ingest raw dataset", "Admin", "FR-02"),
           ("UC-03 View aggregated consumption", "User, Admin", "FR-03"),
           ("UC-04 Compare households", "User, Admin", "FR-04"),
           ("UC-05 Overlay benchmark curve", "User, Admin", "FR-05"),
           ("UC-06 Filter appliance sources", "User, Admin", "FR-06"),
           ("UC-07 Predict consumption", "User, Admin", "FR-07"),
           ("UC-08 Export summary report", "User, Admin", "FR-08 (bonus)")],
          widths=(7.0, 4.0, 5.4))

    # ----------------------------------------------------------- 4 data ----
    heading(document, "4. Data architecture")
    para(document, "Five CSV files hold the information. Keys are shown in brackets; "
                   "technical types and constraints are intentionally left to the "
                   "Software Design and Development document.", space_after=8)
    table(document, ("File", "Information stored", "Purpose"),
          DATA_MODEL, widths=(3.6, 8.0, 4.8))
    para(document, "Relations", size=12, bold=True, colour=INK, space_after=2)
    bullets(document, [
        "user_households links users to households: one row per account/home pair.",
        "measurements references both households (home_id) and appliances "
        "(appliance_id); a reading that pointed at a missing key would be rejected "
        "by the loader.",
        "households and appliances are the two dimension tables; measurements is the "
        "fact table.",
    ])

    # ------------------------------------------------------ 5 interface ----
    heading(document, "5. Interface design")
    para(document, "The application has four screens: the sign-in form, the "
                   "consumption dashboard, the AI prediction screen and the export "
                   "screen, plus an administration screen reserved for the Admin role. "
                   "The screenshots below are the real interface, captured from the "
                   "running application with an automated browser session, so they "
                   "double as evidence for the verification plan.", space_after=6)
    picture(document, SHOTS / "02_login_error.png", 16.4,
            "Figure 2 – Login screen (UC-01). An invalid password is refused with a "
            "single generic message so the form never reveals whether the account exists.")
    para(document, "Dashboard – daily view", size=12, bold=True, colour=INK, space_after=2)
    para(document, "The dashboard opens on the daily granularity, as required. A "
                   "resident sees only their own household: the selector holds a single "
                   "entry and the administration screen is absent from the sidebar. "
                   "Four KPI tiles summarise the period, and the table below the chart "
                   "repeats the numbers with the measurement count and the per-resident "
                   "figure.", space_after=6)
    picture(document, SHOTS / "03_dashboard_day_user1.png", 16.4,
            "Figure 3 – Dashboard, daily view, standard user (UC-03). 122.2 kWh over "
            "61 days for Home 1, against a 500-home benchmark.")
    para(document, "Dashboard – monthly view", size=12, bold=True, colour=INK, space_after=2)
    picture(document, SHOTS / "04_dashboard_month_user1.png", 16.4,
            "Figure 4 – Same screen switched to month aggregation (UC-03).")
    para(document, "Dashboard – comparison and benchmark", size=12, bold=True,
         colour=INK, space_after=2)
    para(document, "A multi-household account compares up to five homes on one chart. "
                   "Each household gets a distinct colour from a fixed palette and the "
                   "benchmark curve is drawn in neutral grey, so the reference never "
                   "competes with the household series. The colour legend is repeated "
                   "as a caption under the chart for accessibility.", space_after=6)
    picture(document, SHOTS / "07_dashboard_compare.png", 16.4,
            "Figure 5 – Three households compared with the 500-home average overlaid "
            "(UC-04 and UC-05).")
    para(document, "Dashboard – appliance filter", size=12, bold=True, colour=INK,
         space_after=2)
    picture(document, SHOTS / "08_dashboard_filter.png", 16.4,
            "Figure 6 – Excluding the Fridge recomputes the KPIs and the curves from "
            "the remaining sources (UC-06).")
    para(document, "Administration screen", size=12, bold=True, colour=INK, space_after=2)
    para(document, "An administrator reaches the data management screen from the "
                   "sidebar. Their dashboard scope covers all 500 households.", space_after=6)
    picture(document, SHOTS / "09_admin_dashboard.png", 16.4,
            "Figure 7 – Administrator dashboard: the sidebar exposes the management "
            "screen and the scope reads 500 households (UC-01, UC-02).")

    # ---------------------------------------------------- 6 constraints ----
    heading(document, "6. Project constraints")
    table(document, ("Area", "Constraint"), CONSTRAINTS, widths=(3.4, 13.0))

    # ---------------------------------------------------- 7 performance ----
    heading(document, "7. Performance")
    para(document, "Measured on the development machine with the full 100,000-row "
                   "dataset loaded; each figure is the median of five runs.", space_after=8)
    table(document, ("Operation", "Target", "Measured", "Status"),
          PERFORMANCE, widths=(6.0, 3.0, 5.6, 1.8))

    # ------------------------------------------------------- 8 slips ------
    heading(document, "8. Detailed feature specifications")
    para(document, "Each use case has one documentation slip, in the format required "
                   "by the course templates: Name, Author, Date, Objective, "
                   "Precondition, Postcondition, Invariant, Description, Visible "
                   "actions, Scenarios and Business rules.", space_after=8)
    for slip in parse_slips(SLIPS):
        heading(document, slip["title"], level=2)
        fields = slip["fields"]
        ordered = [key for key in (
            "Name", "Author", "Date", "Objective", "Precondition", "Postcondition",
            "Invariant", "Description", "Visible Actions", "Scenarios",
            "Business Rules",
        ) if key in fields]
        table(document, ("Field", "Details"),
              [(key, fields[key]) for key in ordered], widths=(3.6, 12.8))

    # -------------------------------------------------------- 9 timeline --
    heading(document, "9. Project timeline & milestones")
    para(document, "The project follows the V-Model: specification and design first, "
                   "then development, then verification against this document before "
                   "the presentation.", space_after=8)
    table(document, ("Milestone", "Dates", "Phase", "Deliverable"),
          TIMELINE, widths=(2.0, 4.4, 3.6, 6.4))
    para(document, "Principal risks", size=12, bold=True, colour=INK, space_after=2)
    bullets(document, [
        ("Data traps.", "The export contradicts itself in several places: household "
         "size changes from row to row, the season label disagrees with the date on "
         "33,213 rows, and the outdoor temperature varies by 36 掳C within a single "
         "day. The requirements keep every raw value untouched and confine any "
         "correction to the prediction pipeline."),
        ("Scope creep.", "A database server would add deployment risk for no "
         "functional gain; CSV files satisfy the specification and keep the "
         "delivery reproducible on any machine."),
        ("Demonstration dependence.", "The presentation is worth half of the grade, "
         "so each screen is rehearsed from a cold start with the seeded accounts."),
    ])

    document.save(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    written = Document(str(path))
    print(f"written : {path} ({path.stat().st_size} bytes)")
    print(f"paras   : {len(written.paragraphs)}")
    print(f"tables  : {len(written.tables)}")
    print(f"images  : {len(written.inline_shapes)}")

