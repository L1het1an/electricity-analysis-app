"""Assemble the official Software Design and Development (SDD) Word document.

The narrative is lifted from ``docs/SDD/data_schema.md`` and the two PlantUML
diagrams in ``docs/diagrams/`` so the Word deliverable can never drift away from
the design sources, exactly like ``build_srs_docx.py`` does for the SRS.

Run from the project root::

    python tools/build_sdd_docx.py

Output: ``output/Software Design and Development.docx``
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "Software Design and Development.docx"
CLASS_DIAGRAM = ROOT / "docs" / "diagrams" / "class_diagram.png"
DATABASE_DIAGRAM = ROOT / "docs" / "diagrams" / "database_diagram.png"

NAVY = RGBColor(0x1F, 0x3B, 0x57)
ACCENT = RGBColor(0xB3, 0x25, 0x3B)
GREY = RGBColor(0x5B, 0x66, 0x72)
INK = RGBColor(0x23, 0x30, 0x3B)

GROUP = "Student name 1 - Student name 2 - Student name 3"
VERSION = "Version 1.0"
DATE = "27/11/2026"

# --------------------------------------------------------------------------- #
# low level helpers
# --------------------------------------------------------------------------- #


def para(
    document: Document,
    text: str = "",
    *,
    size: float = 11.5,
    bold: bool = False,
    italic: bool = False,
    colour: RGBColor | None = None,
    align=None,
    space_after: float = 6,
    style: str | None = None,
):
    """Add one formatted paragraph."""
    paragraph = document.add_paragraph(style=style) if style else document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(0)
    if align is not None:
        paragraph.alignment = align
    if text:
        run = paragraph.add_run(text)
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = "Calibri"
        run.font.color.rgb = colour or INK
    return paragraph


def heading(document: Document, text: str, *, level: int = 1) -> None:
    """Add a numbered section heading in the house style."""
    sizes = {0: 26, 1: 17, 2: 13.5}
    colour = NAVY if level == 0 else (NAVY if level == 1 else GREY)
    space_before = {0: 0, 1: 18, 2: 12}[level]
    paragraph = para(
        document,
        text,
        size=sizes[level],
        bold=True,
        colour=colour,
        space_after=8,
    )
    paragraph.paragraph_format.space_before = Pt(space_before)
    if level == 1:
        _bottom_border(paragraph)


def _bottom_border(paragraph) -> None:
    """Draw a thin accent rule under a heading paragraph."""
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "B3253B")
    borders.append(bottom)
    p_pr.append(borders)


def figure(document: Document, path: Path, caption: str, width_cm: float = 16.0) -> None:
    """Insert an image centred with a caption underneath."""
    if not path.exists():
        para(document, f"[missing figure: {path.name}]", italic=True, colour=ACCENT)
        return
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(path), width=Cm(width_cm))
    caption_paragraph = para(
        document, caption, size=9.5, italic=True, colour=GREY, align=WD_ALIGN_PARAGRAPH.CENTER
    )
    caption_paragraph.paragraph_format.space_after = Pt(12)


def table(document: Document, headers: list[str], rows: list[list[str]], widths=None) -> None:
    """Insert a clean three-line table with a navy header row."""
    grid = document.add_table(rows=1, cols=len(headers))
    grid.style = "Table Grid"
    grid.alignment = WD_TABLE_ALIGNMENT.CENTER
    grid.autofit = widths is None

    header_cells = grid.rows[0].cells
    for index, label in enumerate(headers):
        header_cells[index].text = ""
        run = header_cells[index].paragraphs[0].add_run(label)
        run.font.bold = True
        run.font.size = Pt(10)
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _shade(header_cells[index], "1F3B57")

    for row in rows:
        cells = grid.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = ""
            run = cells[index].paragraphs[0].add_run(str(value))
            run.font.size = Pt(9.5)
            run.font.name = "Calibri"
            run.font.color.rgb = INK

    if widths:
        for row in grid.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)

    para(document, "", space_after=8)


def _shade(cell, hex_colour: str) -> None:
    """Fill a table cell background."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), hex_colour)
    cell._tc.get_or_add_tcPr().append(shading)


def bullets(document: Document, items: list[str]) -> None:
    """Add a bullet list."""
    for item in items:
        bullet = document.add_paragraph(style="List Bullet")
        bullet.paragraph_format.space_after = Pt(3)
        run = bullet.add_run(item)
        run.font.size = Pt(11)
        run.font.name = "Calibri"
        run.font.color.rgb = INK


def page_break(document: Document) -> None:
    """Force a page break."""
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# --------------------------------------------------------------------------- #
# content
# --------------------------------------------------------------------------- #

CLASS_ROWS = [
    ["User", "src/models.py", "Authenticated account; owns its household scope.",
     "verify_password(), is_admin(), can_access_home()"],
    ["Household", "src/models.py", "Anonymised smart home (identifier only).", "—"],
    ["Appliance", "src/models.py", "Metered appliance category.", "—"],
    ["Measurement", "src/models.py", "One raw measurement row, values kept verbatim.", "—"],
    ["CSVDataRepository", "src/data/repository.py",
     "ETL from the cp1252 export, table loading, PK/FK/NN/UN validation.",
     "is_initialized(), ingest_raw_csv(), load_*(), validate_referential_integrity()"],
    ["AuthService", "src/services/auth_service.py",
     "Credential check and deny-by-default RBAC guards.",
     "login(), get_authorized_home_ids(), can_access_home(), ensure_home_access()"],
    ["AnalyticsService", "src/services/analytics_service.py",
     "Day/month/year aggregation, ≤5-household comparison, global average, filters.",
     "authorize(), aggregate(), system_average(), kpi_table()"],
    ["PredictionService", "src/services/prediction_service.py",
     "Statsmodels OLS + scikit-learn baselines on an isolated in-memory copy.",
     "train_baselines(), predict()"],
    ["ReportExportService", "src/services/export_service.py",
     "Monthly/yearly bonus report with total and per-resident consumption.",
     "build_report(), to_csv()"],
]

SCHEMA_ROWS = [
    ["users.csv", "users_id", "int", "PK", "Unique account identifier"],
    ["", "users_name", "str", "UN, NN", "Login name"],
    ["", "password_hash", "str", "NN", "SHA-256 digest of the password"],
    ["", "role", "str", "NN", 'Role: "Admin" or "User"'],
    ["households.csv", "home_id", "int", "PK, NN", "Anonymised smart home identifier"],
    ["user_households.csv", "user_households_id", "int", "PK", "Junction record identifier"],
    ["", "users_id", "int", "FK users.users_id, NN", "Linked account"],
    ["", "home_id", "int", "FK households.home_id, NN", "Linked household"],
    ["", "(users_id, home_id)", "—", "UN", "A link cannot be granted twice"],
    ["appliances.csv", "appliance_id", "int", "PK", "Appliance identifier (1–10)"],
    ["", "appliance_name", "str", "UN, NN", "Appliance category name"],
    ["measurements.csv", "measurement_id", "int", "PK", "Surrogate key (1–100 000)"],
    ["", "home_id", "int", "FK households.home_id, NN", "Owning household"],
    ["", "appliance_id", "int", "FK appliances.appliance_id, NN", "Metered appliance"],
    ["", "energy_consumption", "float", "NN", "Consumption in kWh, raw value"],
    ["", "time", "str", "NN", "Measurement time (HH:MM, 24-hour)"],
    ["", "date", "str", "NN", "Measurement date (YYYY-MM-DD)"],
    ["", "outdoor_temperature", "float", "NN", "Raw outdoor temperature in °C"],
    ["", "season", "str", "NN", "Raw season label (Winter/Summer/Fall/Spring)"],
    ["", "household_size", "int", "NN", "Raw recorded household size"],
]


def build_title_page(document: Document) -> None:
    """Render the cover block required by the official template."""
    para(document, "", space_after=60)
    heading(document, "Software Design and Development", level=0)
    para(document, "Household Electricity Consumption Analysis", size=14, colour=GREY, space_after=4)
    para(document, VERSION, size=12, colour=ACCENT, bold=True, space_after=2)
    para(document, f"Date : {DATE}", size=11, colour=GREY, space_after=2)
    para(document, GROUP, size=11, colour=GREY, space_after=36)
    para(
        document,
        "Master of Science – Software Engineering & Digital Transformation",
        size=10,
        colour=GREY,
        space_after=0,
    )


def build_summary(document: Document) -> None:
    """Render the template's summary page."""
    heading(document, "Summary", level=1)
    bullets(document, ["Class diagram", "Database diagram"])
    para(document, "", space_after=10)
    para(
        document,
        "This document is the design blueprint produced during the Design phase of the "
        "V-Model. It describes the object model of the application (chapter 1) and the "
        "normalised relational schema that stores the 100 000 delivered measurements as "
        "five CSV tables (chapter 2). Source diagrams are PlantUML files kept in "
        "docs/diagrams/src, so the figures and this document are regenerated together.",
        size=11,
    )


def build_class_chapter(document: Document) -> None:
    """Chapter 1 – class diagram and architecture."""
    heading(document, "1. Class diagram", level=1)
    figure(document, CLASS_DIAGRAM, "Figure 1 – Application class diagram (UML, PlantUML source in docs/diagrams/src)")

    para(
        document,
        "The application is organised in four layers. Data-layer classes are the only ones "
        "that touch the file system; services hold the business rules; the ui modules render "
        "Streamlit screens and never compute aggregates themselves; models are dependency-free "
        "value objects shared by every layer.",
        size=11,
    )

    heading(document, "1.1 Class responsibilities", level=2)
    table(
        document,
        ["Class", "Module", "Responsibility", "Key methods"],
        CLASS_ROWS,
        widths=[2.8, 3.2, 5.0, 5.0],
    )

    heading(document, "1.2 Design decisions", level=2)
    bullets(
        document,
        [
            "Encapsulation: User keeps the password digest private; verification exposes only "
            "a boolean through verify_password(), which delegates to hmac.compare_digest so the "
            "comparison is constant-time.",
            "Single source of authority: CSVDataRepository.load_*() are the only entry points to "
            "the CSV tables, so the cp1252 decoding rule and the column order live in one place.",
            "Separation of rules and rendering: AuthService never imports Streamlit and the views "
            "never decide access rights, which is what makes the RBAC guards unit-testable.",
            "Composition: each service receives the repository through its constructor, so a test "
            "or a future database backend can substitute it without touching the callers.",
            "Dependency direction is one-way: ui → services → data → models. No layer imports a "
            "layer above it, which keeps the modules replaceable.",
        ],
    )


def build_database_chapter(document: Document) -> None:
    """Chapter 2 – relational schema and integrity rules."""
    heading(document, "2. Database diagram", level=1)
    figure(
        document,
        DATABASE_DIAGRAM,
        "Figure 2 – Relational schema of the five CSV tables (PK, FK, UN, NN)",
    )

    para(
        document,
        "The delivered export is a single denormalised CSV. Per the course requirement it is "
        "stored in files rather than in a database server, but the relational principles of "
        "primary keys, foreign keys, uniqueness and referential integrity are applied exactly as "
        "they would be in a relational database.",
        size=11,
    )

    heading(document, "2.1 Table definitions", level=2)
    table(
        document,
        ["Table", "Column", "Type", "Constraint", "Description"],
        SCHEMA_ROWS,
        widths=[3.0, 3.2, 1.5, 4.2, 4.1],
    )

    heading(document, "2.2 Relationships and multiplicity", level=2)
    bullets(
        document,
        [
            "Users (1) ↔ User_Households (0..*): one account may be linked to zero, one or many "
            "households; an administrator needs no explicit link because the role grants global "
            "access.",
            "Households (1) ↔ User_Households (0..*): one household may be shared by several users.",
            "Households (1) ↔ Measurements (1..*): each measurement belongs to exactly one "
            "household; a household has many measurements.",
            "Appliances (1) ↔ Measurements (1..*): each measurement records exactly one appliance "
            "category; each category appears in many measurements.",
        ],
    )

    heading(document, "2.3 Referential integrity rules", level=2)
    bullets(
        document,
        [
            "Every users_id in user_households.csv must exist in users.csv.",
            "Every home_id in user_households.csv and measurements.csv must exist in households.csv.",
            "Every appliance_id in measurements.csv must exist in appliances.csv.",
            "Primary keys are unique, unique constraints are enforced in application code and no "
            "mandatory column may be empty.",
            "validate_referential_integrity() returns the verdict of these checks and is executed "
            "from the administration screen (DATA-02).",
        ],
    )

    heading(document, "2.4 Normalisation rationale", level=2)
    para(
        document,
        "Splitting the export into five tables removes three levels of redundancy. The appliance "
        "name is written once in appliances.csv instead of 100 000 times, so renaming a category "
        "becomes a single-row update. Account-to-household permissions live in a junction table, "
        "which expresses a many-to-many relationship that a flat file cannot represent. Household "
        "identity is stored once, so a measurement cannot refer to a home that does not exist. The "
        "measurements table only keeps numeric facts and foreign keys, which is the third normal "
        "form shape of the fact table.",
        size=11,
    )
    para(
        document,
        "measurement_id is a surrogate key on purpose: the delivered export contains a few rows "
        "sharing the same (home, date, time, appliance) combination, and the surrogate key lets "
        "those raw rows be preserved without violating the primary key — which the specification "
        "requires, since no record may be dropped.",
        size=11,
    )

    heading(document, "2.5 Storage boundary", level=2)
    para(
        document,
        "Ingestion reads the raw file with encoding cp1252 (the header contains a raw ° byte) and "
        "copies every value verbatim: no outlier is removed, no season is recomputed and no "
        "household size is harmonised. Cleaning exists only inside the prediction pipeline, on an "
        "in-memory copy that is never written back to data/processed (NFR-02).",
        size=11,
    )


def build_appendix(document: Document) -> None:
    """Appendix – coding standards required by the project-management lecture."""
    page_break(document)
    heading(document, "Appendix A – Coding standards", level=1)
    para(
        document,
        "The rules below are enforced across the code base and are visible in the modules "
        "described in chapter 1.",
        size=11,
    )
    table(
        document,
        ["Rule", "Application in the project"],
        [
            ["PEP 8 naming", "snake_case for functions, variables and modules; PascalCase for "
                             "classes; UPPER_CASE for module constants."],
            ["Docstrings", "Every module, class and public function carries a docstring stating "
                           "purpose, arguments, return value and raised exceptions."],
            ["Function size", "Functions stay below 50 lines; long screens are split into one "
                              "private helper per section."],
            ["Single responsibility", "One module per concern: models, repository, services, views."],
            ["Type hints", "Public signatures are annotated (list[int], User | None) and use "
                           "from __future__ import annotations."],
            ["No global state", "Dependencies are injected through constructors; Streamlit session "
                                "state is confined to the view layer."],
            ["Tests", "pytest suites are named after the SVVP case identifiers so each requirement "
                      "is traceable to an automated test."],
        ],
        widths=[4.0, 12.0],
    )


def main() -> None:
    """Build the document and save it to output/."""
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)

    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    build_title_page(document)
    page_break(document)
    build_summary(document)
    page_break(document)
    build_class_chapter(document)
    page_break(document)
    build_database_chapter(document)
    build_appendix(document)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT)
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
