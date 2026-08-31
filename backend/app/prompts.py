from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .schemas import ChartContext


AUDIENCE_INSTRUCTIONS = {
    "eli5": (
        "Use very simple everyday language. "
        "Explain only the most important pattern. "
        "Avoid technical and statistical jargon."
    ),
    "general": (
        "Use clear, accessible language. "
        "Focus on the main finding, important comparisons, and notable patterns."
    ),
    "scientist": (
        "Use precise analytical language. "
        "Focus on quantitative findings, trends, comparisons, anomalies, and limitations. "
        "Do not make unsupported causal claims."
    ),
}


CHART_INSTRUCTIONS = {
    "trend-chart": (
        "Explain the relationship between sea level and sea temperature over time "
        "for the selected region."
    ),
    "bubble-chart": (
        "Explain the relationship and notable patterns among cyclone counts, "
        "people affected, and economic loss for the selected period."
    ),
    "heatmap": (
        "Explain the distribution of cyclone activity across countries and years "
        "for the selected region or all countries."
    ),
    "cyclone-chart": (
        "Explain the distribution of cyclone activity across countries and years "
        "for the selected region or all countries."
    ),
}


@dataclass(frozen=True)
class PromptBundle:
    system_instruction: str
    user_prompt: str


def build_prompt_bundle(
    context: ChartContext,
    evidence: dict[str, Any],
) -> PromptBundle:

    audience_instruction = AUDIENCE_INSTRUCTIONS[context.audience]
    chart_instruction = CHART_INSTRUCTIONS[context.chart_id]

    system_instruction = f"""
You are a climate data analyst writing a short explanation for a frontend application.

You MUST follow these rules:

1. Use ONLY the supplied evidence.
2. Do NOT invent numbers or facts.
3. Do NOT make causal claims unless the evidence explicitly supports causation.
4. Explicitly mention the selected scope/region when possible.
5. Focus on the strongest observable pattern.
6. Keep the explanation concise.
7. The "explanation" MUST be 300 characters or fewer.
8. The "takeaway" MUST be 200 characters or fewer.
9. Return ONLY valid JSON.
10. Do not use markdown.
11. Do not add fields other than "explanation" and "takeaway".

Audience:
{audience_instruction}

Chart:
{chart_instruction}

The required JSON structure is:

{{
  "explanation": "short explanation",
  "takeaway": "short key takeaway"
}}
""".strip()

    user_prompt = json.dumps(
        {
            "chart_context": context.model_dump(),
            "evidence": evidence,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return PromptBundle(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
    )
