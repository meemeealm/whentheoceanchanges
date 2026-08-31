from __future__ import annotations

import json
import re
import os
from typing import Any

from groq import Groq, GroqError

from .prompts import build_prompt_bundle
from .schemas import ChartContext, ExplanationResponse

GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))


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
            temperature=0.4,
            max_tokens=600,
            timeout=15,
            # DO NOT pass response_format={"type": "json_object"} here
        )

        content = response.choices[0].message.content or ""

        # Clean out any accidental markdown fences/quotes
        clean_text = re.sub(r"^```\w*\n?|\n?```$", "", content.strip()).strip()

        if not clean_text:
            raise RuntimeError("Model returned empty generation.")

        return ExplanationResponse(explanation=clean_text[:500])

    except GroqError as exc:
        print("Groq exception:", exc, flush=True)
        raise RuntimeError(f"Groq API call failed: {exc}") from exc