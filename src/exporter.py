# src/exporter.py
import os
from datetime import datetime
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Brand colors ──────────────────────────────────────────────────────────────

BLUE       = colors.HexColor("#2563EB")
BLUE_LIGHT = colors.HexColor("#EFF6FF")
BLUE_MID   = colors.HexColor("#BFDBFE")
GRAY_900   = colors.HexColor("#111827")
GRAY_600   = colors.HexColor("#4B5563")
GRAY_400   = colors.HexColor("#9CA3AF")
GRAY_100   = colors.HexColor("#F3F4F6")
WHITE      = colors.white


def generate_pdf(
    query:     str,
    standards: List[Dict],
    output_path: str = None,
) -> str:
    """
    Generate a compliance report PDF.
    Returns the output path.
    """
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.dirname(__file__), "..", "data",
            f"BIS_Report_{ts}.pdf"
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    # ── Styles ────────────────────────────────────────────────────────────────

    styles = getSampleStyleSheet()

    style_h1 = ParagraphStyle(
        "h1",
        fontSize=20,
        textColor=GRAY_900,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    style_h2 = ParagraphStyle(
        "h2",
        fontSize=12,
        textColor=BLUE,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
    )
    style_h3 = ParagraphStyle(
        "h3",
        fontSize=10,
        textColor=GRAY_900,
        fontName="Helvetica-Bold",
        spaceAfter=3,
    )
    style_body = ParagraphStyle(
        "body",
        fontSize=9,
        textColor=GRAY_600,
        fontName="Helvetica",
        leading=14,
        spaceAfter=4,
    )
    style_meta = ParagraphStyle(
        "meta",
        fontSize=8,
        textColor=GRAY_400,
        fontName="Helvetica",
        leading=12,
    )
    style_label = ParagraphStyle(
        "label",
        fontSize=7,
        textColor=BLUE,
        fontName="Helvetica-Bold",
        spaceAfter=2,
        leading=10,
    )
    style_rationale = ParagraphStyle(
        "rationale",
        fontSize=9,
        textColor=colors.HexColor("#1E40AF"),
        fontName="Helvetica-Oblique",
        leading=14,
        spaceAfter=4,
        leftIndent=8,
        rightIndent=8,
    )
    style_center = ParagraphStyle(
        "center",
        fontSize=9,
        textColor=GRAY_400,
        fontName="Helvetica",
        alignment=TA_CENTER,
    )
    style_query = ParagraphStyle(
        "query",
        fontSize=10,
        textColor=GRAY_900,
        fontName="Helvetica-Oblique",
        leading=15,
        leftIndent=10,
        rightIndent=10,
    )

    # ── Build content ─────────────────────────────────────────────────────────

    story = []
    now   = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Header block
    story.append(Paragraph("BIS Copilot", style_h1))
    story.append(Paragraph("Compliance Standards Report", ParagraphStyle(
        "sub", fontSize=13, textColor=GRAY_400,
        fontName="Helvetica", spaceAfter=2,
    )))
    story.append(Paragraph(f"Generated on {now}", style_meta))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 4*mm))

    # Query block
    story.append(Paragraph("PRODUCT / COMPLIANCE QUERY", style_label))
    story.append(Paragraph(f'"{query}"', style_query))
    story.append(Spacer(1, 2*mm))

    # Summary table
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_100))
    story.append(Spacer(1, 2*mm))

    summary_data = [["#", "IS Code", "Title", "Section"]]
    for i, s in enumerate(standards, 1):
        title_short = s["title"].title()
        if len(title_short) > 50:
            title_short = title_short[:47] + "..."
        summary_data.append([
            str(i),
            s["is_code"],
            title_short,
            s["section_name"],
        ])

    summary_table = Table(
        summary_data,
        colWidths=[10*mm, 38*mm, 80*mm, 42*mm],
    )
    summary_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",  (0, 0), (-1, 0),  BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",  (0, 0), (-1, 0),  6),
        # Data rows
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("TEXTCOLOR",   (0, 1), (-1, -1), GRAY_600),
        ("TOPPADDING",  (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        # Alternating rows
        *[("BACKGROUND", (0, i), (-1, i), GRAY_100)
          for i in range(2, len(summary_data), 2)],
        # IS code column bold blue
        ("TEXTCOLOR",   (1, 1), (1, -1),  BLUE),
        ("FONTNAME",    (1, 1), (1, -1),  "Helvetica-Bold"),
        # Grid
        ("LINEBELOW",   (0, 0), (-1, 0),  0.5, BLUE_MID),
        ("LINEBELOW",   (0, 1), (-1, -1), 0.3, GRAY_100),
        ("ROWBACKGROUNDS", (0, 0), (-1, 0), [BLUE]),
    ]))

    story.append(Paragraph("RECOMMENDED STANDARDS — SUMMARY", style_label))
    story.append(Spacer(1, 1*mm))
    story.append(summary_table)
    story.append(Spacer(1, 4*mm))

    # Detailed cards
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_100))
    story.append(Paragraph("DETAILED STANDARD PROFILES", style_h2))

    for i, s in enumerate(standards, 1):
        story.append(Spacer(1, 3*mm))

        # Standard header row
        header_data = [[
            Paragraph(f"{i}", ParagraphStyle(
                "rank", fontSize=11, textColor=WHITE,
                fontName="Helvetica-Bold", alignment=TA_CENTER,
            )),
            Paragraph(s["is_code"], ParagraphStyle(
                "code", fontSize=11, textColor=WHITE,
                fontName="Helvetica-Bold",
            )),
            Paragraph(s["section_name"], ParagraphStyle(
                "sec", fontSize=8, textColor=BLUE_MID,
                fontName="Helvetica", alignment=TA_RIGHT,
            )),
        ]]
        header_table = Table(header_data, colWidths=[10*mm, 110*mm, 50*mm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BLUE),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(header_table)

        # Title
        story.append(Table(
            [[Paragraph(s["title"].title(), style_h3)]],
            colWidths=[170*mm],
            style=TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), BLUE_LIGHT),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ])
        ))

        # Body
        body_rows = []

        # Rationale
        if s.get("rationale"):
            body_rows.append(
                Paragraph("WHY THIS APPLIES", style_label)
            )
            body_rows.append(
                Paragraph(s["rationale"], style_rationale)
            )
            body_rows.append(Spacer(1, 2*mm))

        # Scope
        body_rows.append(Paragraph("SCOPE", style_label))
        body_rows.append(Paragraph(s["scope"], style_body))

        # Meta row
        meta_parts = []
        if s.get("year"):
            meta_parts.append(f"Year: {s['year']}")
        if s.get("subcategory") and s["subcategory"] not in ("Foreword", "Contents"):
            meta_parts.append(f"Category: {s['subcategory']}")
        meta_parts.append(f"Relevance Score: {s['rrf_score']:.4f}")
        body_rows.append(Paragraph("  ·  ".join(meta_parts), style_meta))

        body_table = Table(
            [[row] for row in body_rows],
            colWidths=[170*mm],
        )
        body_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("LINEBELOW",     (0, -1), (-1, -1), 0.5, GRAY_100),
        ]))
        story.append(body_table)

    # Footer
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_100))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Generated by BIS Copilot · AI-powered compliance discovery for Indian MSEs · "
        "Based on BIS SP 21 : 2005",
        style_center,
    ))

    doc.build(story)
    return output_path


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with mock data
    mock_standards = [
        {
            "is_code":      "IS 269 : 1989",
            "title":        "ORDINARY PORTLAND CEMENT, 33 GRADE",
            "scope":        "Covers the manufacture and chemical and physical requirements of 33 grade ordinary Portland cement.",
            "section_name": "Cement and Concrete",
            "subcategory":  "Cement",
            "year":         1989,
            "rrf_score":    0.032787,
            "rationale":    "This standard directly governs your 33 grade OPC product, covering all chemical composition and physical performance requirements you must meet for compliance.",
        },
        {
            "is_code":      "IS 8112 : 1989",
            "title":        "43 GRADE ORDINARY PORTLAND CEMENT",
            "scope":        "Manufacture, chemical and physical requirements of 43 grade ordinary Portland cement.",
            "section_name": "Cement and Concrete",
            "subcategory":  "Cement",
            "year":         1989,
            "rrf_score":    0.030258,
            "rationale":    "If you plan to upgrade production to 43 grade OPC, this standard defines the higher strength requirements you would need to meet.",
        },
    ]

    path = generate_pdf(
        query="We manufacture 33 grade ordinary Portland cement",
        standards=mock_standards,
    )
    print(f"✓ PDF generated: {path}")