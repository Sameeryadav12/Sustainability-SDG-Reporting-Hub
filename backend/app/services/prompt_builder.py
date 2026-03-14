"""
Prompt building for AI report section generation (Step 11).

Structured system instruction and user context so the model writes formal report text from project data only.
"""

import json
from typing import Any


def build_system_instruction() -> str:
    """System message: role and constraints for the report writer."""
    return """You are writing a formal university sustainability report section. Your task is to produce professional, factual report text.

Rules:
- Use ONLY the facts and data provided in the user message. Do not invent or assume any data.
- Write in a professional, concise, formal tone suitable for an official sustainability report.
- Organize the section clearly (e.g. short intro, key points, outcomes where supported by data).
- Mention outcomes and impact only when clearly supported by the provided data.
- If the provided data is limited, write a short conservative section; do not fill with generic or invented content.
- Output valid Markdown only (headings, lists, paragraphs). No meta-commentary."""


def build_user_context(
    reporting_cycle_name: str,
    reporting_year: int,
    scope_type: str,
    scope_value: str,
    scope_metadata: dict[str, Any],
    contributions_summary: list[dict[str, Any]],
    analytics_summary: dict[str, Any] | None,
    target_word_count: int,
) -> str:
    """
    Build the user message: structured JSON-like context block plus instruction.
    """
    block = {
        "reporting_cycle": {"name": reporting_cycle_name, "year": reporting_year},
        "scope": {"type": scope_type, "value": scope_value},
        "scope_metadata": scope_metadata,
        "contributions": contributions_summary,
        "analytics_summary": analytics_summary,
        "target_word_count": target_word_count,
    }
    data_str = json.dumps(block, indent=2, default=str)
    return f"""Based on the following project data only, write a report section of approximately {target_word_count} words. Use only the data below; do not invent anything.

## Data

{data_str}

## Output

Write the report section in Markdown. Output nothing else."""
