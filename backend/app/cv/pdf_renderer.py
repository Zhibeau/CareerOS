"""Render CV content dict to PDF bytes using ReportLab."""

from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)


def render_pdf(cv: dict) -> bytes:
    """Render structured CV content to PDF bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    name_style = ParagraphStyle(
        "CVName",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "CVContact",
        parent=styles["Normal"],
        fontSize=10,
        textColor="#666666",
        alignment=1,  # center
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "CVSection",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=6,
        textColor="#1a1a1a",
        borderWidth=0,
        borderPadding=0,
    )
    role_style = ParagraphStyle(
        "CVRole",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )
    dates_style = ParagraphStyle(
        "CVDates",
        parent=styles["Normal"],
        fontSize=9,
        textColor="#666666",
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "CVBullet",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=12,
        bulletIndent=0,
        spaceAfter=3,
    )
    skill_style = ParagraphStyle(
        "CVSkill",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=2,
    )

    story = []

    # Name + contact
    story.append(Paragraph(cv.get("name_placeholder", "[Your Name]"), name_style))
    story.append(
        Paragraph(cv.get("contact_placeholder", "[email] | [phone]"), contact_style)
    )

    # Summary
    summary = cv.get("summary", "")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(Paragraph(summary, styles["Normal"]))

    # Experience
    experience = cv.get("experience", [])
    if experience:
        story.append(Paragraph("EXPERIENCE", section_style))
        for role in experience:
            title_company = f"{role.get('title', '')} — {role.get('company', '')}"
            story.append(Paragraph(title_company, role_style))
            story.append(Paragraph(role.get("dates", ""), dates_style))
            for bullet in role.get("bullets", []):
                story.append(
                    Paragraph(f"\u2022 {bullet}", bullet_style)
                )
            story.append(Spacer(1, 4))

    # Skills
    skills = cv.get("skills", {})
    if skills:
        story.append(Paragraph("SKILLS", section_style))
        for category, items in skills.items():
            if isinstance(items, list):
                text = f"<b>{category}:</b> {', '.join(items)}"
            else:
                text = f"<b>{category}:</b> {items}"
            story.append(Paragraph(text, skill_style))

    doc.build(story)
    return buffer.getvalue()
