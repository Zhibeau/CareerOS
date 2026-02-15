"""LLM-based entity extraction using Claude API.

Classifies conversations as work-relevant and extracts projects, skills, and
achievements in a single API call using tool_use for structured output.
"""

from __future__ import annotations

import json
import os

import anthropic

from src.models import (
    Achievement,
    Conversation,
    ExtractionResult,
    Project,
    Skill,
)

EXTRACTION_TOOL = {
    "name": "store_career_data",
    "description": (
        "Store extracted career data from conversations. "
        "Call this with the structured data you extracted."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "is_work": {
                "type": "boolean",
                "description": (
                    "true if the conversation is about work, projects, "
                    "programming, or technical problem-solving. "
                    "false if it's casual chat, personal questions, "
                    "creative writing, homework, or non-work topics."
                ),
            },
            "projects": {
                "type": "array",
                "description": "Projects or work efforts discussed. Empty if is_work is false.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Short project name inferred from context",
                        },
                        "summary": {
                            "type": "string",
                            "description": "One-line description of what is being built or solved",
                        },
                        "skills": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Technologies/skills used in this project",
                        },
                        "achievements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Concrete accomplishments or problems solved",
                        },
                    },
                    "required": ["name", "summary"],
                },
            },
            "skills": {
                "type": "array",
                "description": "All technologies and skills mentioned. Empty if is_work is false.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Skill name (e.g. 'Python', 'React', 'PostgreSQL')",
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "language",
                                "framework",
                                "tool",
                                "platform",
                                "concept",
                                "soft_skill",
                            ],
                        },
                    },
                    "required": ["name", "category"],
                },
            },
            "achievements": {
                "type": "array",
                "description": (
                    "Concrete accomplishments with measurable impact. "
                    "Empty if is_work is false."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "What was achieved",
                        },
                        "impact": {
                            "type": "string",
                            "description": "Quantified impact if available (e.g. '80% faster')",
                        },
                    },
                    "required": ["summary"],
                },
            },
        },
        "required": ["is_work", "projects", "skills", "achievements"],
    },
}

SYSTEM_PROMPT = """\
You are a career data extraction assistant. You analyze AI chat conversations
and extract structured career-related data.

Your job:
1. Determine if the conversation is work/technical (programming, system design,
   debugging, DevOps, data engineering, etc.) or non-work (casual chat, creative
   writing, personal questions, homework help, etc.).
2. If work-related, extract:
   - Projects: What is being built or worked on? Infer a short project name.
   - Skills: What specific technologies, languages, frameworks, tools are used?
   - Achievements: What concrete problems were solved or outcomes achieved?
3. If NOT work-related, set is_work=false and return empty arrays.

Important:
- Do NOT invent or guess job titles, companies, or role information.
- Do NOT extract skills that were only mentioned in passing by the assistant.
  Only extract skills the USER is actively working with.
- Achievements should be concrete ("fixed memory leak reducing usage by 40%"),
  not vague ("learned about databases").
- Project names should be short and descriptive ("E-commerce API", "Dashboard UI").
"""


def _format_conversation(conv: Conversation) -> str:
    """Format a conversation into a readable string for the LLM."""
    lines = [f"Title: {conv.title}", f"Date: {conv.started_at}", "---"]
    for msg in conv.messages:
        prefix = "User" if msg.role == "user" else "Assistant"
        # Truncate very long messages to manage tokens
        text = msg.text[:2000] if len(msg.text) > 2000 else msg.text
        lines.append(f"{prefix}: {text}")
    return "\n".join(lines)


def _parse_tool_result(tool_input: dict) -> ExtractionResult:
    """Parse the tool_use response into an ExtractionResult."""
    is_work = tool_input.get("is_work", False)

    projects = [
        Project(name=p["name"], summary=p["summary"])
        for p in tool_input.get("projects", [])
    ]
    skills = [
        Skill(name=s["name"], category=s["category"])
        for s in tool_input.get("skills", [])
    ]
    achievements = [
        Achievement(summary=a["summary"], impact=a.get("impact"))
        for a in tool_input.get("achievements", [])
    ]

    # Build project→skill and project→achievement link maps
    project_skills: dict[str, list[str]] = {}
    project_achievements: dict[str, list[str]] = {}
    for p in tool_input.get("projects", []):
        if p.get("skills"):
            project_skills[p["name"]] = p["skills"]
        if p.get("achievements"):
            project_achievements[p["name"]] = p["achievements"]

    return ExtractionResult(
        is_work=is_work,
        projects=projects,
        skills=skills,
        achievements=achievements,
        project_skills=project_skills,
        project_achievements=project_achievements,
    )


def extract_from_conversations(
    conversations: list[Conversation],
    batch_size: int = 5,
    model: str = "claude-sonnet-4-5-20250929",
) -> list[tuple[str, ExtractionResult]]:
    """Extract career data from conversations using Claude API.

    Returns a list of (conversation_id, ExtractionResult) tuples.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is required. "
            "Set it with: export ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)
    results: list[tuple[str, ExtractionResult]] = []

    # Process in batches
    for i in range(0, len(conversations), batch_size):
        batch = conversations[i : i + batch_size]

        for conv in batch:
            formatted = _format_conversation(conv)

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[EXTRACTION_TOOL],
                tool_choice={"type": "tool", "name": "store_career_data"},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Analyze this conversation and extract career data. "
                            "Use the store_career_data tool to return your results.\n\n"
                            f"{formatted}"
                        ),
                    }
                ],
            )

            # Find the tool_use block in the response
            for block in response.content:
                if block.type == "tool_use" and block.name == "store_career_data":
                    result = _parse_tool_result(block.input)
                    results.append((conv.id, result))
                    break

    return results
