"""Generate the one-page artist CV and stripped leave-behind PDF."""
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

ROOT = Path(__file__).resolve().parents[1]
CV_PDF = ROOT / "cv" / "Abhilasha_Gulhane_Artist_CV.pdf"
LEAVE_PDF = ROOT / "Abhilasha_Gulhane_Artist_Portfolio.pdf"
INVENTORY_PDF = ROOT / "cv" / "Abhilasha_Gulhane_Inventory.pdf"

INK = HexColor("#222222")
MUTED = HexColor("#666666")
RULE = HexColor("#D9D3C7")
PAGE = letter


def wrap(c, text, font, size, max_width):
    return simpleSplit(text, font, size, max_width)


def hrule(c, y, x0=0.7 * inch, x1=None):
    if x1 is None:
        x1 = PAGE[0] - 0.7 * inch
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(x0, y, x1, y)


def draw_section(c, title, y):
    c.setFillColor(INK)
    c.setFont("Times-Bold", 10)
    c.drawString(0.7 * inch, y, title.upper())
    hrule(c, y - 6)
    return y - 22


def draw_item(c, year, title, body, y, width):
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(0.7 * inch, y, year)
    x = 1.85 * inch
    max_w = width - x - 0.7 * inch
    c.setFillColor(INK)
    c.setFont("Times-Bold", 11)
    title_lines = wrap(c, title, "Times-Bold", 11, max_w)
    for i, line in enumerate(title_lines):
        c.drawString(x, y - i * 13, line)
    y -= 13 * len(title_lines) + 2
    if body:
        c.setFillColor(MUTED)
        c.setFont("Times-Roman", 9.5)
        for line in wrap(c, body, "Times-Roman", 9.5, max_w):
            c.drawString(x, y, line)
            y -= 12
    return y - 10


def make_cv():
    CV_PDF.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(CV_PDF), pagesize=PAGE)
    c.setTitle("Abhilasha Gulhane — Artist CV")
    c.setAuthor("Abhilasha Gulhane")
    width, height = PAGE
    y = height - 0.7 * inch

    c.setFillColor(INK)
    c.setFont("Times-Bold", 26)
    c.drawString(0.7 * inch, y, "Abhilasha Gulhane")
    y -= 22
    c.setFont("Times-Roman", 13)
    c.drawString(0.7 * inch, y, "Visual artist")
    y -= 18
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(
        0.7 * inch,
        y,
        "Bay Area, California  ·  abhilashagulhane111@gmail.com  ·  +1 650 602 8740  ·  @abhilasha.sfart",
    )
    y -= 16
    c.setFillColor(INK)
    c.setFont("Times-Italic", 11)
    line = "Paintings of mind, attention, and systems — in a geometric line language drawn from Maharashtra wall painting."
    for wrapped in wrap(c, line, "Times-Italic", 11, width - 1.4 * inch):
        c.drawString(0.7 * inch, y, wrapped)
        y -= 14
    y -= 8

    y = draw_section(c, "Education", y)
    y = draw_item(
        c,
        "2009",
        "Intermediate Drawing Grade Examination, Grade A",
        "Government Drawing Grade Examination, Directorate of Arts, Government of Maharashtra. Annual government-certified art test: still life, memory drawing, design, geometry and lettering.",
        y,
        width,
    )
    y = draw_item(
        c,
        "2007",
        "Elementary Drawing Grade Examination, Grade A",
        "Government Drawing Grade Examination, Directorate of Arts, Government of Maharashtra. Annual government-certified art test: object drawing, memory drawing, design, plane geometry and lettering.",
        y,
        width,
    )
    y = draw_item(c, "2020", "M.S., University of Illinois Urbana-Champaign", "", y, width)
    y = draw_item(c, "2018", "B.Tech., Indian Institute of Technology Kharagpur", "", y, width)

    y = draw_section(c, "Selected work", y)
    y = draw_item(
        c,
        "2026",
        "Human Mind and Technology Ecosystem",
        "Acrylic on canvas. Ten works in three formats: monument canvases (24 × 36 in); horizon triptych (12 × 36 in per panel, three panels); intimate studies (18 × 24 in).",
        y,
        width,
    )

    y = draw_section(c, "Charity auctions", y)
    y = draw_item(
        c,
        "2024",
        "BlackRock San Francisco Giving Days, silent auction",
        "Five paintings sold.",
        y,
        width,
    )
    y = draw_item(
        c,
        "2023",
        "BlackRock San Francisco Giving Days, silent auction",
        "Paintings sold.",
        y,
        width,
    )

    y -= 8
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 9)
    note = "Inventory (title, year, medium, size, availability) on request. Prices not listed on the public site."
    c.drawString(0.7 * inch, y, note)
    c.save()


WORKS = [
    ("The Living Circuit", "Acrylic on canvas", "24 × 36 in"),
    ("Mindstream", "Acrylic on canvas", "24 × 36 in"),
    ("The Pattern Oracle", "Acrylic on canvas", "24 × 36 in"),
    ("Spectrum of Awareness", "Acrylic on canvas, triptych", "12 × 36 in × 3 panels"),
    ("Dual Hemisphere", "Acrylic on canvas", "18 × 24 in"),
    ("Between Worlds", "Acrylic on canvas", "18 × 24 in"),
    ("Cosmos & Collective", "Acrylic on canvas", "18 × 24 in"),
    ("Neural Blueprint", "Acrylic on canvas", "18 × 24 in"),
    ("Consciousness Hub", "Acrylic on canvas", "18 × 24 in"),
    ("Mind Garden", "Acrylic on canvas", "18 × 24 in"),
]


def make_inventory():
    INVENTORY_PDF.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(INVENTORY_PDF), pagesize=PAGE)
    c.setTitle("Abhilasha Gulhane — Inventory 2026")
    c.setAuthor("Abhilasha Gulhane")
    height = PAGE[1]
    y = height - 0.7 * inch
    c.setFillColor(INK)
    c.setFont("Times-Bold", 20)
    c.drawString(0.7 * inch, y, "Inventory")
    y -= 16
    c.setFont("Times-Italic", 12)
    c.drawString(0.7 * inch, y, "Human Mind and Technology Ecosystem · 2026")
    y -= 14
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(0.7 * inch, y, "Abhilasha Gulhane  ·  Prices on request  ·  Do not publish prices on the homepage")
    y -= 18
    hrule(c, y)
    y -= 22
    for title, medium, size in WORKS:
        c.setFillColor(INK)
        c.setFont("Times-Bold", 12)
        c.drawString(0.7 * inch, y, title)
        y -= 14
        c.setFillColor(MUTED)
        c.setFont("Times-Roman", 10)
        c.drawString(0.7 * inch, y, f"{medium}  ·  {size}  ·  Available")
        y -= 20
    y -= 6
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 9)
    c.drawString(0.7 * inch, y, "Year: 2026 for all works. Filename convention: Gulhane_Title_2026.jpg")
    c.save()


ABOUT = (
    "Abhilasha Gulhane is a visual artist based in the Bay Area. Her current series, "
    "Human Mind and Technology Ecosystem (2026), uses white acrylic line on deep burgundy "
    "and navy grounds to map thought, attention, circuitry, and living systems as one geometry. "
    "The mark comes from Maharashtra wall painting: a spare, rhythmic line language she treats "
    "as a tool for describing the mind, not as a folk story. Heads become circuit cities. Data "
    "becomes current. Pattern becomes a way of seeing inner and outer worlds at the same scale. "
    "She holds Grade A in the Elementary (2007) and Intermediate (2009) Drawing Grade Examinations "
    "— government-certified art tests of the Maharashtra State Board of Art Education. She has "
    "painted since childhood, moving from pencil and watercolor into acrylic in 2015. Selected work, 2026."
)

STATEMENT = [
    "I paint the mind as a system: attention, circuitry, and living networks sharing one geometry.",
    "White acrylic line on burgundy and navy is how thought becomes visible — inner weather mapped onto the same structures that run technology and collective life.",
    "The line language is drawn from Maharashtra wall painting; the subject is contemporary consciousness, not folk narrative.",
    "In Human Mind and Technology Ecosystem (2026), heads become circuit cities, data becomes current, and pattern becomes a way of seeing.",
    "The work asks whether thought, economy, and ecology are separate domains, or one field drawn at different scales.",
]


def draw_wrapped_block(c, text, y, font="Times-Roman", size=11, leading=15, color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    max_w = PAGE[0] - 1.4 * inch
    for line in wrap(c, text, font, size, max_w):
        c.drawString(0.7 * inch, y, line)
        y -= leading
    return y


def make_leavebehind():
    c = canvas.Canvas(str(LEAVE_PDF), pagesize=PAGE)
    c.setTitle("Abhilasha Gulhane — Selected work, 2026")
    c.setAuthor("Abhilasha Gulhane")
    width, height = PAGE

    # Cover
    y = height - 1.3 * inch
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(0.7 * inch, y, "VISUAL ARTIST")
    y -= 36
    c.setFillColor(INK)
    c.setFont("Times-Bold", 32)
    c.drawString(0.7 * inch, y, "Abhilasha Gulhane")
    y -= 28
    c.setFont("Times-Italic", 13)
    for line in wrap(
        c,
        "Paintings of mind, attention, and systems — in a geometric line language drawn from Maharashtra wall painting.",
        "Times-Italic",
        13,
        width - 1.4 * inch,
    ):
        c.drawString(0.7 * inch, y, line)
        y -= 18
    y -= 8
    hrule(c, y)
    y -= 28
    c.setFont("Times-Roman", 12)
    c.drawString(0.7 * inch, y, "Selected work, 2026")
    y -= 16
    c.setFont("Times-Italic", 14)
    c.drawString(0.7 * inch, y, "Human Mind and Technology Ecosystem")
    y -= 18
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 11)
    c.drawString(0.7 * inch, y, "Acrylic on canvas  ·  Ten works")
    y -= 40
    c.setFillColor(INK)
    c.setFont("Times-Roman", 11)
    for line in [
        "Bay Area, California",
        "abhilashagulhane111@gmail.com",
        "+1 650 602 8740",
        "Instagram @abhilasha.sfart",
    ]:
        c.drawString(0.7 * inch, y, line)
        y -= 16
    c.showPage()

    # About + statement
    y = height - 0.85 * inch
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(0.7 * inch, y, "ABOUT")
    y -= 8
    hrule(c, y)
    y -= 22
    y = draw_wrapped_block(c, ABOUT, y, size=11, leading=15)
    y -= 18
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(0.7 * inch, y, "ARTIST STATEMENT")
    y -= 8
    hrule(c, y)
    y -= 22
    for para in STATEMENT:
        y = draw_wrapped_block(c, para, y, size=11, leading=15)
        y -= 8
    y -= 8
    c.setFillColor(MUTED)
    c.setFont("Times-Italic", 11)
    c.drawString(0.7 * inch, y, "— Abhilasha Gulhane")
    c.showPage()

    # Inventory
    y = height - 0.85 * inch
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 10)
    c.drawString(0.7 * inch, y, "WORKS  ·  2026")
    y -= 8
    hrule(c, y)
    y -= 22
    for title, medium, size in WORKS:
        c.setFillColor(INK)
        c.setFont("Times-Bold", 12)
        c.drawString(0.7 * inch, y, title)
        y -= 14
        c.setFillColor(MUTED)
        c.setFont("Times-Roman", 10)
        c.drawString(0.7 * inch, y, f"{medium}  ·  {size}  ·  Available")
        y -= 20
    y -= 6
    c.setFillColor(MUTED)
    c.setFont("Times-Roman", 9)
    c.drawString(0.7 * inch, y, "Prices on request. Do not list prices on the public site until they are set.")
    c.save()


if __name__ == "__main__":
    make_cv()
    make_inventory()
    make_leavebehind()
    print("Wrote", CV_PDF)
    print("Wrote", INVENTORY_PDF)
    print("Wrote", LEAVE_PDF)
