"""Render CV content dict to DOCX bytes using python-docx."""

from __future__ import annotations

import io

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def render_docx(cv: dict) -> bytes:
    """Render structured CV content to DOCX bytes."""
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Name
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_para.add_run(cv.get("name_placeholder", "[Your Name]"))
    name_run.font.size = Pt(20)
    name_run.font.bold = True

    # Contact
    contact_para = doc.add_paragraph()
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_run = contact_para.add_run(
        cv.get("contact_placeholder", "[email] | [phone] | [location]")
    )
    contact_run.font.size = Pt(10)
    contact_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # Summary
    summary = cv.get("summary", "")
    if summary:
        _add_section_heading(doc, "PROFESSIONAL SUMMARY")
        doc.add_paragraph(summary)

    # Experience
    experience = cv.get("experience", [])
    if experience:
        _add_section_heading(doc, "EXPERIENCE")
        for role in experience:
            # Title + Company
            role_para = doc.add_paragraph()
            title_run = role_para.add_run(
                f"{role.get('title', '')} — {role.get('company', '')}"
            )
            title_run.font.bold = True
            title_run.font.size = Pt(11)

            # Dates
            dates_para = doc.add_paragraph()
            dates_run = dates_para.add_run(role.get("dates", ""))
            dates_run.font.size = Pt(9)
            dates_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

            # Bullets
            for bullet in role.get("bullets", []):
                bullet_para = doc.add_paragraph(style="List Bullet")
                bullet_run = bullet_para.add_run(bullet)
                bullet_run.font.size = Pt(10)

    # Skills
    skills = cv.get("skills", {})
    if skills:
        _add_section_heading(doc, "SKILLS")
        for category, items in skills.items():
            skill_para = doc.add_paragraph()
            cat_run = skill_para.add_run(f"{category}: ")
            cat_run.font.bold = True
            cat_run.font.size = Pt(10)
            if isinstance(items, list):
                skill_para.add_run(", ".join(items)).font.size = Pt(10)
            else:
                skill_para.add_run(str(items)).font.size = Pt(10)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _add_section_heading(doc: Document, text: str) -> None:
    """Add a styled section heading with an underline."""
    para = doc.add_paragraph()
    para.space_before = Pt(14)
    para.space_after = Pt(6)
    run = para.add_run(text)
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
