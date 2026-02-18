"""CV generation endpoints: preview, render, and combined generate."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.cv.generator import generate_cv_content
from app.cv.pdf_renderer import render_pdf
from app.cv.docx_renderer import render_docx

router = APIRouter()


# ── Request models ──────────────────────────────────────────────────


class CVPreviewRequest(BaseModel):
    career_data: dict
    job_description: str


class CVRenderRequest(BaseModel):
    cv_content: dict
    format: str  # "pdf" or "docx"


class CVRequest(BaseModel):
    career_data: dict
    job_description: str
    format: str  # "pdf" or "docx"


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("/preview")
async def preview_cv(
    body: CVPreviewRequest, user: dict = Depends(get_current_user)
):
    """Generate structured CV content (JSON) for in-app preview."""
    try:
        cv_content = generate_cv_content(
            career_data=body.career_data,
            job_description=body.job_description,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV generation failed: {e}")

    return cv_content


@router.post("/render")
async def render_cv(
    body: CVRenderRequest, user: dict = Depends(get_current_user)
):
    """Render previously generated CV content to PDF or DOCX bytes."""
    if body.format not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'")

    try:
        if body.format == "pdf":
            file_bytes = render_pdf(body.cv_content)
            media_type = "application/pdf"
            filename = "CareerOS_CV.pdf"
        else:
            file_bytes = render_docx(body.cv_content)
            media_type = (
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            )
            filename = "CareerOS_CV.docx"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV rendering failed: {e}")

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/generate")
async def generate_cv(body: CVRequest, user: dict = Depends(get_current_user)):
    """Combined: generate CV content and render to file in one call."""
    if body.format not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'")

    try:
        cv_content = generate_cv_content(
            career_data=body.career_data,
            job_description=body.job_description,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV generation failed: {e}")

    if body.format == "pdf":
        file_bytes = render_pdf(cv_content)
        media_type = "application/pdf"
        filename = "CareerOS_CV.pdf"
    else:
        file_bytes = render_docx(cv_content)
        media_type = (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )
        filename = "CareerOS_CV.docx"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
