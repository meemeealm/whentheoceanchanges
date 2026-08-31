from __future__ import annotations

import json
import re
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq, GroqError

from .prompts import CHART_INSTRUCTIONS, build_system_prompt
from .schemas import ChartContext, ExplanationResponse


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL", "").strip()
REQUEST_TIMEOUT = 15

GROQ_CLIENT = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_model_output(content: str) -> str:
    """Remove accidental Markdown code fences."""
    text = (content or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


def _extract_json_object(content: str) -> str:
    """
    Extract a JSON object even if the model accidentally adds
    text before or after it.
    """

    clean = _clean_model_output(content)

    if not clean:
        return ""

    if clean.startswith("{") and clean.endswith("}"):
        return clean

    start = clean.find("{")
    end = clean.rfind("}")

    if start != -1 and end != -1 and end > start:
        return clean[start:end + 1]

    return clean


def _get_audience(context: ChartContext) -> str:
    """
    ChartContext validates audience to:
        eli5
        general
        scientist
    """

    audience = getattr(context, "audience", "general")

    if not audience:
        return "general"

    audience = str(audience).strip().lower()

    if audience not in {"eli5", "general", "scientist"}:
        return "general"

    return audience


def _get_audience_instructions(audience: str) -> str:
    """
    Strongly differentiate the three audiences.
    """

    if audience == "eli5":
        return """
AUDIENCE: ELI5

Explain the chart to a complete beginner.

Use:
- Very simple everyday language.
- Short, clear sentences.
- Simple explanations of numbers.
- Intuitive descriptions of trends.
- No unnecessary technical terminology.

Avoid:
- Scientific jargon.
- Advanced statistics.
- Methodology details.
- Assuming prior knowledge.

Focus on:
"What is happening in this chart, in simple words?"
""".strip()

    if audience == "scientist":
        return """
AUDIENCE: SCIENTIST

Explain the chart to a scientifically literate audience.

Use:
- Precise analytical terminology.
- Quantitative comparisons.
- Numerical patterns.
- Temporal or spatial patterns.
- Correlations or relationships when provided.
- Appropriate statistical language.

Important:
- Distinguish association from causation.
- Do not invent statistical significance.
- Do not invent uncertainty.
- Do not invent mechanisms.
- Do not make claims unsupported by the supplied evidence.

Focus on:
"What does the evidence quantitatively indicate?"
""".strip()

    return """
AUDIENCE: GENERAL

Explain the chart to an ordinary adult reader without specialist
scientific knowledge.

Use:
- Clear and accessible language.
- Enough context to understand the chart.
- The main trend or relationship.
- Important numbers when useful.

Avoid:
- Unnecessary scientific jargon.
- Childish language.
- Advanced statistics unless explained.

Focus on:
"What does this chart show, and why is the pattern important?"
""".strip()


# ---------------------------------------------------------------------------
# Evidence-based fallback
# ---------------------------------------------------------------------------

def _fallback_response(
    context: ChartContext,
    evidence: dict[str, Any],
) -> ExplanationResponse:

    data = evidence.get("data") or {}
    scope = evidence.get("scope") or "the selected scope"
    audience = _get_audience(context)

    # =======================================================================
    # TREND CHART
    # =======================================================================

    if context.chart_id == "trend-chart":

        sea_level = data.get("series", {}).get("sea_level", {})
        temperature = data.get("series", {}).get("temperature", {})
        year_range = data.get("year_range", {})

        sea_level_trend = sea_level.get("trend", "mixed")
        temperature_trend = temperature.get("trend", "mixed")

        start_year = year_range.get("start", "the beginning")
        end_year = year_range.get("end", "the end")

        if audience == "eli5":

            explanation = (
                f"In {scope}, the chart shows that sea level had a "
                f"{sea_level_trend} pattern while temperature had a "
                f"{temperature_trend} pattern between {start_year} "
                f"and {end_year}. In simple terms, the chart shows "
                f"how these two things changed over time."
            )

            takeaway = (
                "The important idea is that the environmental conditions "
                "changed during the years shown."
            )

        elif audience == "scientist":

            explanation = (
                f"For {scope}, the time series from {start_year} to "
                f"{end_year} indicates a {sea_level_trend} sea-level "
                f"trajectory alongside a {temperature_trend} temperature "
                f"trajectory. These represent separate temporal signals "
                f"unless the supplied evidence establishes a statistical "
                f"relationship."
            )

            takeaway = (
                f"The principal temporal signals are a {sea_level_trend} "
                f"sea-level trend and a {temperature_trend} temperature "
                f"trend."
            )

        else:

            explanation = (
                f"In {scope}, sea level shows a {sea_level_trend} pattern "
                f"and temperature shows a {temperature_trend} pattern "
                f"from {start_year} to {end_year}. Overall, the chart "
                f"shows how these environmental indicators changed over "
                f"the selected period."
            )

            takeaway = (
                f"The main takeaway is that {scope} experienced "
                f"changes in the environmental indicators shown."
            )

        return ExplanationResponse(
            explanation=explanation,
            takeaway=takeaway,
        )

    # =======================================================================
    # BUBBLE CHART
    # =======================================================================

    if context.chart_id == "bubble-chart":

        totals = data.get("totals", {})
        correlations = data.get("correlations", {})

        cyclone_count = totals.get("cyclone_count", 0)
        people_affected = totals.get("people_affected", 0)
        economic_loss = totals.get("economic_loss", 0)

        correlation = correlations.get(
            "cyclones_vs_people_affected",
            "not available",
        )

        try:
            formatted_loss = f"${float(economic_loss):,.2f}"
        except (TypeError, ValueError):
            formatted_loss = str(economic_loss)

        if audience == "eli5":

            explanation = (
                f"In {scope}, the chart records {cyclone_count} cyclones. "
                f"These events affected about {people_affected} people "
                f"and the reported economic loss was {formatted_loss}. "
                f"The correlation value is {correlation}, which describes "
                f"how closely cyclone numbers and affected people "
                f"change together."
            )

            takeaway = (
                "The chart shows that cyclones can have large effects "
                "on people and money."
            )

        elif audience == "scientist":

            explanation = (
                f"For {scope}, the aggregated dataset contains "
                f"{cyclone_count} cyclones, {people_affected} people "
                f"affected, and {formatted_loss} in reported economic "
                f"loss. The correlation between cyclone frequency and "
                f"people affected is {correlation}, representing the "
                f"observed association in the supplied data."
            )

            takeaway = (
                f"The key quantitative relationship is the "
                f"{correlation} correlation between cyclone frequency "
                f"and affected population."
            )

        else:

            explanation = (
                f"In {scope}, the chart records {cyclone_count} cyclones, "
                f"{people_affected} people affected, and {formatted_loss} "
                f"in reported economic loss. The correlation between "
                f"cyclone counts and people affected is {correlation}, "
                f"showing how closely these measures are related."
            )

            takeaway = (
                "The chart highlights the human and economic impacts "
                "associated with cyclone activity."
            )

        return ExplanationResponse(
            explanation=explanation,
            takeaway=takeaway,
        )

    # =======================================================================
    # HEATMAP / CYCLONE CHART
    # =======================================================================

    if context.chart_id in {"heatmap", "cyclone-chart"}:

        peak_year = data.get("peak_year", {})
        quiet_year = data.get("quiet_year", {})
        top_countries = data.get("top_countries") or []

        peak_year_value = peak_year.get(
            "year",
            "one year",
        )

        quiet_year_value = quiet_year.get(
            "year",
            "another year",
        )

        if top_countries:

            first_country = top_countries[0]

            if isinstance(first_country, dict):
                top_country = first_country.get(
                    "country",
                    "the leading country",
                )
            else:
                top_country = str(first_country)

        else:
            top_country = "the leading country"

        if audience == "eli5":

            explanation = (
                f"In {scope}, cyclone activity is highest in "
                f"{peak_year_value} and lowest in {quiet_year_value}. "
                f"{top_country} is one of the places with high cyclone "
                f"activity. This means some years and places have "
                f"many more cyclones than others."
            )

            takeaway = (
                "Cyclones do not happen equally often everywhere "
                "or every year."
            )

        elif audience == "scientist":

            explanation = (
                f"The {scope} dataset exhibits a temporal maximum "
                f"in cyclone activity in {peak_year_value} and a "
                f"minimum in {quiet_year_value}. {top_country} appears "
                f"among the highest-activity locations, indicating "
                f"temporal and spatial concentration within the "
                f"supplied dataset."
            )

            takeaway = (
                f"The distribution shows temporal concentration "
                f"around {peak_year_value} and spatial concentration "
                f"among the leading locations."
            )

        else:

            explanation = (
                f"In {scope}, cyclone activity peaks in "
                f"{peak_year_value} and is lowest in "
                f"{quiet_year_value}. {top_country} is among the "
                f"locations with the most activity. Overall, the "
                f"chart shows that cyclone activity varies across "
                f"years and places."
            )

            takeaway = (
                "Cyclone activity is concentrated in particular "
                "places and years."
            )

        return ExplanationResponse(
            explanation=explanation,
            takeaway=takeaway,
        )

    # =======================================================================
    # GENERIC FALLBACK
    # =======================================================================

    if audience == "eli5":

        return ExplanationResponse(
            explanation=(
                "The chart shows a pattern in the selected data. "
                "In simple terms, some values or places change more "
                "than others."
            ),
            takeaway=(
                "The selected data is not uniform."
            ),
        )

    if audience == "scientist":

        return ExplanationResponse(
            explanation=(
                "The chart indicates a measurable pattern in the "
                "supplied dataset. Interpretation should be based "
                "on the observed relationships and trends represented "
                "by the chart."
            ),
            takeaway=(
                "The dataset contains an observable pattern that "
                "can be evaluated quantitatively."
            ),
        )

    return ExplanationResponse(
        explanation=(
            "The chart shows a clear pattern in the selected data "
            "for the chosen region and period."
        ),
        takeaway=(
            "The selected data contains a notable trend or relationship."
        ),
    )


# ---------------------------------------------------------------------------
# Parse model response
# ---------------------------------------------------------------------------

def _parse_explanation_response(
    content: str,
) -> ExplanationResponse:

    clean_text = _extract_json_object(content)

    if not clean_text:
        raise ValueError("empty_generation")

    try:

        payload = json.loads(clean_text)

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"invalid_json_generation: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "generation_is_not_json_object"
        )

    explanation = payload.get("explanation")
    takeaway = payload.get("takeaway")

    if not isinstance(explanation, str):
        raise ValueError(
            "missing_or_invalid_explanation"
        )

    if not isinstance(takeaway, str):
        takeaway = ""

    explanation = explanation.strip()
    takeaway = takeaway.strip()

    if not explanation:
        raise ValueError(
            "empty_explanation"
        )

    return ExplanationResponse(
        explanation=explanation,
        takeaway=takeaway,
    )


# ---------------------------------------------------------------------------
# Main explanation generator
# ---------------------------------------------------------------------------

def generate_explanation(
    context: ChartContext,
    evidence: dict[str, Any],
) -> ExplanationResponse:

    audience = _get_audience(context)

    audience_instructions = _get_audience_instructions(
        audience
    )

    system_prompt = build_system_prompt(
        audience
    )

    chart_prompt = CHART_INSTRUCTIONS.get(
        context.chart_id,
        CHART_INSTRUCTIONS["heatmap"],
    )

    # -----------------------------------------------------------------------
    # Explicitly include audience in the model input.
    # -----------------------------------------------------------------------

    user_payload = {
        "chart_context": context.model_dump(),
        "audience": audience,
        "evidence": evidence,
    }

    user_prompt = json.dumps(
        user_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    # -----------------------------------------------------------------------
    # Debug log
    # -----------------------------------------------------------------------

    print(
        "Groq request started:",
        {
            "model": MODEL_NAME or "<not configured>",
            "scope": evidence.get("scope"),
            "audience": audience,
            "chart_id": context.chart_id,
            "timeout_seconds": REQUEST_TIMEOUT,
        },
        flush=True,
    )

    # -----------------------------------------------------------------------
    # Missing API key
    # -----------------------------------------------------------------------

    if GROQ_CLIENT is None:

        print(
            "Groq client unavailable: GROQ_API_KEY is missing. "
            "Using audience-aware fallback.",
            flush=True,
        )

        return _fallback_response(
            context,
            evidence,
        )

    # -----------------------------------------------------------------------
    # Missing model
    # -----------------------------------------------------------------------

    if not MODEL_NAME:

        print(
            "Groq model unavailable: GROQ_MODEL is not configured. "
            "Using audience-aware fallback.",
            flush=True,
        )

        return _fallback_response(
            context,
            evidence,
        )

    # -----------------------------------------------------------------------
    # Groq request
    #
    # IMPORTANT:
    # There is intentionally NO response_format parameter.
    # The previous response_format caused:
    #
    # 400 json_validate_failed
    #
    # The model is instructed to return JSON and Python parses it.
    # -----------------------------------------------------------------------

    try:

        response = GROQ_CLIENT.chat.completions.create(
            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        f"{audience_instructions}\n\n"
                        f"CHART INSTRUCTIONS:\n"
                        f"{chart_prompt}\n\n"

                        "AUDIENCE REQUIREMENT:\n"
                        f"The selected audience is '{audience}'. "
                        "You MUST tailor the explanation to this "
                        "audience. Do not produce the same explanation "
                        "for different audiences.\n\n"

                        "OUTPUT REQUIREMENT:\n"
                        "Return ONLY one JSON object.\n"
                        '{"explanation":"...","takeaway":"..."}\n'
                        "Both values must be strings.\n"
                        "The explanation must be one paragraph and no more than 300 characters.\n"
                        "The takeaway must be no more than 200 characters.\n"
                        "Do not use Markdown.\n"
                        "Do not use code fences.\n"
                        "Do not add any other fields.\n"),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            reasoning_effort="low",
            temperature=0.2,
            max_tokens=1000,
            timeout=REQUEST_TIMEOUT,
        )

        # DEBUG: inspect the actual Groq response
        # print("FULL GROQ RESPONSE:", response, flush=True)
        # print("CHOICES:", response.choices, flush=True)
        # print("MESSAGE:", response.choices[0].message, flush=True)
        # print(
        #     "CONTENT:",
        #     repr(response.choices[0].message.content),
        #     flush=True,
        # )
        # print(
        #     "FINISH REASON:",
        #     response.choices[0].finish_reason,
        #     flush=True,
        # )

        print(
            "Groq explanation generated successfully:",
            {
                "audience": audience,
                "chart_id": context.chart_id,
            },
            flush=True,
        )



        # -------------------------------------------------------------------
        # Get model output
        # -------------------------------------------------------------------

        content = (
            response.choices[0].message.content
            or ""
        )

        if not content.strip():

            print(
                "Groq returned empty content; "
                "using audience-aware fallback.",
                flush=True,
            )

            return _fallback_response(
                context,
                evidence,
            )

        # -------------------------------------------------------------------
        # Parse model output
        # -------------------------------------------------------------------

        try:

            result = _parse_explanation_response(
                content
            )

            print(
                "Groq explanation generated successfully:",
                {
                    "audience": audience,
                    "chart_id": context.chart_id,
                },
                flush=True,
            )

            return result

        except Exception as exc:

            print(
                f"Groq output could not be parsed: {exc}. "
                "Using audience-aware fallback.",
                flush=True,
            )

            print(
                f"Raw Groq output: {content[:1000]}",
                flush=True,
            )

            return _fallback_response(
                context,
                evidence,
            )

    # -----------------------------------------------------------------------
    # Groq API error
    # -----------------------------------------------------------------------

    except GroqError as exc:

        error_text = str(exc)

        print(
            "Groq exception:",
            error_text,
            flush=True,
        )

        if (
            "model_not_found" in error_text.lower()
            or "does not exist" in error_text.lower()
            or "do not have access" in error_text.lower()
            or "404" in error_text
        ):

            print(
                f"Configured Groq model '{MODEL_NAME}' "
                "is unavailable. Using audience-aware fallback.",
                flush=True,
            )

        else:

            print(
                "Groq API error; using audience-aware fallback.",
                flush=True,
            )

        return _fallback_response(
            context,
            evidence,
        )

    # -----------------------------------------------------------------------
    # Unexpected error
    # -----------------------------------------------------------------------

    except Exception as exc:

        print(
            f"Unexpected error during Groq explanation: {exc}. "
            "Using audience-aware fallback.",
            flush=True,
        )

        return _fallback_response(
            context,
            evidence,
        )
