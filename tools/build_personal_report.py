"""Build the Personal Report for member B (analytics, UI and router).

The document follows the six sections of the ESIGELEC/UESTC template and only
states facts that are verifiable in the repository: line counts, test counts and
the recorded browser logs.
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path.home() / "Pictures" / "Technical Project" / "Technical Project" / "Technical Project" / "Templates" / "Personal report.docx"
OUTPUT = ROOT / "output" / "Personal Report.docx"
SHOTS = ROOT / "docs" / "shots"

STUDENT = "Tan Haowen"
VERSION = "Version 1.0"
DATE = "27/11/2026"

NAVY = RGBColor(0x1F, 0x3B, 0x57)
ACCENT = RGBColor(0xB3, 0x25, 0x3B)
GREY = RGBColor(0x5B, 0x66, 0x72)
INK = RGBColor(0x23, 0x30, 0x3B)


# --------------------------------------------------------------------------- #
# Word helpers
# --------------------------------------------------------------------------- #
def _sect_index(document: Document) -> int:
    """Return the position of the section properties in the body."""
    for index, child in enumerate(document.element.body):
        if child.tag == qn("w:sectPr"):
            return index
    return len(document.element.body)


def clear_body(document: Document) -> None:
    """Remove every paragraph and table while keeping the section properties."""
    body = document.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _append(document: Document, block) -> None:
    """Move a freshly built paragraph or table just before the section properties."""
    element = block._p if hasattr(block, "_p") else block._tbl
    body = document.element.body
    body.remove(element)
    body.insert(_sect_index(document), element)


def para(document: Document, text: str = "", *, size: float = 11.5, bold: bool = False,
         italic: bool = False, colour: RGBColor | None = None, space_after: float = 6,
         indent: float = 0.0, align=None) -> object:
    """Append one body paragraph."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(0)
    if indent:
        paragraph.paragraph_format.left_indent = Cm(indent)
    if align is not None:
        paragraph.alignment = align
    if text:
        run = paragraph.add_run(text)
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = "Calibri"
        if colour is not None:
            run.font.color.rgb = colour
    _append(document, paragraph)
    return paragraph


def heading(document: Document, text: str, level: int = 1) -> None:
    """Append a numbered or plain heading."""
    size = 17 if level == 1 else 13
    colour = NAVY if level == 1 else INK
    space_before = 14 if level == 1 else 10
    paragraph = para(document, text, size=size, bold=True, colour=colour,
                     space_after=5)
    paragraph.paragraph_format.space_before = Pt(space_before)


def bullets(document: Document, items) -> None:
    """Append a bulleted list; items may be (lead, detail) tuples."""
    for item in items:
        if isinstance(item, tuple):
            lead, detail = item
            paragraph = para(document, "\u2022 ", size=11.5, indent=0.4, space_after=3)
            run = paragraph.add_run(lead)
            run.font.bold = True
            run.font.size = Pt(11.5)
            run.font.name = "Calibri"
            run.font.color.rgb = INK
            tail = paragraph.add_run(" \u2014 " + detail)
            tail.font.size = Pt(11.5)
            tail.font.name = "Calibri"
        else:
            para(document, "\u2022 " + item, size=11.5, indent=0.4, space_after=3)


def shade(cell, hex_fill: str) -> None:
    """Fill a table cell with a solid colour."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn("w:shd"), {qn("w:val"): "clear",
                                          qn("w:color"): "auto",
                                          qn("w:fill"): hex_fill})
    tc_pr.append(shd)


def table(document: Document, header, rows, widths=None) -> None:
    """Append a table with a dark header row."""
    block = document.add_table(rows=1, cols=len(header))
    block.style = document.styles["Table Grid"] if "Table Grid" in [
        style.name for style in document.styles] else None
    block.autofit = False
    for index, label in enumerate(header):
        cell = block.rows[0].cells[index]
        cell.text = ""
        run = cell.paragraphs[0].add_run(label)
        run.font.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.name = "Calibri"
        shade(cell, "1F3B57")
    for row in rows:
        cells = block.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = ""
            run = cells[index].paragraphs[0].add_run(str(value))
            run.font.size = Pt(10)
            run.font.name = "Calibri"
    if widths:
        for row in block.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    _append(document, block)
    para(document, "", size=6, space_after=4)


def title_block(document: Document) -> None:
    """Write the cover block that the template expects."""
    para(document, "Personal Report", size=28, bold=True, colour=NAVY, space_after=4)
    para(document, STUDENT, size=15, bold=True, colour=ACCENT, space_after=4)
    para(document, VERSION, size=11.5, colour=GREY, space_after=2)
    para(document, f"Date : {DATE}", size=11.5, colour=GREY, space_after=10)
    para(document, "Summary", size=15, bold=True, colour=NAVY, space_after=4)
    para(document,
         "This report covers my contribution to the Household Electricity Consumption "
         "Analysis project as member B: the analytics service, the Streamlit "
         "dashboard, and the main application router that mounts every team member's "
         "screen into one application. I also produced the official Software "
         "Requirements Specification in Word and the browser evidence that supports "
         "the verification plan. The figures quoted below come from the repository "
         "and from the recorded browser logs, not from memory.", space_after=12)


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def section_overview(document: Document) -> None:
    """Section 1 - the project context and its subject."""
    heading(document, "1. Project overview")
    para(document,
         "The client is a utility operator that collects smart-meter readings from 500 "
         "anonymised households in Europe. The provided dataset is a single CSV export "
         "of 100,000 readings taken between 1 January 2023 and 1 January 2024. Each row "
         "records one appliance of one household at one instant: the energy consumed in "
         "kWh, the outdoor temperature, the season and the declared household size. Ten "
         "appliance categories appear, from a fridge at roughly 0.30 kWh per reading up "
         "to air conditioning and heating at roughly 3.50 kWh.")
    para(document,
         "The application answers a simple need that the raw file cannot: a resident has "
         "no way to see which of their appliances drives the bill, and no way to compare "
         "their household with the neighbourhood. The client asked for a Python "
         "application where a resident signs in, sees only their own households, reads "
         "the consumption per day, month or year, compares up to five households on one "
         "chart, overlays the city-wide average, filters appliance sources, asks an AI "
         "model to predict consumption from a weather forecast, and exports a monthly or "
         "yearly summary. Administrators see all 500 households and load the dataset.")
    table(document, ("Decision", "Why it was taken"),
          [("Streamlit as the UI framework", "Python only, no separate front end to "
            "maintain, and the whole team can read the code"),
           ("Six normalised CSV tables", "The project brief fixes CSV files as the "
            "storage mechanism; normalising keeps referential integrity checkable"),
           ("Raw values preserved on disk", "Non-functional requirement NFR-02: cleaning "
            "happens in memory inside the AI pipeline only"),
           ("One router module", "Each member owns exactly one render function, so three "
            "branches can be merged without touching each other's screens")],
          widths=(5.2, 12.2))


def section_role(document: Document) -> None:
    """Section 2 - role and tasks."""
    heading(document, "2. Role and responsibilities")
    para(document,
         "My role was analytics, visualisation and main interface integration. Concretely "
         "I owned four deliverables.")

    heading(document, "2.1 Analytics service", 2)
    para(document, "src/services/analytics_service.py, 344 lines.")
    bullets(document, [
        ("Aggregation", "one service returns consumption per day, per month or per year, "
         "grouped by household and filtered in the same call"),
        ("Comparison", "between two and five households are drawn together, each with a "
         "fixed colour taken from a palette of five"),
        ("Benchmark", "the system average is always computed over all 500 households, "
         "whatever the signed-in user may see, so the reference curve never leaks an "
         "individual record"),
        ("Authorisation", "an UnauthorizedHomeError is raised in the service layer, not in "
         "the view, so a second user interface could not bypass it"),
        ("KPIs", "total kWh, number of periods, mean per period, number of measurements, "
         "number of days, mean household size and kWh per resident"),
    ])

    heading(document, "2.2 Dashboard view", 2)
    para(document, "src/ui/dashboard_view.py, 283 lines.")
    bullets(document, [
        ("Controls", "granularity radio, household multiselect capped at five, appliance "
         "multiselect, benchmark overlay checkbox and a period slider"),
        ("Chart", "a Vega-Lite line chart with a scale domain fixed by the service, which "
         "is the only reliable way to keep a household the same colour when the selection "
         "changes"),
        ("Detail table", "a pivot of the same aggregation, downloadable as CSV"),
        ("Readability", "the colour legend is repeated as a caption under the chart, "
         "because the Vega legend truncates long labels"),
    ])

    heading(document, "2.3 Main router and integration", 2)
    para(document, "app.py, the only module that decides which screen runs.")
    para(document,
         "Member C delivered the AI prediction and the export screens as two render "
         "functions with the same signature as mine: "
         "(service, user, authorized_homes). Because the contract was respected, the "
         "integration took three edits: import the two views, instantiate the two "
         "services from the same repository, and add the two labels to the sidebar. The "
         "administrator entry appears only for the Admin role. After merging member C's "
         "branch, the full repository ran 38 tests with no failure.")

    heading(document, "2.4 Documentation and evidence", 2)
    bullets(document, [
        ("SRS in Word", "17 pages, 15 tables, 7 figures, built from the official ESIGELEC "
         "template: nine chapters, the RBAC matrix in 3.2, the data architecture in 3.3, "
         "the real screenshots in chapter 5 and the eight documentation slips in chapter 8"),
        ("Screenshots", "12 browser screenshots captured from the running application with "
         "an automated Playwright session"),
        ("Verification logs", "drive_log.json (9 checks) and router_log.json (16 checks) "
         "recorded from the same session, both with zero JavaScript errors"),
        ("Unit tests", "21 tests for the analytics service: role-based access, "
         "aggregation, appliance filtering, comparison, KPIs and the read-only guarantee"),
    ])


def section_difficulties(document: Document) -> None:
    """Section 3 - technical, management and human difficulties."""
    heading(document, "3. Difficulties encountered")

    heading(document, "3.1 Technical difficulties", 2)
    bullets(document, [
        ("The dataset contradicts its own column names",
         "500 households out of 500 declare more than one household size, so the column "
         "cannot be a household attribute. The season column is a mechanical mapping of "
         "the month: 33,213 rows disagree with the date. The temperature column changes "
         "between two readings of the same household on the same day, so it carries no "
         "signal at all. We decided to preserve the raw values on disk, document the three "
         "anomalies, and expose the household size as an administrator-entered attribute "
         "instead of trusting the export."),
        ("Aggregation returning the wrong shape",
         "pandas 3 returns a Series where the earlier code expected a DataFrame once the "
         "grouping keys change, which broke the day/month/year switch silently for one "
         "granularity and loudly for the others. The fix was to build every aggregation "
         "with as_index=False and to pin the derived date columns to int64 before any "
         "merge."),
        ("Keeping a household the same colour",
         "Vega-Lite colours by the values present in the data, so filtering a household out "
         "re-assigns the colours of the others. The service now exposes a colour map that "
         "the view passes as an explicit scale domain and range."),
        ("Streamlit's data editor",
         "the household register let the administrator type a resident count, but the value "
         "never reached the CSV. Streamlit returns the frame it sent, never the edited one; "
         "the edited values only exist in the widget state. Two further problems followed: "
         "the widget had to be re-keyed after every save, otherwise an identical second "
         "edit produced no event, and a single click selects a cell without entering edit "
         "mode, so an automated browser test typed into nothing for two hours before we "
         "instrumented the DOM and saw that no input element existed."),
    ])

    heading(document, "3.2 Project management difficulties", 2)
    bullets(document, [
        ("Three parallel branches on one repository",
         "our first commit was based on a three-day-old main, which meant the first push "
         "would have reverted member C's work. Merging origin/main first was the only safe "
         "order, and it succeeded without conflict precisely because the router file was "
         "owned by exactly one person."),
        ("Two versions of the SRS",
         "member C wrote a markdown draft while I assembled the official Word document. We "
         "kept the Word file as the deliverable and imported the one section he had written "
         "better than me: the role-based access control matrix."),
        ("An unreliable network for Git",
         "the global Git configuration pointed at a local proxy that was not running, so "
         "every push failed with a TLS error. Bypassing the proxy for a single command "
         "(-c http.proxy=) proved that GitHub was reachable directly."),
    ])

    heading(document, "3.3 Human difficulties", 2)
    para(document,
         "The main difficulty was not technical but about agreeing on a contract early. We "
         "spent the first session arguing about the data model, which felt like lost time "
         "and turned out to be the best decision of the project: once the five tables and "
         "the render signature (service, user, authorized_homes) were fixed, the three "
         "branches merged without a single conflict. The lesson is that on a three-person "
         "project the interface contract deserves more attention than the implementation.")


def section_achievements(document: Document) -> None:
    """Section 4 - what was learned."""
    heading(document, "4. Achievements and takeaways")
    bullets(document, [
        ("Data engineering is mostly suspicion",
         "the most valuable output of this project is a list of three claims the dataset "
         "makes that are false. Reading a CSV carefully is a skill, and the decision to "
         "preserve the raw rows instead of silently cleaning them is what makes the "
         "anomalies auditable."),
        ("Separating the service from the view",
         "putting the authorisation check in the service, not in the dashboard, is what let "
         "me hand the same service to two interfaces without duplicating a single rule."),
        ("pandas is not a spreadsheet",
         "the shape of a groupby result depends on the grouping keys and on the pandas "
         "version. Writing the tests first would have caught the granularity bug on the "
         "day it appeared."),
        ("Streamlit is fast to build and slow to test",
         "a screen that takes twenty lines to write needs a browser automation script to be "
         "verified. Our Playwright session is now the only reproducible proof that the "
         "screens work, and it found bugs that the unit tests could not see."),
        ("English technical writing",
         "assembling a seventeen-page specification in a foreign language taught me that a "
         "requirement is only useful if it names its actor, its trigger and its expected "
         "result in one sentence."),
    ])


def section_next(document: Document) -> None:
    """Section 5 - what remains and what would be done differently."""
    heading(document, "5. What's next to the project?")
    para(document, "Have we met the client's needs? Almost all of them.")
    table(document, ("Client requirement", "Status on 27 November 2026"),
          [("Load the CSV export", "Done, single batch loader with referential checks"),
           ("Default daily view", "Done, the dashboard opens on Day"),
           ("Day / month / year aggregation", "Done, one service, three granularities"),
           ("Compare up to 5 households with distinct colours", "Done, hard cap of five"),
           ("Overlay the city-wide average", "Done, always computed over 500 homes"),
           ("Filter appliance sources", "Done, computed in memory"),
           ("AI prediction from weather and household features", "Done, two baselines "
            "(OLS and gradient boosting), trained only on the provided data"),
           ("Monthly / yearly report with total and per-resident figures", "Done, "
            "downloadable as CSV"),
           ("Sign-in and role separation", "Done, session based"),
           ("Interactive dataset loading screen", "Partial, the loader exists as a script "
            "and the administrator screen is being finalised by member A")],
          widths=(8.0, 9.4))

    para(document, "What I would improve, and what I would do differently with today's "
                   "experience:", space_after=4)
    bullets(document, [
        ("Move to a real database",
         "six CSV files are enough for 100,000 rows, and the brief required them, but a "
         "permanent system needs indexes on (home_id, date) and a transaction around the "
         "dataset reload."),
        ("Test the browser flow from day one",
         "the data-editor bug survived four manual demonstrations and was only found when "
         "an automated session typed into a cell that had never entered edit mode."),
        ("Agree on the interface contract in writing",
         "a one-page file naming the five tables and the render signature would have saved "
         "the first day of discussion and the merge anxiety at the end."),
        ("Model the household size properly",
         "instead of an administrator form, the size could be inferred from the most "
         "frequent value in the first month of a household, with the administrator form "
         "kept as an override."),
    ])


def section_conclusion(document: Document) -> None:
    """Section 6 - conclusion."""
    heading(document, "6. Conclusion")
    para(document,
         "This project gave me the complete cycle of a small data product: reading a "
         "suspicious export, designing five normalised tables, building a service with an "
         "enforced authorisation rule, drawing six screens that a non-technical user can "
         "operate, verifying them with automated tests and in a real browser, and writing "
         "the specification that a client would sign.")
    para(document,
         "The part I am most satisfied with is the boundary between the service and the "
         "view. It is the reason three people working on three branches could deliver one "
         "application without a single conflict, and it is the reason the analytics service "
         "could be reused unchanged when the router grew from one screen to four.")
    para(document,
         "The part I would redo is the order of the work. I wrote the dashboard before the "
         "tests, then spent two days finding a bug the tests would have caught in ten "
         "minutes. On the next project I would write the contract, then the tests, then the "
         "screen.")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def build() -> None:
    """Assemble the document and save it next to the SRS."""
    document = Document(str(TEMPLATE))
    clear_body(document)
    title_block(document)
    section_overview(document)
    section_role(document)
    section_difficulties(document)
    section_achievements(document)
    section_next(document)
    section_conclusion(document)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(OUTPUT))
    words = sum(len(paragraph.text.split()) for paragraph in document.paragraphs)
    print(f"written : {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    print(f"paras   : {len(document.paragraphs)}")
    print(f"tables  : {len(document.tables)}")
    print(f"words   : {words}")


if __name__ == "__main__":
    build()
