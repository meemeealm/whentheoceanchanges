from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .schemas import ChartContext


AUDIENCE_INSTRUCTIONS = {
    "eli5": (
        "Use very simple everyday language with short sentences and simple analogies. "
        "Explain only the most obvious pattern. Avoid technical or statistical terms."
    ),
    "general": (
        "Use clear, accessible, and balanced language. "
        "Focus on the main findings, important comparisons, and key patterns."
    ),
    "scientist": (
        "Use precise analytical language. "
        "Focus on quantitative metrics, anomalies, and data trends using technical terms where appropriate."
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


def build_system_prompt(audience: str) -> str:
    style = (audience or "general").strip().lower()
    audience_instruction = AUDIENCE_INSTRUCTIONS.get(style, AUDIENCE_INSTRUCTIONS["general"])

    return f"""
You are a climate data analyst writing a brief chart explanation.

Strict Guidelines:
1. Use ONLY the supplied evidence data. Do NOT invent numbers or facts.
2. Do NOT make causal claims unless explicit in the evidence.
3. Explicitly mention the target region/scope.
4. Keep output concise: "explanation" should be 2-3 short sentences (approx 40 words); "takeaway" should be 1 short sentence (approx 15 words).
5. Output MUST be valid JSON matching the exact schema below. Do not use Markdown formatting or code blocks.

Audience Style Directives:
{audience_instruction}

Target JSON Format:
{{
  "explanation": "Brief context and pattern analysis.",
  "takeaway": "Key takeaway sentence."
}}
""".strip()


def build_prompt_bundle(
    context: ChartContext,
    evidence: dict[str, Any],
) -> PromptBundle:

    # 1. Generate base system prompt containing instructions & audience directive
    system_base = build_system_prompt(getattr(context, "audience", "general"))
    
    # 2. Get specific chart focus instruction
    chart_instruction = CHART_INSTRUCTIONS.get(context.chart_id, CHART_INSTRUCTIONS["heatmap"])

    # 3. Assemble full system instruction without redundant string duplication
    system_instruction = f"{system_base}\n\nChart Focus Area:\n{chart_instruction}"

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