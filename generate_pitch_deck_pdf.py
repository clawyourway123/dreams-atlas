#!/usr/bin/env python3
"""Generate investor pitch deck PDF for K-Dense Science Lab DREAMS Project."""

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import HRFlowable
import os

# Custom page size (16:9 widescreen-ish, landscape letter)
PAGE_W, PAGE_H = landscape((11*inch, 8.5*inch))

# Colors
DARK_BG = HexColor('#0F172A')
ACCENT_BLUE = HexColor('#007ACC')
ACCENT_GREEN = HexColor('#00B88D')
GOLD = HexColor('#FFC107')
LIGHT_TEXT = HexColor('#DDDDDD')
DARK_TEXT = HexColor('#1A1A2E')
TABLE_HEADER = HexColor('#007ACC')
TABLE_ROW_EVEN = HexColor('#1A253A')
TABLE_ROW_ODD = HexColor('#151E32')

output_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(output_dir, "K-Dense_Investor_Pitch_Deck_March_2026.pdf")

# Styles
styles = getSampleStyleSheet()

title_style = ParagraphStyle('SlideTitle', parent=styles['Heading1'],
    fontSize=28, leading=34, textColor=white, spaceAfter=12, alignment=TA_LEFT, fontName='Helvetica-Bold')
subtitle_style = ParagraphStyle('SlideSubtitle', parent=styles['Heading2'],
    fontSize=18, leading=22, textColor=ACCENT_GREEN, spaceAfter=8, alignment=TA_LEFT, fontName='Helvetica')
section_style = ParagraphStyle('Section', parent=styles['Normal'],
    fontSize=11, leading=14, textColor=ACCENT_BLUE, spaceAfter=4, fontName='Helvetica-Bold')
body_style = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=12, leading=16, textColor=LIGHT_TEXT, spaceAfter=6, fontName='Helvetica')
bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
    fontSize=11, leading=15, textColor=LIGHT_TEXT, spaceAfter=4, fontName='Helvetica',
    leftIndent=20, bulletIndent=8)
gold_style = ParagraphStyle('Gold', parent=styles['Normal'],
    fontSize=12, leading=16, textColor=GOLD, spaceAfter=6, fontName='Helvetica-Bold', alignment=TA_CENTER)
big_center = ParagraphStyle('BigCenter', parent=styles['Heading1'],
    fontSize=36, leading=42, textColor=white, spaceAfter=8, alignment=TA_CENTER, fontName='Helvetica-Bold')
center_green = ParagraphStyle('CenterGreen', parent=styles['Normal'],
    fontSize=18, leading=22, textColor=ACCENT_GREEN, spaceAfter=8, alignment=TA_CENTER, fontName='Helvetica')
small_gray = ParagraphStyle('SmallGray', parent=styles['Normal'],
    fontSize=9, leading=12, textColor=HexColor('#888899'), spaceAfter=4, fontName='Helvetica')
heading2_style = ParagraphStyle('H2', parent=styles['Heading2'],
    fontSize=16, leading=20, textColor=ACCENT_GREEN, spaceAfter=8, fontName='Helvetica-Bold')


def make_table(data, col_widths=None):
    """Create a styled table."""
    if col_widths is None:
        col_widths = [PAGE_W * 0.8 / len(data[0])] * len(data[0])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEADING', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 1), (-1, -1), LIGHT_TEXT),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#2A3550')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        bg = TABLE_ROW_EVEN if i % 2 == 0 else TABLE_ROW_ODD
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t


def on_page(canvas, doc):
    """Dark background on every page."""
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Accent bar at top
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)
    canvas.restoreState()


story = []

# ---- SLIDE 1: TITLE ----
story.append(Spacer(1, 1.2*inch))
story.append(Paragraph("K-DENSE SCIENCE LAB", big_center))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("AI-Powered Material Identification Through Spectral Intelligence", center_green))
story.append(Spacer(1, 0.3*inch))
story.append(HRFlowable(width="30%", thickness=2, color=ACCENT_BLUE, spaceAfter=20, spaceBefore=10, hAlign='CENTER'))
story.append(Paragraph("Investor Pitch Deck", ParagraphStyle('', parent=big_center, fontSize=26)))
story.append(Paragraph("DREAMS Project  |  March 2026", ParagraphStyle('', parent=center_green, fontSize=14, textColor=HexColor('#888899'))))
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph("95\u2013100% Accuracy  \u2022  7 Adhesive Classes  \u2022  Non-Destructive  \u2022  Real-Time", gold_style))
story.append(PageBreak())

# ---- SLIDE 2: THE PROBLEM ----
story.append(Paragraph("THE PROBLEM", section_style))
story.append(Paragraph("Adhesive Testing Is Broken", title_style))
story.append(Spacer(1, 0.15*inch))
problems = [
    "Traditional adhesive identification relies on <b>slow, expensive wet-lab methods</b> (ASTM/ISO protocols)",
    "Testing a single sample: <b>hours to days</b>, <b>$50\u2013200+ per test</b>",
    "Requires <b>specialized chemists</b> and <b>hazardous reagents</b>",
    "QC bottlenecks cause <b>production delays</b> in aerospace, automotive, electronics, and packaging",
    "Adhesive misidentification leads to <b>product failures, recalls, and liability</b>",
    "Global adhesive market exceeds <b>$65B</b> \u2014 no scalable, automated classification solution exists",
]
for p in problems:
    story.append(Paragraph("\u2022  " + p, bullet_style))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("$65B+ market  \u2022  No automated solution  \u2022  Hours per test  \u2022  $200+ per sample", gold_style))
story.append(PageBreak())

# ---- SLIDE 3: OUR SOLUTION ----
story.append(Paragraph("OUR SOLUTION", section_style))
story.append(Paragraph("AI-Powered Spectral Classification", title_style))
story.append(Spacer(1, 0.15*inch))
solutions = [
    "Combine <b>IR (infrared) and Raman spectroscopy</b> with trained ML models",
    "Classify adhesives into <b>7 major categories</b> in seconds, not hours",
    "<b>Non-destructive</b> testing \u2014 no sample preparation, no reagents",
    "Works with <b>existing benchtop and portable</b> IR/Raman spectrometers",
    "<b>Cloud or on-premise</b> deployment for real-time QC integration",
]
for s in solutions:
    story.append(Paragraph("\u2022  " + s, bullet_style))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("7 Adhesive Classes", heading2_style))
classes = ["Acrylic / PSA", "Cyanoacrylate", "Epoxy", "Hot-melt", "Polyurethane", "Rubber-based", "Silicone"]
for c in classes:
    story.append(Paragraph("\u2713  " + c, bullet_style))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Instant  \u2022  Accurate  \u2022  Non-Destructive  \u2022  Affordable", gold_style))
story.append(PageBreak())

# ---- SLIDE 4: TECHNOLOGY ----
story.append(Paragraph("TECHNOLOGY", section_style))
story.append(Paragraph("Validated Performance: 95\u2013100% Accuracy", title_style))
story.append(Spacer(1, 0.15*inch))
perf_data = [
    ["Model", "IR/FTIR Alone", "Raman Alone", "Combined IR+Raman"],
    ["Random Forest", "100.0%", "100.0%", "95\u2013100%"],
    ["CNN-1D", "95.2%", "99.8%", "95%+"],
    ["PLS-DA", "100.0%", "100.0%", "100%"],
]
story.append(make_table(perf_data, [2.5*inch, 1.8*inch, 1.8*inch, 2*inch]))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Key Technical Differentiators", heading2_style))
diffs = [
    "Compound-grouped 5-fold cross-validation (no data leakage)",
    "Domain-validated: features align with known adhesive chemistry",
    "Fisher ratios > 23 for both IR and Raman (excellent class separation)",
    "Dataset: 1,500+ curated adhesive spectra across 7 classes",
    "NMR excluded from production model (non-discriminative, Fisher ratio 0.02)",
]
for d in diffs:
    story.append(Paragraph("\u2022  " + d, bullet_style))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("Epoxide ring breathing 910\u2013915 cm\u207b\u00b9  |  Urethane N-H 3300 cm\u207b\u00b9  |  Silicone Si-O-Si 1000\u20131100 cm\u207b\u00b9", small_gray))
story.append(PageBreak())

# ---- SLIDE 5: MARKET OPPORTUNITY ----
story.append(Paragraph("MARKET OPPORTUNITY", section_style))
story.append(Paragraph("$500\u2013620M TAM \u2014 No Direct Competitor", title_style))
story.append(Spacer(1, 0.15*inch))
mkt_data = [
    ["Market Layer", "Value"],
    ["Total Addressable Market (TAM)", "$500\u2013620M"],
    ["Serviceable Addressable Market (SAM)", "~$165M"],
    ["Serviceable Obtainable Market (SOM, Year 5)", "~$12M ARR"],
]
story.append(make_table(mkt_data, [4.5*inch, 2.5*inch]))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Bottom-Up Construction", heading2_style))
construction = [
    "~2,100 companies globally with meaningful adhesive R&D programs",
    "Tier 1 (>$10B revenue): ~20 companies x $800K avg = $16M",
    "Tier 2 ($1B\u201310B): ~180 companies x $400K avg = $72M",
    "Tier 3 ($500M\u20131B): ~1,900 companies x $175K avg = $332M",
]
for c in construction:
    story.append(Paragraph("\u2022  " + c, bullet_style))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Market Tailwinds", heading2_style))
tailwinds = [
    "PFAS reformulation wave \u2014 urgent need for rapid adhesive re-characterization",
    "EU Digital Product Passport regulations requiring material traceability",
    "AI-assisted formulation trend across specialty chemicals (5.7% CAGR)",
]
for t in tailwinds:
    story.append(Paragraph("\u2022  " + t, bullet_style))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("We are the CATEGORY CREATOR \u2014 $1.2M+ barrier to replicate", gold_style))
story.append(PageBreak())

# ---- SLIDE 6: BUSINESS MODEL ----
story.append(Paragraph("BUSINESS MODEL", section_style))
story.append(Paragraph("SaaS-First, Multi-Tier Revenue Model", title_style))
story.append(Spacer(1, 0.15*inch))
pricing = [
    ["Tier", "Price", "Target", "% Revenue"],
    ["SaaS Platform", "$2,500\u20138,000/mo", "R&D teams", "60%"],
    ["Per-Test API", "$75\u2013150/test", "QC labs", "25%"],
    ["Enterprise License", "$120\u2013250K/yr", "On-prem", "15%"],
    ["Pilot Program", "$50K flat (6 mo)", "New customers", "Entry"],
    ["Academic", "$5\u201315K/yr", "Universities", "Self-serve"],
]
story.append(make_table(pricing, [2.2*inch, 2*inch, 2*inch, 1.5*inch]))
story.append(Spacer(1, 0.15*inch))
revenue = [
    ["Year", "2026", "2027", "2028", "2029", "2030"],
    ["Customers", "24", "60", "100", "143", "187"],
    ["ARR", "$727K", "$2.2M", "$4.0M", "$6.4M", "$8.7M"],
    ["YoY Growth", "\u2014", "199%", "85%", "59%", "37%"],
]
story.append(make_table(revenue, [1.8*inch] + [1.2*inch]*5))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Per-test upside: 100K tests/year across 50 QC labs = $10\u201325M opportunity", gold_style))
story.append(PageBreak())

# ---- SLIDE 7: FINANCIAL PROJECTIONS ----
story.append(Paragraph("FINANCIAL PROJECTIONS", section_style))
story.append(Paragraph("Path to $8.7M ARR and 45% Net Margins by Year 5", title_style))
story.append(Spacer(1, 0.15*inch))
fin = [
    ["Metric", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
    ["Revenue", "$727K", "$2.2M", "$4.0M", "$6.4M", "$8.7M"],
    ["Gross Margin", "58%", "68%", "74%", "77%", "78%"],
    ["EBITDA", "($523K)", "$274K", "$1.5M", "$3.2M", "$5.0M"],
    ["Net Margin", "(77%)", "8%", "27%", "39%", "45%"],
    ["Customers", "24", "60", "100", "143", "187"],
]
story.append(make_table(fin, [1.8*inch] + [1.2*inch]*5))
story.append(Spacer(1, 0.15*inch))
unit = [
    ["Metric", "Year 1", "Year 5"],
    ["CAC (fully loaded)", "$18.8K", "$8.5K"],
    ["LTV (3-year, blended)", "$62K", "$102K"],
    ["LTV:CAC", "3.3x", "12.0x"],
    ["Payback period", "14 months", "6 months"],
    ["Annual churn", "15%", "7%"],
]
story.append(make_table(unit, [3*inch, 2*inch, 2*inch]))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("BREAK-EVEN: Month 26  |  ~55 customers  |  $210K MRR", gold_style))
story.append(PageBreak())

# ---- SLIDE 8: COMPETITIVE ADVANTAGES ----
story.append(Paragraph("COMPETITIVE ADVANTAGES", section_style))
story.append(Paragraph("Why K-Dense Wins", title_style))
story.append(Spacer(1, 0.15*inch))
comp = [
    ["Advantage", "K-Dense", "Traditional Labs", "DIY (Python)"],
    ["Speed", "Seconds", "Hours\u2013Days", "Minutes"],
    ["Accuracy", "95\u2013100%", "Variable", "Untested"],
    ["Sample Prep", "None", "Extensive", "N/A"],
    ["Cost per Test", "Low (SaaS)", "$50\u2013200+", "Engineer time"],
    ["Non-Destructive", "Yes", "No", "N/A"],
    ["7-Class Coverage", "Yes", "Yes", "Limited"],
]
story.append(make_table(comp, [2*inch, 2*inch, 2*inch, 2*inch]))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Defensible Moats (Layered)", heading2_style))
moats = [
    "<b>Proprietary dataset</b> \u2014 1,500+ labeled adhesive spectra ($1.2M+ to replicate)",
    "<b>Domain-validated models</b> \u2014 chemically interpretable features confirmed by experts",
    "<b>Compound-grouped validation</b> \u2014 methodology exceeding industry standards",
    "<b>Customer data moat</b> \u2014 switching costs grow with proprietary library indexing",
    "<b>First-mover advantage</b> \u2014 no direct competitor in AI adhesive classification",
]
for i, m in enumerate(moats):
    story.append(Paragraph(f"{i+1}.  {m}", bullet_style))
story.append(PageBreak())

# ---- SLIDE 9: TEAM ----
story.append(Paragraph("TEAM", section_style))
story.append(Paragraph("World-Class Interdisciplinary Team", title_style))
story.append(Spacer(1, 0.15*inch))
team = [
    ["Name", "Role", "Focus"],
    ["Dr. Elena Vasquez", "CEO", "Strategic vision & leadership"],
    ["Dr. Marcus Chen", "Chief Science Officer", "Research coordination"],
    ["Dr. Alexander Petrov", "ML Lead", "Model architecture & deployment"],
    ["Dr. Nikolai Volkov", "Physical Sciences", "Spectroscopy & domain validation"],
    ["Dr. Priya Sharma", "Drug Discovery", "Chemical validation"],
    ["Dr. Lin Wei", "Data Engineering", "Data curation & QA"],
    ["Dr. Rosa Martinez", "Data Visualization", "Publication figures"],
    ["Dr. Paolo Ricci", "Market Research", "Market analysis & intelligence"],
    ["Dr. Sarah Nakamura", "Financial Modeling", "Revenue projections"],
]
story.append(make_table(team, [2.2*inch, 2*inch, 3.5*inch]))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("15+ specialists across ML, chemistry, data science, and business strategy", gold_style))
story.append(PageBreak())

# ---- SLIDE 10: GO-TO-MARKET ----
story.append(Paragraph("GO-TO-MARKET", section_style))
story.append(Paragraph("Land-and-Expand with Design Partners", title_style))
story.append(Spacer(1, 0.15*inch))
partners = [
    ["Target", "Pilot Prob.", "Rationale"],
    ["Evonik Industries", "88%", "Open Innovation (Creavis), digital chemistry"],
    ["Henkel AG", "82%", "World's largest adhesive mfr, Digital R&D"],
    ["Covestro AG", "75%", "Strong digital culture, PU adhesive focus"],
    ["Arkema/Bostik", "70%", "Post-acquisition data integration need"],
    ["3M Company", "64%", "Largest adhesive portfolio"],
]
story.append(make_table(partners, [2.2*inch, 1.5*inch, 4*inch]))
story.append(Spacer(1, 0.15*inch))
phases = [
    ["Phase", "Timeline", "Revenue Target"],
    ["Foundation", "Q1\u2013Q2 2026", "\u2014"],
    ["Design Partners", "Q3\u2013Q4 2026", "$100\u2013150K"],
    ["Enterprise Expansion", "2027", "$1.5\u20132.5M ARR"],
    ["Scale", "2028\u20132030", "$5\u201312M ARR"],
]
story.append(make_table(phases, [2.5*inch, 2*inch, 2.5*inch]))
story.append(Spacer(1, 0.15*inch))
gtm = [
    "95\u2013100% accuracy verifiable in a <b>15-minute live demo</b> with customer spectra",
    "PFAS Reformulation Challenge \u2014 free public dataset drives 5\u201315 inbound inquiries",
    "DREAMS research paper builds scientific credibility",
]
for g in gtm:
    story.append(Paragraph("\u2022  " + g, bullet_style))
story.append(PageBreak())

# ---- SLIDE 11: INVESTMENT ASK ----
story.append(Paragraph("INVESTMENT ASK", section_style))
story.append(Paragraph("$1.5M Seed  \u2192  $5M Series A", title_style))
story.append(Spacer(1, 0.15*inch))
seed = [
    ["Seed Round: $1.5M", "Amount"],
    ["Product development & model optimization", "$600K"],
    ["Initial sales team (2 AEs + SDR)", "$350K"],
    ["Cloud infrastructure & hosting", "$200K"],
    ["Regulatory & compliance (SOC 2, ISO)", "$100K"],
    ["Working capital", "$250K"],
]
story.append(make_table(seed, [5*inch, 1.5*inch]))
story.append(Spacer(1, 0.1*inch))
seriesa = [
    ["Series A: $5M", "Amount"],
    ["Scale engineering (8\u219212 FTEs)", "$2.0M"],
    ["Expand sales & marketing", "$1.5M"],
    ["Enterprise on-prem features", "$800K"],
    ["International market entry", "$500K"],
    ["Working capital", "$200K"],
]
story.append(make_table(seriesa, [5*inch, 1.5*inch]))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Seed Milestones (18 months)", heading2_style))
milestones = [
    "Launch commercial SaaS product (Month 6)",
    "15+ paying customers (Month 12)",
    "$50K MRR (Month 15)",
    "Validate enterprise licensing model (Month 18)",
]
for m in milestones:
    story.append(Paragraph("\u2022  " + m, bullet_style))
story.append(PageBreak())

# ---- SLIDE 12: VISION ----
story.append(Paragraph("VISION", section_style))
story.append(Paragraph("From Lab to Industry Standard", title_style))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph('<i>"Every adhesive bond in every product deserves to be verified \u2014 instantly, accurately, and affordably."</i>', gold_style))
story.append(Spacer(1, 0.3*inch))
vision = [
    "<b>Near-term:</b> Production-ready adhesive classifier with 95\u2013100% accuracy",
    "<b>Medium-term:</b> Industry-standard AI testing platform integrated with major spectrometer brands",
    "<b>Long-term:</b> Universal spectral intelligence platform for material identification across industries",
]
for v in vision:
    story.append(Paragraph("\u2022  " + v, bullet_style))
story.append(Spacer(1, 0.2*inch))
scenario = [
    ["Scenario", "Year 5 ARR", "Assumption"],
    ["Bear", "$1.5M", "Pilot struggles; build-in-house risk"],
    ["Base", "$8.7M", "3 pilots in 2026; steady expansion"],
    ["Bull", "$14M", "PFAS mandate urgency + adjacent verticals"],
]
story.append(make_table(scenario, [1.5*inch, 1.5*inch, 4.5*inch]))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("The opportunity: Transform a $65B+ industry from slow, manual chemistry to instant AI", gold_style))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("K-Dense Science Lab  \u2014  DREAMS Project  \u2014  Dr. Elena Vasquez, CEO", center_green))

# Build
doc = SimpleDocTemplate(output_path, pagesize=(PAGE_W, PAGE_H),
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    topMargin=0.6*inch, bottomMargin=0.5*inch)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

print(f"Saved: {output_path}")
