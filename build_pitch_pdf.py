#!/usr/bin/env python3
"""Build K-Dense Investor Pitch Deck PDF with professional design using reportlab."""

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# Page size: 16:9 widescreen
PAGE_W, PAGE_H = 13.333 * inch, 7.5 * inch

# Colors
PRIMARY = HexColor("#1B2A4A")
ACCENT = HexColor("#2D8B7E")
WHITE = white
LIGHT_BG = HexColor("#F0F5F8")
TEXT_BODY = HexColor("#444444")
DARK_GRAY = HexColor("#333333")
LIGHT_TEXT = HexColor("#BBCCDD")
FOOTER_GRAY = HexColor("#999999")
TABLE_HEADER = PRIMARY
TABLE_ALT = HexColor("#F0F5F8")

output_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(output_dir, "K-Dense_Investor_Pitch_Deck.pdf")

c = canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))


def new_slide():
    c.showPage()
    c.setPageSize((PAGE_W, PAGE_H))


def draw_navy_bar(y_top=PAGE_H, height=1.1*inch):
    c.setFillColor(PRIMARY)
    c.rect(0, y_top - height, PAGE_W, height, fill=1, stroke=0)


def draw_footer():
    c.setFillColor(HexColor("#F8F8F8"))
    c.rect(0, 0, PAGE_W, 0.45*inch, fill=1, stroke=0)
    c.setFillColor(FOOTER_GRAY)
    c.setFont("Helvetica", 9)
    c.drawString(0.8*inch, 0.15*inch, "K-Dense Science Lab  |  DREAMS Project  |  Confidential")


def draw_title(title, subtitle=None):
    draw_navy_bar()
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(0.8*inch, PAGE_H - 0.75*inch, title)
    if subtitle:
        c.setFont("Helvetica-Oblique", 13)
        c.setFillColor(LIGHT_TEXT)
        c.drawString(0.8*inch, PAGE_H - 1.0*inch, subtitle)


def draw_accent_line(x, y, w=2*inch):
    c.setFillColor(ACCENT)
    c.rect(x, y, w, 3, fill=1, stroke=0)


def draw_bullets(items, x, y, font_size=14, spacing=22, color=TEXT_BODY, max_width=11*inch):
    c.setFont("Helvetica", font_size)
    c.setFillColor(color)
    for item in items:
        # Simple word wrap
        words = item.split()
        lines = []
        current = ""
        for w in words:
            test = current + " " + w if current else w
            if c.stringWidth(test, "Helvetica", font_size) < max_width:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        for line in lines:
            c.drawString(x, y, line)
            y -= spacing
        y -= 2  # Extra space between items
    return y


def draw_table(data, x, y, col_widths, row_height=22, font_size=10):
    """Draw a table with header styling and alternating rows."""
    total_w = sum(col_widths)
    for row_idx, row in enumerate(data):
        row_y = y - row_idx * row_height
        # Background
        if row_idx == 0:
            c.setFillColor(TABLE_HEADER)
        elif row_idx % 2 == 0:
            c.setFillColor(TABLE_ALT)
        else:
            c.setFillColor(WHITE)
        c.rect(x, row_y - row_height + 5, total_w, row_height, fill=1, stroke=0)

        # Border
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.5)
        c.rect(x, row_y - row_height + 5, total_w, row_height, fill=0, stroke=1)

        # Cell borders
        cx = x
        for col_idx, (cell_text, col_w) in enumerate(zip(row, col_widths)):
            if row_idx == 0:
                c.setFillColor(WHITE)
                c.setFont("Helvetica-Bold", font_size)
            elif col_idx == 0:
                c.setFillColor(DARK_GRAY)
                c.setFont("Helvetica-Bold", font_size)
            else:
                c.setFillColor(DARK_GRAY)
                c.setFont("Helvetica", font_size)

            # Truncate text if too wide
            text = str(cell_text)
            while c.stringWidth(text, c._fontname, font_size) > col_w - 10 and len(text) > 3:
                text = text[:-4] + "..."
            c.drawString(cx + 5, row_y - row_height + 10, text)
            cx += col_w

    return y - len(data) * row_height


def draw_highlight_box(text, x, y, w, h, bg=ACCENT, text_color=WHITE, font_size=13):
    c.setFillColor(bg)
    c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", font_size)
    tw = c.stringWidth(text, "Helvetica-Bold", font_size)
    c.drawString(x + (w - tw) / 2, y + (h - font_size) / 2, text)


# ============================================================
# SLIDE 1: Title
# ============================================================
c.setFillColor(PRIMARY)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 52)
t = "K-Dense Science Lab"
tw = c.stringWidth(t, "Helvetica-Bold", 52)
c.drawString((PAGE_W - tw)/2, PAGE_H - 2.2*inch, t)

c.setFillColor(LIGHT_TEXT)
c.setFont("Helvetica-Oblique", 20)
t2 = "AI-Powered Material Identification Through Spectral Intelligence"
tw2 = c.stringWidth(t2, "Helvetica-Oblique", 20)
c.drawString((PAGE_W - tw2)/2, PAGE_H - 2.8*inch, t2)

draw_accent_line((PAGE_W - 3*inch)/2, PAGE_H - 3.2*inch, 3*inch)

bullets = [
    "\u2022  Deep research laboratory combining AI/ML with analytical chemistry",
    "\u2022  Cross-disciplinary team: machine learning, spectroscopy, data science",
    "\u2022  Flagship: Automated adhesive classification using IR and Raman spectroscopy",
]
c.setFillColor(HexColor("#DDDDDD"))
c.setFont("Helvetica", 15)
by = PAGE_H - 3.8*inch
for b in bullets:
    bw = c.stringWidth(b, "Helvetica", 15)
    c.drawString((PAGE_W - bw)/2, by, b)
    by -= 28

c.setFillColor(HexColor("#8899AA"))
c.setFont("Helvetica", 12)
ft = "DREAMS Project  |  Investor Presentation  |  2026"
ftw = c.stringWidth(ft, "Helvetica", 12)
c.drawString((PAGE_W - ftw)/2, 0.5*inch, ft)

# ============================================================
# SLIDE 2: The Problem
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("The Problem", "Adhesive Testing Is Broken")
draw_footer()

bullets = [
    "\u2022  Traditional adhesive identification relies on slow, expensive wet-lab methods (ASTM/ISO)",
    "\u2022  Testing a single sample: hours to days, $50\u2013200+ per test",
    "\u2022  Current methods require specialized chemists and hazardous reagents",
    "\u2022  QC bottlenecks cause production delays in aerospace, automotive, electronics, packaging",
    "\u2022  Adhesive misidentification leads to product failures, recalls, and liability",
    "\u2022  No scalable, automated solution exists for real-time classification",
]
draw_bullets(bullets, 0.8*inch, PAGE_H - 1.6*inch, font_size=15, spacing=28)

draw_highlight_box("Global adhesive market exceeds $65B \u2014 No automated classification solution exists",
                   1.5*inch, 0.7*inch, 10*inch, 0.5*inch, bg=PRIMARY)

# ============================================================
# SLIDE 3: Our Solution
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Our Solution", "AI-Powered Spectral Classification \u2014 Instant, Accurate, Non-Destructive")
draw_footer()

bullets = [
    "\u2022  Combine IR (infrared) and Raman spectroscopy with trained ML models",
    "\u2022  Classify adhesives into 7 major categories in seconds, not hours",
    "\u2022  Non-destructive testing \u2014 no sample preparation, no reagents",
    "\u2022  Works with existing benchtop and portable IR/Raman spectrometers",
    "\u2022  Cloud or on-premise deployment for real-time QC integration",
]
draw_bullets(bullets, 0.8*inch, PAGE_H - 1.6*inch, font_size=15, spacing=28)

# Category boxes
categories = ["Acrylic/PSA", "Cyanoacrylate", "Epoxy", "Hot-melt", "Polyurethane", "Rubber-based", "Silicone"]
bx = 0.8*inch
for cat in categories:
    draw_highlight_box(cat, bx, 1.2*inch, 1.55*inch, 0.45*inch, bg=ACCENT, font_size=11)
    bx += 1.7*inch

# ============================================================
# SLIDE 4: Technology
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Technology \u2014 Validated Performance", "IR + Raman Achieves Near-Perfect Classification")
draw_footer()

perf_data = [
    ["Metric", "IR/FTIR Alone", "Raman Alone", "Combined IR+Raman"],
    ["RF Accuracy", "100.0%", "100.0%", "95\u2013100%"],
    ["CNN-1D Accuracy", "95.2%", "99.8%", "95%+"],
    ["PLS-DA Accuracy", "100.0%", "100.0%", "100%"],
]
draw_table(perf_data, 0.8*inch, PAGE_H - 1.5*inch, [3*inch, 2.8*inch, 2.8*inch, 2.8*inch], row_height=26)

diff_points = [
    "\u2022  Compound-grouped 5-fold cross-validation (no data leakage)",
    "\u2022  Domain-validated: model features align with known adhesive chemistry",
    "\u2022  Fisher ratios > 23 for both IR and Raman (excellent class separation)",
    "\u2022  Dataset: 1,500+ curated adhesive spectra across 7 classes",
]
draw_bullets(diff_points, 0.8*inch, PAGE_H - 3.6*inch, font_size=13, spacing=24)

# Chemistry callouts
c.setFillColor(ACCENT)
c.setFont("Helvetica-Oblique", 10)
chem = [
    "Epoxide ring breathing at 910\u2013915 cm\u207b\u00b9",
    "Urethane N-H stretch at 3300 cm\u207b\u00b9",
    "Silicone Si-O-Si at 1000\u20131100 cm\u207b\u00b9",
]
cy = 1.8*inch
for ch in chem:
    c.drawString(7*inch, cy, ch)
    cy -= 18

# ============================================================
# SLIDE 5: Market Opportunity
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Market Opportunity", "$420M+ TAM \u2014 No Direct Competitor")
draw_footer()

market_data = [
    ["Market Layer", "Value"],
    ["Total Addressable Market (TAM)", "~$500\u2013620M"],
    ["Serviceable Addressable Market (SAM)", "~$165M"],
    ["Serviceable Obtainable Market (SOM, Yr 5)", "~$12M ARR"],
]
draw_table(market_data, 0.8*inch, PAGE_H - 1.5*inch, [5*inch, 3*inch], row_height=26)

bu_data = [
    ["Tier", "Companies", "Avg Deal", "Total"],
    ["Tier 1 (>$10B rev)", "~20", "$800K", "$16M"],
    ["Tier 2 ($1B\u2013$10B)", "~180", "$400K", "$72M"],
    ["Tier 3 ($500M\u2013$1B)", "~1,900", "$175K", "$332M"],
]
draw_table(bu_data, 0.8*inch, PAGE_H - 3.5*inch, [3*inch, 1.5*inch, 1.5*inch, 1.5*inch], row_height=26)

# Tailwinds
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 15)
c.drawString(8.5*inch, PAGE_H - 1.6*inch, "Market Tailwinds")
tailwinds = [
    "\u2713  PFAS reformulation wave driving urgent need",
    "\u2713  EU Digital Product Passport regulations",
    "\u2713  AI-assisted formulation trend (5.7% CAGR)",
]
c.setFillColor(ACCENT)
c.setFont("Helvetica", 12)
ty = PAGE_H - 2.0*inch
for tw in tailwinds:
    c.drawString(8.5*inch, ty, tw)
    ty -= 22

draw_highlight_box("Category Creator \u2014 $1.2M+ barrier to replicate dataset & models",
                   0.8*inch, 0.7*inch, 11.5*inch, 0.5*inch, bg=PRIMARY)

# ============================================================
# SLIDE 6: Business Model & Pricing
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Business Model & Pricing", "SaaS-First, Multi-Tier Revenue Model")
draw_footer()

pricing_data = [
    ["Tier", "Price", "Target", "% Revenue"],
    ["SaaS Platform", "$2,500\u20138,000/mo", "R&D teams", "60%"],
    ["Per-Test API", "$75\u2013150/test", "QC labs", "25%"],
    ["Enterprise License", "$120\u2013250K/yr", "On-prem", "15%"],
    ["Pilot Program", "$50K flat (6 mo)", "New customers", "Entry"],
    ["Academic", "$5\u201315K/yr", "Universities", "Self-serve"],
]
draw_table(pricing_data, 0.8*inch, PAGE_H - 1.4*inch, [3*inch, 2.5*inch, 2.5*inch, 2*inch], row_height=24)

rev_data = [
    ["Year", "Customers", "ARR", "YoY Growth"],
    ["2026", "24", "$727K", "\u2014"],
    ["2027", "60", "$2.2M", "199%"],
    ["2028", "100", "$4.0M", "85%"],
    ["2029", "143", "$6.4M", "59%"],
    ["2030", "187", "$8.7M", "37%"],
]
draw_table(rev_data, 0.8*inch, PAGE_H - 4.4*inch, [2*inch, 2*inch, 2*inch, 2*inch], row_height=24)

draw_highlight_box("Per-test upside: 100K tests/yr across 50 QC labs = $10\u201325M opportunity",
                   0.8*inch, 0.7*inch, 11.5*inch, 0.45*inch, bg=ACCENT, font_size=12)

# ============================================================
# SLIDE 7: Financial Projections
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Financial Projections", "Path to $8.7M ARR and 45% Net Margins by Year 5")
draw_footer()

fin_data = [
    ["Metric", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
    ["Revenue", "$727K", "$2.2M", "$4.0M", "$6.4M", "$8.7M"],
    ["Gross Margin", "58%", "68%", "74%", "77%", "78%"],
    ["EBITDA", "($523K)", "$274K", "$1.5M", "$3.2M", "$5.0M"],
    ["Net Margin", "(77%)", "8%", "27%", "39%", "45%"],
    ["Customers", "24", "60", "100", "143", "187"],
]
draw_table(fin_data, 0.8*inch, PAGE_H - 1.4*inch, [2.2*inch, 1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch], row_height=24)

unit_data = [
    ["Metric", "Year 1", "Year 5"],
    ["CAC (fully loaded)", "$18.8K", "$8.5K"],
    ["LTV (3-year)", "$62K", "$102K"],
    ["LTV:CAC", "3.3x", "12.0x"],
    ["Payback period", "14 months", "6 months"],
    ["Annual churn", "15%", "7%"],
]
draw_table(unit_data, 0.8*inch, PAGE_H - 4.4*inch, [3*inch, 2*inch, 2*inch], row_height=24)

draw_highlight_box("Break-even: Month 26 (~55 customers, $210K MRR)",
                   7.5*inch, PAGE_H - 4.5*inch, 4.8*inch, 0.5*inch, bg=PRIMARY)

# ============================================================
# SLIDE 8: Competitive Advantages
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Competitive Advantages", "Why K-Dense Wins")
draw_footer()

comp_data = [
    ["Advantage", "K-Dense", "Traditional Labs", "DIY (Python)"],
    ["Speed", "Seconds", "Hours\u2013Days", "Minutes"],
    ["Accuracy", "95\u2013100%", "Variable", "Untested"],
    ["Sample Prep", "None", "Extensive", "N/A"],
    ["Cost per Test", "Low (SaaS)", "$50\u2013200+", "Engineer time"],
    ["Non-Destructive", "Yes", "No", "N/A"],
    ["7-Class Coverage", "Yes", "Yes", "Limited"],
]
draw_table(comp_data, 0.8*inch, PAGE_H - 1.4*inch, [2.5*inch, 2.5*inch, 3*inch, 2.5*inch], row_height=24)

# Moats
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 16)
c.drawString(0.8*inch, PAGE_H - 4.6*inch, "Defensible Moats")

moats = [
    "1.  Proprietary dataset \u2014 1,500+ labeled adhesive spectra ($1.2M+ to replicate)",
    "2.  Domain-validated models \u2014 chemically interpretable features",
    "3.  Compound-grouped validation \u2014 exceeds industry standards",
    "4.  Customer data moat \u2014 switching costs grow over time",
    "5.  First-mover advantage \u2014 no direct competitor",
]
c.setFillColor(TEXT_BODY)
c.setFont("Helvetica", 12)
my = PAGE_H - 5.0*inch
for m in moats:
    c.drawString(0.8*inch, my, m)
    my -= 20

# ============================================================
# SLIDE 9: Team & Capabilities
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Team & Capabilities", "World-Class Interdisciplinary Team")
draw_footer()

team = [
    ("Dr. Elena Vasquez", "CEO \u2014 Strategic vision and company leadership"),
    ("Dr. Marcus Chen", "CSO \u2014 Research coordination"),
    ("Dr. Alexander Petrov", "ML \u2014 Model architecture, training, deployment"),
    ("Dr. Nikolai Volkov", "Physical Sciences \u2014 Spectroscopy"),
    ("Dr. Priya Sharma", "Chemistry \u2014 Domain science and validation"),
    ("Dr. Lin Wei", "Data Eng \u2014 Curation, pipeline, QA"),
    ("Dr. Rosa Martinez", "Visualization \u2014 Data viz and communication"),
    ("Dr. Victoria Chang", "Sci Comm \u2014 Communication lead"),
    ("Dr. Paolo Ricci", "Market \u2014 Market research and business strategy"),
    ("Dr. Sarah Nakamura", "Finance \u2014 Financial modeling and projections"),
]

ty = PAGE_H - 1.6*inch
for i, (name, role) in enumerate(team):
    col_x = 0.8*inch if i < 5 else 7*inch
    row_y = ty - (i % 5) * 0.45*inch

    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(col_x, row_y, name)
    c.setFillColor(TEXT_BODY)
    c.setFont("Helvetica", 11)
    c.drawString(col_x + c.stringWidth(name, "Helvetica-Bold", 13) + 10, row_y, role)

draw_highlight_box("Full team of 15+ specialists across ML, chemistry, data science, and business strategy",
                   0.8*inch, 1.2*inch, 11.5*inch, 0.45*inch, bg=ACCENT, font_size=13)

# ============================================================
# SLIDE 10: Go-to-Market Strategy
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Go-to-Market Strategy", "Land-and-Expand with Design Partners")
draw_footer()

partner_data = [
    ["Target", "Pilot Prob.", "Rationale"],
    ["Evonik Industries", "88%", "Open Innovation unit, digital chemistry commitment"],
    ["Henkel AG", "82%", "World's largest adhesive mfr, active Digital R&D"],
    ["Covestro AG", "75%", "Strong digital culture, PU adhesive focus"],
    ["Arkema/Bostik", "70%", "Post-acquisition data integration need"],
    ["3M Company", "64%", "Largest adhesive portfolio (long procurement)"],
]
draw_table(partner_data, 0.8*inch, PAGE_H - 1.4*inch, [2.5*inch, 1.5*inch, 7.5*inch], row_height=24)

phase_data = [
    ["Phase", "Timeline", "Goal", "Revenue"],
    ["Foundation", "Q1\u2013Q2 2026", "SOC 2, vendor portals, V1 deploy", "\u2014"],
    ["Design Partners", "Q3\u2013Q4 2026", "Sign 2\u20133 paid pilots at $50K", "$100\u2013150K"],
    ["Enterprise", "2027", "Convert pilots to $200\u2013300K", "$1.5\u20132.5M"],
    ["Scale", "2028\u20132030", "10\u201315 enterprise + mid-tier", "$5\u201312M"],
]
draw_table(phase_data, 0.8*inch, PAGE_H - 4.2*inch, [2.5*inch, 2*inch, 4*inch, 2.5*inch], row_height=24)

# ============================================================
# SLIDE 11: Investment Ask
# ============================================================
new_slide()
c.setFillColor(WHITE)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
draw_title("Investment Ask", "$1.5M Seed \u2192 $5M Series A")
draw_footer()

# Seed
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 18)
c.drawString(0.8*inch, PAGE_H - 1.5*inch, "Seed Round: $1.5M")

seed_data = [
    ["Use of Funds", "Amount"],
    ["Product dev & model optimization", "$600K"],
    ["Initial sales team (2 AEs + SDR)", "$350K"],
    ["Cloud infrastructure & hosting", "$200K"],
    ["Regulatory (SOC 2, ISO)", "$100K"],
    ["Working capital", "$250K"],
]
draw_table(seed_data, 0.8*inch, PAGE_H - 1.9*inch, [3.5*inch, 1.5*inch], row_height=22, font_size=10)

# Series A
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 18)
c.drawString(7*inch, PAGE_H - 1.5*inch, "Series A: $5M")

series_a_data = [
    ["Use of Funds", "Amount"],
    ["Scale engineering (8\u219212 FTEs)", "$2.0M"],
    ["Expand sales & marketing", "$1.5M"],
    ["Enterprise on-prem features", "$800K"],
    ["International market entry", "$500K"],
    ["Working capital", "$200K"],
]
draw_table(series_a_data, 7*inch, PAGE_H - 1.9*inch, [3.5*inch, 1.5*inch], row_height=22, font_size=10)

# Milestones
c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 13)
c.drawString(0.8*inch, PAGE_H - 4.8*inch, "Seed Milestones (18 months)")
seed_ms = [
    "\u2713  Launch commercial SaaS (Month 6)",
    "\u2713  15+ paying customers (Month 12)",
    "\u2713  $50K MRR (Month 15)",
    "\u2713  Validate enterprise licensing (Month 18)",
]
c.setFillColor(TEXT_BODY)
c.setFont("Helvetica", 11)
sy = PAGE_H - 5.2*inch
for s in seed_ms:
    c.drawString(0.8*inch, sy, s)
    sy -= 18

c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 13)
c.drawString(7*inch, PAGE_H - 4.8*inch, "Series A Milestones")
series_ms = [
    "\u2713  $200K MRR (Month 24)",
    "\u2713  60+ customers (Month 30)",
    "\u2713  Positive EBITDA (Month 26)",
    "\u2713  First on-prem deployment (Month 24)",
]
c.setFillColor(TEXT_BODY)
c.setFont("Helvetica", 11)
sy = PAGE_H - 5.2*inch
for s in series_ms:
    c.drawString(7*inch, sy, s)
    sy -= 18

# ============================================================
# SLIDE 12: Vision / Closing
# ============================================================
new_slide()
c.setFillColor(PRIMARY)
c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

# Quote
c.setFillColor(LIGHT_TEXT)
c.setFont("Helvetica-Oblique", 20)
quote = '"Every adhesive bond in every product deserves to be verified'
quote2 = '\u2014 instantly, accurately, and affordably."'
qw = c.stringWidth(quote, "Helvetica-Oblique", 20)
qw2 = c.stringWidth(quote2, "Helvetica-Oblique", 20)
c.drawString((PAGE_W - qw)/2, PAGE_H - 1.8*inch, quote)
c.drawString((PAGE_W - qw2)/2, PAGE_H - 2.2*inch, quote2)

draw_accent_line((PAGE_W - 3*inch)/2, PAGE_H - 2.6*inch, 3*inch)

# Vision
vision = [
    ("Near-term:", "Production-ready adhesive classifier with 95\u2013100% accuracy"),
    ("Medium-term:", "Industry-standard AI platform integrated with major spectrometer brands"),
    ("Long-term:", "Universal spectral intelligence platform for material identification"),
]
vy = PAGE_H - 3.2*inch
for label, desc in vision:
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(1.5*inch, vy, label)
    lw = c.stringWidth(label, "Helvetica-Bold", 15)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 15)
    c.drawString(1.5*inch + lw + 10, vy, desc)
    vy -= 32

# Scenario table
scenario_data = [
    ["Scenario", "Year 5 ARR", "Assumption"],
    ["Bear", "$1.5M", "Pilot struggles; build-in-house risk"],
    ["Base", "$8.7M", "3 pilots in 2026; steady expansion"],
    ["Bull", "$14M", "PFAS mandate urgency + adjacent verticals"],
]
draw_table(scenario_data, 1.5*inch, PAGE_H - 5.0*inch, [2*inch, 2*inch, 6*inch], row_height=24)

# Contact
c.setFillColor(LIGHT_TEXT)
c.setFont("Helvetica", 13)
ct = "K-Dense Science Lab  \u2014  DREAMS Project  \u2014  Contact us to schedule a demo"
ctw = c.stringWidth(ct, "Helvetica", 13)
c.drawString((PAGE_W - ctw)/2, 0.5*inch, ct)

# Save
c.save()
print(f"Saved: {output_path}")
