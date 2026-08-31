from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .schemas import ChartContext


AUDIENCE_INSTRUCTIONS = {
    "eli5": {
        "style": "very simple and intuitive",
        "focus": "the easiest-to-understand key takeaway",
        "language": "everyday language",
        "avoid": [
            "technical terminology",
            "statistical jargon",
            "unsupported causal explanations",
        ],
        "priority": [
            "what happened",
            "who or what was most affected",
            "simple surprising comparisons",
        ],
    },

    "general": {
        "style": "clear and accessible",
        "focus": "main finding and important comparisons",
        "language": "plain but informative",
        "avoid": [
            "unnecessary technical jargon",
            "overly detailed methodology",
        ],
        "priority": [
            "key takeaway",
            "notable pattern",
            "important comparison",
            "context",
        ],
    },

    "scientist": {
        "style": "precise and analytical",
        "focus": "quantitative findings and relationships",
        "language": "scientific terminology where appropriate",
        "avoid": [
            "unsupported causal claims",
            "overinterpretation",
            "vague statements",
        ],
        "priority": [
            "effect magnitude",
            "comparisons",
            "trends",
            "anomalies",
            "limitations",
        ],
    },
}


CHART_INSTRUCTIONS = {
    "trend-chart": (
        "Explain the relationship between sea level and sea temperature "
        "over time for the selected region or Pacific overall."
    ),

    "bubble-chart": (
        "Explain the scatter/bubble pattern in cyclone counts, "
        "people affected, and economic loss for the selected period."
    ),

    "heatmap": (
        "Explain the distribution over years and countries "
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

    selected_region = evidence.get("scope")

    system_instruction = f"""
You are writing a concise climate-chart explanation for a frontend application.

Use ONLY the supplied evidence.
Do not invent numbers, causes, or facts.

SELECTED REGION:
{selected_region}

IMPORTANT REGION RULE:
- The selected region is "{selected_region}".
- You MUST explicitly mention "{selected_region}" in the explanation.
- Do NOT replace the selected region with "Pacific Overall".
- Do NOT describe all countries when a specific region is selected.
- Use only data belonging to the selected region when the evidence is region-specific.

WRITING RULES:
- Lead with a clear key takeaway sentence that captures the primary conclusion.
- Follow the key takeaway with a thorough, well-developed explanation of the chart findings.
- Target length: 500 words (up to 2,000 characters).
- Include specific trends, notable data points, and context provided in the evidence.
- Describe the primary trend or pattern first, then support it with observed evidence.
- Prefer absolute changes and observed trends.
- Do not emphasize percentage changes when the starting value is near zero.
- Do not make unsupported causal claims.
- Do not mention information that is not present in the evidence.

AUDIENCE:
{json.dumps(audience_instruction, ensure_ascii=False)}

CHART FOCUS:
{chart_instruction}

OUTPUT FORMAT:
Return only a single plain-text paragraph containing the explanation.
The first sentence must serve as the key takeaway.
Do not wrap in JSON.
Do not include code fences or markdown formatting.
""".strip()

    user_prompt = json.dumps(
        {
            "chart_context": context.model_dump(),
            "evidence": evidence,
        },
        indent=2,
        sort_keys=True,
    )

    return PromptBundle(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
    )