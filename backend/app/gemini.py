from __future__ import annotations

import os
from functools import lru_cache

from fastapi import HTTPException
from google import genai
from google.genai import types
from pydantic import ValidationError

from .prompts import build_prompt_bundle
from .schemas import ChartContext, ExplanationResponse


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")
    return genai.Client(api_key=api_key)


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def generate_explanation(context: ChartContext, evidence: dict) -> ExplanationResponse:
    prompt = build_prompt_bundle(context, evidence)
    client = get_client()

    schema_dict = ExplanationResponse.model_json_schema()
    schema_dict.pop("additionalProperties", None)

    try:
        # Create a chat session to handle Automatic Function Calling (AFC) cleanly
        chat = client.chats.create(
            model=get_model_name(),
            config=types.GenerateContentConfig(
                system_instruction=prompt.system_instruction,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=schema_dict,
                max_output_tokens=2048,
            ),
        )

        # Send message through the chat session instead of models.generate_content
        response = chat.send_message(prompt.user_prompt)

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - surface SDK failures as HTTP
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    text = getattr(response, "text", None)
    if not text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")

    try:
        return ExplanationResponse.model_validate_json(text)
    except ValidationError as exc:
        print("GEMINI RAW RESPONSE:")
        print(text)

        print("VALIDATION ERROR:")
        print(exc)

        raise HTTPException(
            status_code=502,
            detail="Gemini returned invalid structured output"
        ) from exc