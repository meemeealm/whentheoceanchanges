from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .schemas import ChartContext

AUDIENCE_INSTRUCTIONS = {
    "eli5": (
        "Use very simple language, short sentences, and intuitive explanations. "
        "Avoid technical jargon unless the chart data truly requires it."
    ),
    "general": (
        "Use clear scientific language, be concise, and focus on the main trend and why it matters."
    ),
    "scientist": (
        "Use precise terminology, quantify the pattern where possible, and mention uncertainty or limits when relevant."
    ),
}

CHART_INSTRUCTIONS = {
    "trend-chart": (
        "Explain the relationship between sea level and sea temperature over time for the selected region or Pacific overall."
    ),
    "bubble-chart": (
        "Explain the scatter/bubble pattern in cyclone counts, people affected, and economic loss for the selected period."
    ),
    "cyclone-chart": (
        "Explain the cyclone distribution over years and countries for the selected region or all countries."
    ),
}


@dataclass(frozen=True)
class PromptBundle:
    system_instruction: str
    user_prompt: str


def build_prompt_bundle(context: ChartContext, evidence: dict[str, Any]) -> PromptBundle:
    audience_instruction = AUDIENCE_INSTRUCTIONS[context.audience]
    chart_instruction = CHART_INSTRUCTIONS[context.chart_id]

    system_instruction = (
        "You are writing a climate-chart explanation for a frontend app. "
        "Use only the supplied evidence. Do not invent numbers, causes, or missing facts. "
        "If the evidence shows association rather than causation, say that the chart shows or suggests a pattern instead of claiming proof. "
        "Return only JSON that matches the provided schema.\n\n"
        f"Audience style: {audience_instruction}\n"
        f"Chart focus: {chart_instruction}"
    )

    user_prompt = json.dumps(
        {
            "chart_context": context.model_dump(),
            "evidence": evidence,
        },
        indent=2,
        sort_keys=True,
    )

    return PromptBundle(system_instruction=system_instruction, user_prompt=user_prompt)

