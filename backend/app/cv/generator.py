"""Generate CV content using Claude API."""

from __future__ import annotations

import json
import os

import anthropic

from app.config import settings

_SYSTEM_PROMPT = """\
You are a professional CV/resume writer. Given structured career data and a job
description, generate polished CV content tailored to the role.

Output a JSON object with these sections:
{
  "name_placeholder": "[Your Name]",
  "contact_placeholder": "[email] | [phone] | [location]",
  "summary": "2-3 sentence professional summary tailored to the JD",
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "dates": "Start — End",
      "bullets": ["Achievement-focused bullet point...", ...]
    }
  ],
  "skills": {
    "Languages": ["Python", "JavaScript", ...],
    "Frameworks": ["React", "FastAPI", ...],
    ...
  }
}

Guidelines:
- Use strong action verbs (Led, Designed, Implemented, Optimized, etc.)
- Include quantified impact where available
- Tailor content to match the job description keywords
- Keep bullets concise (one line each)
- 3-5 bullets per role
- Group skills by category
"""


def generate_cv_content(career_data: dict, job_description: str) -> dict:
    """Call Claude to generate structured CV content."""
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate a tailored CV based on this data.\n\n"
                    f"## Career Data\n```json\n{json.dumps(career_data, indent=2)}\n```\n\n"
                    f"## Job Description\n{job_description}\n\n"
                    f"Return ONLY the JSON object, no markdown fences."
                ),
            }
        ],
    )

    text = response.content[0].text.strip()
    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[: -len("```")]

    return json.loads(text)
