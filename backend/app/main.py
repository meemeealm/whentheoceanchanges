from __future__ import annotations

import asyncio
import os
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .climate import build_chart_context
from .groq import generate_explanation
from .rate_limit import SimpleRateLimiter
from .schemas import ChartContext, ExplanationResponse


app = FastAPI(title="Climate Storytelling Backend")


def _parse_origins(value: str | None) -> list[str]:
    if value:
        origins = [
            origin.strip()
            for origin in value.split(",")
            if origin.strip()
        ]

        if origins:
            return origins

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
    ]


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

rate_limiter = SimpleRateLimiter(
    limit=int(
        os.getenv(
            "RATE_LIMIT_REQUESTS_PER_WINDOW",
            "30",
        )
    ),
    window_seconds=int(
        os.getenv(
            "RATE_LIMIT_WINDOW_SECONDS",
            "60",
        )
    ),
)


# ---------------------------------------------------------------------------
# Rate-limit middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def enforce_rate_limit(
    request: Request,
    call_next,
):
    if (
        request.method == "OPTIONS"
        or request.url.path == "/health"
    ):
        return await call_next(request)

    if request.url.path == "/api/explain":
        client_host = (
            request.client.host
            if request.client
            else "unknown"
        )

        result = rate_limiter.check(client_host)

        if not result.allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded"
                },
                headers={
                    "Retry-After": str(
                        result.retry_after_seconds
                    )
                },
            )

    return await call_next(request)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Explanation endpoint
# ---------------------------------------------------------------------------

@app.post(
    "/api/explain",
    response_model=ExplanationResponse,
)
async def explain(
    context: ChartContext,
) -> ExplanationResponse:

    request_id = uuid.uuid4().hex[:8]

    print(
        f"[{request_id}] /api/explain START",
        flush=True,
    )

    print(
        f"[{request_id}] Received selection:",
        context.selection.model_dump(),
        flush=True,
    )

    try:

        # ---------------------------------------------------------------
        # Build evidence exactly once
        # ---------------------------------------------------------------

        evidence = await asyncio.to_thread(
            build_chart_context,
            context,
        )

        print(
            f"[{request_id}] build_chart_context() completed:",
            {
                "chart_id": evidence.get("chart_id"),
                "scope": evidence.get("scope"),
            },
            flush=True,
        )

        # ---------------------------------------------------------------
        # Generate explanation exactly once
        # ---------------------------------------------------------------

        result = await asyncio.to_thread(
            generate_explanation,
            context,
            evidence,
        )

        print(
            f"[{request_id}] generate_explanation() completed",
            flush=True,
        )

        print(
            f"[{request_id}] /api/explain END",
            flush=True,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        print(
            f"[{request_id}] Error generating explanation: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Failed to generate explanation from LLM: "
                f"{str(exc)}"
            ),
        ) from exc
