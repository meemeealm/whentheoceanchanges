from __future__ import annotations

import json
import re
import os
from typing import Any

from groq import Groq, GroqError

from .prompts import build_prompt_bundle
from .schemas import ChartContext, ExplanationResponse

from dotenv import load_dotenv

load_dotenv()

GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _clean_model_output(content: str) -> str:
    # Strip accidental markdown fences before attempting to parse JSON.
    return re.sub(r"^```\w*\n?|\n?```$", "", content.strip()).strip()


def _fallback_response(
    context: ChartContext,
    evidence: dict[str, Any],
) -> ExplanationResponse:
    data = evidence.get("data") or {}
    scope = evidence.get("scope") or "the selected scope"

    if context.chart_id == "trend-chart":
        sea_level = data.get("series", {}).get("sea_level", {})
        temperature = data.get("series", {}).get("temperature", {})
        year_range = data.get("year_range", {})

        explanation = (
            f"{scope} shows a {sea_level.get('trend', 'mixed')} sea-level pattern "
            f"and a {temperature.get('trend', 'mixed')} temperature pattern "
            f"from {year_range.get('start', 'the start')} to {year_range.get('end', 'the end')}."
        )
        takeaway = (
            f"The selected period in {scope} points to a clear long-term shift."
        )
        return ExplanationResponse(
            explanation=explanation,
            takeaway=takeaway,
        )

    if context.chart_id == "bubble-chart":
        totals = data.get("totals", {})
        correlations = data.get("correlations", {})

        explanation = (
            f"In {scope}, the chart totals {totals.get('cyclone_count', 0)} cyclones, "
            f"{totals.get('people_affected', 0)} people affected, and "
            f"${totals.get('economic_loss', 0):,.2f} in economic loss. "
            f"Cyclones and people affected are correlated at "
            f"{correlations.get('cyclones_vs_people_affected')}"
            "."
        )
        takeaway = (
            f"In {scope}, bigger cyclone totals line up with higher impact."
        )
        return ExplanationResponse(
            explanation=explanation,
            takeaway=takeaway,
        )

    if context.chart_id in {"heatmap", "cyclone-chart"}:
        peak_year = data.get("peak_year", {})
        quiet_year = data.get("quiet_year", {})
        top_countries = data.get("top_countries") or []
        top_country = top_countries[0]["country"] if top_countries else "the leading country"

        explanation = (
            f"In {scope}, cyclone activity peaks in {peak_year.get('year', 'one year')} "
            f"and is lowest in {quiet_year.get('year', 'another year')}, with "
            f"{top_country} among the most active countries."
        )
        takeaway = (
            f"Cyclone activity is concentrated in a few places and peak years."
        )
        return ExplanationResponse(
            explanation=explanation,
            takeaway=takeaway,
        )

    return ExplanationResponse(
        explanation="The chart shows a clear pattern in the selected data.",
        takeaway="The selected data contains a notable trend.",
    )


def _parse_explanation_response(content: str) -> ExplanationResponse:
    clean_text = _clean_model_output(content)

    if not clean_text:
        raise ValueError("empty_generation")

    try:
        payload = json.loads(clean_text)
    except json.JSONDecodeError:
        return ExplanationResponse(
            explanation=clean_text,
            takeaway="",
        )

    if not isinstance(payload, dict):
        return ExplanationResponse(
            explanation=clean_text,
            takeaway="",
        )

    explanation = payload.get("explanation", "")
    takeaway = payload.get("takeaway", "")

    if not isinstance(explanation, str):
        explanation = clean_text

    if not isinstance(takeaway, str):
        takeaway = ""

    return ExplanationResponse(
        explanation=explanation,
        takeaway=takeaway,
    )


def generate_explanation(
    context: ChartContext,
    evidence: dict[str, Any],
) -> ExplanationResponse:
    prompt_bundle = build_prompt_bundle(context, evidence)

    print(
        "Groq request started:",
        {
            "model": "openai/gpt-oss-20b",
            "scope": evidence.get("scope"),
            "timeout_seconds": 45,
        },
        flush=True,
    )

    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": prompt_bundle.system_instruction},
                {"role": "user", "content": prompt_bundle.user_prompt},
            ],
            temperature=0.2,
            max_tokens=256,
            timeout=15,
            # DO NOT pass response_format={"type": "json_object"} here
        )

        content = response.choices[0].message.content or ""
        if not content.strip():
            print(
                "Groq returned empty content; using evidence-based fallback.",
                flush=True,
            )
            return _fallback_response(context, evidence)

        try:
            return _parse_explanation_response(content)
        except ValueError:
            print(
                "Groq returned empty content; using evidence-based fallback.",
                flush=True,
            )
            return _fallback_response(context, evidence)
        except Exception as exc:
            print(
                f"Groq output could not be parsed; using fallback: {exc}",
                flush=True,
            )
            return _fallback_response(context, evidence)

    except GroqError as exc:
        print("Groq exception:", exc, flush=True)
        raise RuntimeError(f"Groq API call failed: {exc}") from exc
