from __future__ import annotations

import asyncio
import os

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
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if origins:
            return origins
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(os.getenv("CORS_ORIGINS")),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

rate_limiter = SimpleRateLimiter(
    limit=int(os.getenv("RATE_LIMIT_REQUESTS_PER_WINDOW", "30")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path == "/health":
        return await call_next(request)

    if request.url.path == "/api/explain":
        client_host = request.client.host if request.client else "unknown"
        result = rate_limiter.check(client_host)
        if not result.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(result.retry_after_seconds)},
            )

    return await call_next(request)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/explain", response_model=ExplanationResponse)
async def explain(context: ChartContext) -> ExplanationResponse:
    print(
        "Received selection:",
        context.selection.model_dump(),
        flush=True,
    )

    try:
        evidence = await asyncio.to_thread(build_chart_context, context)

        print(
            "build_chart_context() completed:",
            {
                "chart_id": evidence.get("chart_id"),
                "scope": evidence.get("scope"),
            },
            flush=True,
        )

        return await asyncio.to_thread(generate_explanation, context, evidence)

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error generating explanation: {exc}", flush=True)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate explanation from LLM: {str(exc)}",
        ) from exc