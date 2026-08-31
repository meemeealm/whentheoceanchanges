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
    return re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content.strip(),
        flags=re.IGNORECASE,
    ).strip()


def _get_audience(context: ChartContext) -> str:
    """
    ChartContext already validates audience to one of:
        eli5
        general
        scientist
    """

    audience = getattr(context, "audience", "general")

    if not audience:
        return "general"

    return str(audience).strip().lower()


def _get_audience_instructions(audience: str) -> str:
    """
    Explicit instructions for each audience.

    These instructions are deliberately very different so the generated
    explanations do not become identical.
    """

    if audience == "eli5":
        return """
AUDIENCE: ELI5

Explain the chart as if you are explaining it to a curious child or
complete beginner.

Requirements:
- Use very simple everyday language.
- Avoid scientific jargon.
- If a technical term is necessary, explain it immediately.
- Focus on WHAT the chart shows.
- Explain numbers and trends in an intuitive way.
- Use short, easy-to-understand sentences.
- Do not assume prior knowledge.
- Do not discuss methodology unless absolutely necessary.
- Make the takeaway easy for a beginner to remember.

The explanation should answer:
"What is happening in this chart, in simple words?"
""".strip()

    if audience == "scientist":
        return """
AUDIENCE: SCIENTIST

Explain the chart for a scientifically literate audience.

Requirements:
- Use precise analytical terminology where appropriate.
- Focus on quantitative patterns, trends, relationships, and comparisons.
- Mention relevant magnitudes, correlations, temporal patterns, or
  spatial patterns when those are present in the evidence.
- Distinguish observed association from causation.
- Do not oversimplify the findings.
- Do not invent statistical significance, uncertainty, mechanisms,
  or causal explanations that are not contained in the evidence.
- Focus on what can actually be supported by the supplied data.

The explanation should answer:
"What does the evidence quantitatively indicate?"
""".strip()

    # general
    return """
AUDIENCE: GENERAL

Explain the chart for an ordinary adult reader who does not need
specialist technical knowledge.

Requirements:
- Use clear, accessible language.
- Give enough context to understand the chart.
- Explain the main trend or relationship.
- Include important numbers when useful.
- Avoid unnecessary scientific jargon.
- Do not make the explanation childish.
- Do not assume advanced statistical knowledge.
- Keep the explanation practical and understandable.

The explanation should answer:
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

        # -------------------------------------------------------------------
        # ELI5
        # -------------------------------------------------------------------

        if audience == "eli5":

            explanation = (
                f"In {scope}, the chart shows that sea level had a "
                f"{sea_level_trend} pattern while temperature had a "
                f"{temperature_trend} pattern between {start_year} and "
                f"{end_year}. In simple terms, the chart shows how these "
                f"two things changed over time."
            )

            takeaway = (
                "The important idea is that the environment changed over "
                "the years shown in the chart."
            )

        # -------------------------------------------------------------------
        # SCIENTIST
        # -------------------------------------------------------------------

        elif audience == "scientist":

            explanation = (
                f"For {scope}, the time series from {start_year} to "
                f"{end_year} indicates a {sea_level_trend} sea-level "
                f"trajectory alongside a {temperature_trend} temperature "
                f"trajectory. The two indicators should be interpreted as "
                f"separate temporal signals unless the supplied evidence "
                f"establishes a statistical relationship between them."
            )

            takeaway = (
                f"The principal temporal signals are a {sea_level_trend} "
                f"sea-level trend and a {temperature_trend} temperature "
                f"trend over the observation period."
            )

        # -------------------------------------------------------------------
        # GENERAL
        # -------------------------------------------------------------------

        else:

            explanation = (
                f"In {scope}, sea level shows a {sea_level_trend} pattern "
                f"and temperature shows a {temperature_trend} pattern "
                f"from {start_year} to {end_year}. Overall, the chart "
                f"shows how these environmental indicators changed over "
                f"the selected period."
            )

            takeaway = (
                f"The main takeaway is that {scope} experienced noticeable "
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

        # -------------------------------------------------------------------
        # ELI5
        # -------------------------------------------------------------------

        if audience == "eli5":

            explanation = (
                f"In {scope}, the chart records {cyclone_count} cyclones. "
                f"These events affected about {people_affected} people "
                f"and the reported economic loss was {formatted_loss}. "
                f"The correlation value is {correlation}, which describes "
                f"how closely cyclone numbers and the number of affected "
                f"people move together."
            )

            takeaway = (
                "The chart shows that cyclones can have large effects on "
                "both people and money."
            )

        # -------------------------------------------------------------------
        # SCIENTIST
        # -------------------------------------------------------------------

        elif audience == "scientist":

            explanation = (
                f"For {scope}, the aggregated dataset contains "
                f"{cyclone_count} cyclones, {people_affected} people "
                f"affected, and {formatted_loss} in reported economic "
                f"loss. The correlation between cyclone frequency and "
                f"people affected is {correlation}, providing a quantitative "
                f"measure of their association in the supplied data."
            )

            takeaway = (
                f"The key quantitative relationship is the "
                f"{correlation} correlation between cyclone frequency "
                f"and affected population."
            )

        # -------------------------------------------------------------------
        # GENERAL
        # -------------------------------------------------------------------

        else:

            explanation = (
                f"In {scope}, the chart records {cyclone_count} cyclones, "
                f"{people_affected} people affected, and {formatted_loss} "
                f"in reported economic loss. The correlation between "
                f"cyclone counts and people affected is {correlation}, "
                f"showing how closely these two measures are related "
                f"in the selected data."
            )

            takeaway = (
                "The chart highlights the human and economic impact "
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

        peak_year_value = peak_year.get("year", "one year")
        quiet_year_value = quiet_year.get("year", "another year")

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

        # -------------------------------------------------------------------
        # ELI5
        # -------------------------------------------------------------------

        if audience == "eli5":

            explanation = (
                f"In {scope}, cyclone activity is highest in "
                f"{peak_year_value} and lowest in {quiet_year_value}. "
                f"{top_country} is one of the places with high cyclone "
                f"activity. This means that some years and places have "
                f"many more cyclones than others."
            )

            takeaway = (
                "Cyclones do not happen equally often everywhere or "
                "every year."
            )

        # -------------------------------------------------------------------
        # SCIENTIST
        # -------------------------------------------------------------------

        elif audience == "scientist":

            explanation = (
                f"The {scope} dataset exhibits a temporal maximum in "
                f"cyclone activity in {peak_year_value} and a minimum in "
                f"{quiet_year_value}. {top_country} appears among the "
                f"highest-activity locations, indicating both temporal "
                f"and spatial concentration within the supplied dataset."
            )

            takeaway = (
                f"The distribution shows temporal concentration around "
                f"{peak_year_value} and spatial concentration among "
                f"the leading locations."
            )

        # -------------------------------------------------------------------
        # GENERAL
        # -------------------------------------------------------------------

        else:

            explanation = (
                f"In {scope}, cyclone activity peaks in {peak_year_value} "
                f"and is lowest in {quiet_year_value}. {top_country} is "
                f"among the locations with the most activity. Overall, "
                f"the chart shows that cyclone activity varies across "
                f"both years and places."
            )

            takeaway = (
                "Cyclone activity is concentrated in particular places "
                "and years."
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
            takeaway="The chart shows that the selected data is not uniform.",
        )

    if audience == "scientist":
        return ExplanationResponse(
            explanation=(
                "The chart indicates a measurable pattern in the supplied "
                "dataset. Interpretation should be based on the observed "
                "relationships and trends represented by the chart."
            ),
            takeaway=(
                "The dataset contains a measurable pattern that warrants "
                "quantitative interpretation."
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

    if not explanation.strip():
        raise ValueError("missing_explanation")

    return ExplanationResponse(
        explanation=explanation.strip(),
        takeaway=takeaway.strip(),
    )


# ---------------------------------------------------------------------------
# Main explanation generator
# ---------------------------------------------------------------------------

def generate_explanation(
    context: ChartContext,
    evidence: dict[str, Any],
) -> ExplanationResponse:

    audience = _get_audience(context)
    audience_instructions = _get_audience_instructions(audience)

    system_prompt = build_system_prompt(audience)

    chart_prompt = CHART_INSTRUCTIONS.get(
        context.chart_id,
        CHART_INSTRUCTIONS["heatmap"],
    )

    # -----------------------------------------------------------------------
    # Explicitly put audience into the model input.
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
    # Log exactly what audience reached this function.
    #
    # This is VERY important for debugging the selector.
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
    # No Groq client
    # -----------------------------------------------------------------------

    if GROQ_CLIENT is None:

        print(
            "Groq client unavailable: GROQ_API_KEY is missing. "
            "Using audience-aware fallback.",
            flush=True,
        )

        return _fallback_response(context, evidence)

    # -----------------------------------------------------------------------
    # No model
    # -----------------------------------------------------------------------

    if not MODEL_NAME:

        print(
            "Groq model unavailable: GROQ_MODEL is not configured. "
            "Using audience-aware fallback.",
            flush=True,
        )

        return _fallback_response(context, evidence)

    # -----------------------------------------------------------------------
    # Groq request
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
                        f"CHART INSTRUCTIONS:\n{chart_prompt}\n\n"
                        "The audience selection is mandatory. "
                        "Generate a substantially audience-specific "
                        "explanation rather than reusing generic wording."
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=350,
            timeout=REQUEST_TIMEOUT,
        )

        content = response.choices[0].message.content or ""

        # -------------------------------------------------------------------
        # Empty response
        # -------------------------------------------------------------------

        if not content.strip():

            print(
                "Groq returned empty content; "
                "using audience-aware fallback.",
                flush=True,
            )

            return _fallback_response(context, evidence)

        # -------------------------------------------------------------------
        # Parse response
        # -------------------------------------------------------------------

        try:

            result = _parse_explanation_response(content)

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

            return _fallback_response(context, evidence)

    # -----------------------------------------------------------------------
    # Groq error
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
                f"Configured Groq model '{MODEL_NAME}' is unavailable. "
                "Using audience-aware fallback.",
                flush=True,
            )

        else:

            print(
                "Groq API error; using audience-aware fallback.",
                flush=True,
            )

        return _fallback_response(context, evidence)

    # -----------------------------------------------------------------------
    # Unexpected error
    # -----------------------------------------------------------------------

    except Exception as exc:

        print(
            f"Unexpected error during Groq explanation: {exc}. "
            "Using audience-aware fallback.",
            flush=True,
        )

        return _fallback_response(context, evidence)
