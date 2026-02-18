"""Extraction endpoint — proxies to Claude API."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user

# Reuse existing extraction logic from the CLI project.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.extractor import extract_from_conversations
from src.models import Conversation as ConvModel, Message as MsgModel

router = APIRouter()


class MessageIn(BaseModel):
    role: str
    text: str


class ConversationIn(BaseModel):
    id: str
    source: str
    title: str
    messages: list[MessageIn]
    started_at: str


class ExtractRequest(BaseModel):
    conversations: list[ConversationIn]


class ExtractResponse(BaseModel):
    results: list[dict]


@router.post("", response_model=ExtractResponse)
async def extract(body: ExtractRequest, user: dict = Depends(get_current_user)):
    if len(body.conversations) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 conversations per request",
        )

    # Convert to internal models.
    convs = [
        ConvModel(
            id=c.id,
            source=c.source,
            title=c.title,
            messages=[MsgModel(role=m.role, text=m.text) for m in c.messages],
            started_at=c.started_at,
        )
        for c in body.conversations
    ]

    try:
        raw_results = extract_from_conversations(convs)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    results = []
    for conv_id, extraction in raw_results:
        results.append({
            "conversation_id": conv_id,
            "extraction": {
                "is_work": extraction.is_work,
                "projects": [
                    {"id": p.id, "name": p.name, "summary": p.summary}
                    for p in extraction.projects
                ],
                "skills": [
                    {"id": s.id, "name": s.name, "category": s.category}
                    for s in extraction.skills
                ],
                "achievements": [
                    {"id": a.id, "summary": a.summary, "impact": a.impact}
                    for a in extraction.achievements
                ],
                "project_skills": extraction.project_skills,
                "project_achievements": extraction.project_achievements,
            },
        })

    return ExtractResponse(results=results)
