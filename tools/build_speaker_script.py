"""Build the 5-minute bilingual speaker script for member B."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "Speaker Script (5 min, EN-CN).docx"

NAVY = RGBColor(0x1F, 0x3B, 0x57)
ACCENT = RGBColor(0xB3, 0x25, 0x3B)
GREY = RGBColor(0x5B, 0x66, 0x72)
INK = RGBColor(0x23, 0x30, 0x3B)
CHINESE = RGBColor(0x2B, 0x4A, 0x6F)

DATE = "27/11/2026"
STUDENT = "Tan Haowen"

# --------------------------------------------------------------------------- #
# Script content: (section title, time budget, [(english, chinese, note?)])
# --------------------------------------------------------------------------- #
SCRIPT = [
    (
        "Opening \u2014 who I am and what I own",
        "0:00 \u2013 0:30",
        [
            ("Good afternoon. My name is Tan Haowen, and I am member B on the project. "
             "I own three things: the analytics service, the dashboard, and the main "
             "router that puts the whole application together. I also built the official "
             "SRS in Word.",
             "下午好。我是谭皓文，项目里的成员 B。我负责三件事：分析服务、仪表盘，"
             "以及把整个应用拼起来的主路由。另外我做了正式的 SRS 文档。",
             "Stand relaxed, look at the audience. This is 30 seconds, do not rush it."),
        ],
    ),
    (
        "The problem in one sentence",
        "0:30 \u2013 1:00",
        [
            ("The client gives us one CSV file: 100,000 readings from 500 households. "
             "A resident can read that file, but they learn nothing from it. They cannot "
             "tell which appliance costs them money, and they cannot tell whether their "
             "consumption is normal.",
             "客户给我们一个 CSV 文件：500 户、10 万条读数。住户能打开这个文件，"
             "但学不到任何东西。他们不知道自己哪台电器费钱，也不知道自己的用电量是否正常。",
             "Point at the dashboard screenshot on the slide."),
        ],
    ),
    (
        "Demo 1 \u2014 the daily view",
        "1:00 \u2013 1:45",
        [
            ("So here is the dashboard. It opens on the daily view, because that is what "
             "the brief asks for. The user sees one line for their household, in blue, "
             "and one grey line for the average of all 500 households. Right here, Home 1 "
             "used 122.2 kWh over 61 days, which is two kWh a day \u2014 slightly below the "
             "neighbourhood average.",
             "这就是仪表盘。默认是日视图，因为需求文档就是这么要求的。用户看到蓝色的是"
             "自己家的曲线，灰色的是全部 500 户的平均线。这里 Home 1 在 61 天里用了 "
             "122.2 kWh，平均每天 2 kWh，略低于邻里平均。",
             "This is the moment the audience understands the product. Slow down."),
            ("Below the chart, the same numbers are repeated as a table, with the number "
             "of measurements and the consumption per resident, so the resident can check "
             "the figure and not just look at a curve.",
             "图表下面是同一组数据的表格，带测量条数和人均用电量，住户可以核对数字，"
             "而不只是看一条曲线。"),
        ],
    ),
    (
        "Demo 2 \u2014 switching granularity and comparing",
        "1:45 \u2013 2:30",
        [
            ("Now I switch to Month. The same service answers, the same household, "
             "twelve points instead of 61. And now I add two more households. Three "
             "households, three colours, one grey benchmark.",
             "现在切到月度。还是同一个服务、同一户，61 个点变成 12 个点。接下来我加上"
             "另外两户。三户、三种颜色、一条灰色基准线。",
             "Click the radio and the multiselect live. Do not fake it."),
            ("The colour is the point here. Each household keeps the same colour no matter "
             "which families are selected, because the service publishes an explicit "
             "colour map and the chart uses it as a fixed scale. Without that, filtering "
             "one household out would repaint the others.",
             "颜色这里是关键。不管选了哪几户，每户的颜色都不变，因为服务发布了一张"
             "明确的颜色表，图表把它当作固定比例尺。没有这个，去掉一户会让其它户变色。"),
        ],
    ),
    (
        "The technical core \u2014 one service, three guarantees",
        "2:30 \u2013 3:30",
        [
            ("Let me step behind the screen for one minute. All of this comes from a single "
             "class, AnalyticsService, 344 lines. It gives three guarantees.",
             "我花一分钟讲讲界面背后。所有这些都来自一个类 AnalyticsService，344 行。"
             "它提供三个保证。",
             "Switch to the code slide. This is the part the jury grades hardest."),
            ("First, authorisation lives in the service, not in the screen. If a user asks "
             "for a household that is not theirs, the service raises an error. A second "
             "interface could not bypass it.",
             "第一，权限校验在服务里，不在界面里。用户如果请求不属于自己的户，服务直接报错。"
             "第二个界面也绕不过去。"),
            ("Second, the benchmark curve is always computed over all 500 households, even "
             "when a user may only see one. That is what makes the comparison meaningful "
             "without exposing anybody's private data.",
             "第二，基准线永远按全部 500 户算，即使用户只能看到自己一户。这样对比才有意义，"
             "又不泄露任何人的隐私数据。"),
            ("Third, nothing is computed twice. Day, month and year are the same query "
             "with a different time key, so a new granularity costs no new code.",
             "第三，不做重复计算。日、月、年就是同一个查询换一个时间键，"
             "加一个新粒度不需要写新代码。"),
        ],
    ),
    (
        "Verification \u2014 the numbers",
        "3:30 \u2013 4:15",
        [
            ("On verification: 21 unit tests cover the service, including the "
             "authorisation rule. The whole repository runs 38 tests after the three "
             "branches were merged, with no failure.",
             "验证方面：21 个单元测试覆盖这个服务，包括权限规则。三个分支合并后，"
             "整个仓库跑 38 个测试，全部通过。",
             "Speak the numbers slowly and clearly. The jury writes them down."),
            ("And because unit tests do not prove a screen works, I also drove the real "
             "application in a headless browser: 16 checks across the four screens, zero "
             "JavaScript errors. Those logs are in the repository.",
             "而且单元测试证明不了界面对不对，所以我用无头浏览器把真实应用跑了一遍："
             "四个页面 16 项检查，零 JavaScript 错误。日志在仓库里。"),
            ("One honest note. The dataset contains no weather signal at all: the "
             "temperature changes between two readings of the same house on the same day. "
             "Our AI screen reports that instead of hiding it. A model that admits it "
             "learned nothing is worth more than one that pretends.",
             "有一点我要诚实说明。这个数据集里完全没有天气信号：同一户同一天的两条读数"
             "温度都不一样。我们的 AI 页面如实报告这一点，而不是藏起来。"
             "一个承认自己没学到东西的模型，比一个假装学到的更有价值。",
             "This is the slide that makes you look honest. Do not skip it."),
        ],
    ),
    (
        "Closing",
        "4:15 \u2013 5:00",
        [
            ("To close, I want to name the decision I am most satisfied with. It is not "
             "the chart and it is not the AI. It is the boundary between the service and "
             "the screen.",
             "最后，我想说我最满意的一个决定。不是图表，也不是 AI，"
             "而是服务和界面之间的那条边界。",
             "Slow down. This is your last sentence, make it land."),
            ("Three people, three branches, one application, and not a single merge "
             "conflict \u2014 because each screen talks to a service and the router is the "
             "only file that knows about all of them.",
             "三个人、三个分支、一个应用，一次合并冲突都没有——因为每个界面只和"
             "服务对话，而路由器是唯一知道所有界面的文件。"),
            ("Thank you. I am happy to take questions about the analytics service, the "
             "dashboard, or the SRS.",
             "谢谢。关于分析服务、仪表盘或 SRS 文档，欢迎大家提问。"),
        ],
    ),
]

# --------------------------------------------------------------------------- #
# Likely questions and answers
# --------------------------------------------------------------------------- #
QUESTIONS = [
    ("Why do you cap the comparison at five households?",
     "Because the brief asks for five, and because a palette of five colours is the limit "
     "of what stays readable on a line chart. The cap is enforced twice: the widget limits "
     "the selection, and the service rejects six.",
     "为什么对比上限是五户？",
     "因为需求文档要求五户，也因为线性图上五种颜色已经是可读性的极限。"
     "这个上限做了两道：控件限制选择，服务拒绝六户。"),
    ("Why is the household size entered by an administrator and not read from the CSV?",
     "Because it cannot be read. All 500 households declare more than one size in the "
     "export, so the column is a per-row noise value, not a household attribute. We keep "
     "the original column on disk for audit, and expose the size as a maintained attribute.",
     "为什么户人数是管理员录入而不是从 CSV 读？",
     "因为读不出来。500 户在导出文件里都声明了不止一个人数，所以这一列是逐行噪声，"
     "不是住户属性。我们把原始列保留在磁盘上供审计，把人数做成可维护的属性。"),
    ("How did you know the dashboard is correct?",
     "Three ways: the manual arithmetic in the unit tests, where Home 1 over January must "
     "equal 34.93 kWh; the aggregation being identical across the day, month and year view "
     "for the same period; and the browser log, which records the values the page rendered.",
     "你怎么知道仪表盘是对的？",
     "三条路：单元测试里的手算，Home 1 一月份必须等于 34.93 kWh；同一时间段在日、月、"
     "年三种视图下聚合结果一致；以及浏览器日志，它记录了页面实际渲染的数值。"),
    ("What would you do differently?",
     "Write the tests before the screen. The most stubborn bug we had \u2014 a resident "
     "count that never reached the file \u2014 survived four manual demonstrations and only "
     "appeared when an automated browser typed into a cell that had never entered edit mode.",
     "如果重做，你会怎么改？",
     "先写测试再写界面。我们最难缠的那个 bug——录入的户人数存不进文件——"
     "躲过了四次手动演示，最后是自动化浏览器往一个从未进入编辑态的单元格里输入才暴露出来。"),
]

# --------------------------------------------------------------------------- #
# Rehearsal tips
# --------------------------------------------------------------------------- #
TIPS = [
    ("Total budget", "5 minutes. Rehearse with a timer three times. If you run over, cut "
     "Demo 2 to one sentence \u2014 never cut the verification numbers."),
    ("Speech rate", "Around 120 to 130 words per minute in English. The English text "
     "below is about 640 words, which lands at five minutes with the pauses."),
    ("Click, do not fake", "Every demo click must be live. If the network fails, the "
     "screenshots in chapter 5 of the SRS are your fallback."),
    ("Two numbers to memorise", "122.2 kWh over 61 days for Home 1 against a 500-home "
     "benchmark; 38 tests passing across the repository."),
    ("The honest slide", "The temperature finding is not a weakness, it is the most "
     "scientific thing in the presentation. Say it with confidence."),
    ("If a question is unclear", "Repeat it in your own words before answering: \u201cSo "
     "you are asking whether ...\u201d. It buys three seconds and it prevents answering the "
     "wrong question."),
]


# --------------------------------------------------------------------------- #
# Word helpers
# --------------------------------------------------------------------------- #
def _sect_index(document: Document) -> int:
    """Return the position of the section properties in the body."""
    for index, child in enumerate(document.element.body):
        if child.tag == qn("w:sectPr"):
            return index
    return len(document.element.body)


def _append(document: Document, block) -> None:
    """Move a freshly built block just before the section properties."""
    element = block._p if hasattr(block, "_p") else block._tbl
    body = document.element.body
    body.remove(element)
    body.insert(_sect_index(document), element)


def para(document: Document, text: str = "", *, size: float = 11, bold: bool = False,
         italic: bool = False, colour: RGBColor | None = None, space_after: float = 4,
         indent: float = 0.0) -> object:
    """Append one paragraph."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(0)
    if indent:
        paragraph.paragraph_format.left_indent = Cm(indent)
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


def shade(cell, hex_fill: str) -> None:
    """Fill a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn("w:shd"), {qn("w:val"): "clear",
                                          qn("w:color"): "auto",
                                          qn("w:fill"): hex_fill})
    tc_pr.append(shd)


def build() -> None:
    """Assemble the script document."""
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.6)

    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    para(document, "Speaker Script", size=26, bold=True, colour=NAVY, space_after=2)
    para(document, "Member B \u2014 analytics, dashboard and router integration",
         size=14, bold=True, colour=ACCENT, space_after=2)
    para(document, f"{STUDENT}  \u00b7  five minutes  \u00b7  {DATE}",
         size=10.5, colour=GREY, space_after=10)

    # ---- how to read the page ------------------------------------------ #
    para(document, "How to use this page", size=13, bold=True, colour=NAVY, space_after=3)
    para(document,
         "The English line is what you say. The Chinese line underneath is the meaning, "
         "so you can rehearse the idea in your own language and then deliver it in "
         "English. The grey note in brackets is a stage direction, not something you say.",
         space_after=10)

    # ---- the script ---------------------------------------------------- #
    for title, timing, parts in SCRIPT:
        para(document, f"{title}   ({timing})", size=13, bold=True, colour=NAVY,
             space_after=4)
        for part in parts:
            english, chinese = part[0], part[1]
            note = part[2] if len(part) > 2 else None
            para(document, english, size=11.5, space_after=2)
            para(document, "\u4e2d\u6587\uff1a" + chinese, size=10.5, colour=CHINESE,
                 space_after=2)
            if note:
                para(document, f"[{note}]", size=9, italic=True, colour=GREY,
                     space_after=8)
            else:
                para(document, "", size=6, space_after=6)

    # ---- questions ----------------------------------------------------- #
    para(document, "Likely questions and answers", size=16, bold=True, colour=NAVY,
         space_after=6)
    for index, (question, answer, question_cn, answer_cn) in enumerate(QUESTIONS, 1):
        para(document, f"Q{index}. {question}", size=11.5, bold=True, colour=INK,
             space_after=2)
        para(document, "\u95ee\uff1a" + question_cn, size=10, colour=GREY, space_after=3)
        para(document, "A. " + answer, size=11, space_after=2)
        para(document, "\u7b54\uff1a" + answer_cn, size=10.5, colour=CHINESE,
             space_after=10)

    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---- rehearsal tips ------------------------------------------------ #
    para(document, "Rehearsal checklist", size=16, bold=True, colour=NAVY, space_after=6)
    block = document.add_table(rows=1, cols=2)
    block.style = document.styles["Table Grid"] if "Table Grid" in [
        style.name for style in document.styles] else None
    for index, label in enumerate(("Item", "What to do")):
        cell = block.rows[0].cells[index]
        cell.text = ""
        run = cell.paragraphs[0].add_run(label)
        run.font.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.name = "Calibri"
        shade(cell, "1F3B57")
    for label, detail in TIPS:
        cells = block.add_row().cells
        cells[0].text = ""
        run = cells[0].paragraphs[0].add_run(label)
        run.font.bold = True
        run.font.size = Pt(10)
        run.font.name = "Calibri"
        cells[1].text = ""
        run = cells[1].paragraphs[0].add_run(detail)
        run.font.size = Pt(10)
        run.font.name = "Calibri"
    for row in block.rows:
        row.cells[0].width = Cm(4.6)
        row.cells[1].width = Cm(12.4)
    _append(document, block)

    para(document, "", size=6, space_after=8)
    para(document, "Demo order (do not improvise)", size=13, bold=True, colour=NAVY,
         space_after=4)
    for step in [
        "1. Log in as user1 \u2014 the sidebar shows three screens and no administration.",
        "2. Dashboard, Day: read the total aloud (122.2 kWh) and point at the grey line.",
        "3. Switch to Month: the same total, twelve points.",
        "4. Log in as user_multi \u2014 three households in the selector.",
        "5. Select the three households \u2014 three colours plus the grey benchmark.",
        "6. Unselect Fridge in the appliance filter \u2014 the totals drop and the curve moves.",
        "7. Optional: log in as admin \u2014 four screens and 500 households.",
    ]:
        para(document, step, size=10.5, indent=0.5, space_after=3)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(OUTPUT))
    words_en = sum(len(part[0].split()) for _, _, parts in SCRIPT for part in parts)
    print(f"written : {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    print(f"english words : {words_en}")
    print(f"at 130 wpm    : {words_en / 130:.1f} minutes")
    print(f"tables        : {len(document.tables)}")


if __name__ == "__main__":
    build()
