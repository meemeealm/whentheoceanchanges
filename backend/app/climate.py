from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any

from fastapi import HTTPException

from .schemas import BubbleSelection, ChartContext, CycloneSelection, TrendSelection

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

TREND_FILES = ["sea_temperature.json", "01_environmental_trends.json"]
BUBBLE_FILES = ["economic_loss.json", "bubble_data.json"]
CYCLONE_FILES = ["impacts.json", "03_cyclones_data.json"]


def _load_first_available(file_names: list[str]) -> list[dict[str, Any]]:
    for name in file_names:
        path = DATA_DIR / name
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
    raise FileNotFoundError(f"Could not find any of: {', '.join(file_names)}")


@lru_cache(maxsize=1)
def load_trend_data() -> list[dict[str, Any]]:
    rows = _load_first_available(TREND_FILES)
    normalized = []
    for row in rows:
        try:
            normalized.append(
                {
                    "country": str(row["country"]).strip(),
                    "year": int(row["year"]),
                    "sea_level": float(row.get("sea_lvl_value", row.get("sea_level"))),
                    "temperature": float(row.get("sea_temperature", row.get("temperature"))),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return [row for row in normalized if row["country"]]


@lru_cache(maxsize=1)
def load_bubble_data() -> list[dict[str, Any]]:
    rows = _load_first_available(BUBBLE_FILES)
    normalized = []
    for row in rows:
        try:
            normalized.append(
                {
                    "country": str(row["country"]).strip(),
                    "cyclone_count": int(row["cyclone_count"]),
                    "people_affected": int(row["people_affected"]),
                    "economic_loss": float(row["economic_loss"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return [row for row in normalized if row["country"]]


@lru_cache(maxsize=1)
def load_cyclone_data() -> list[dict[str, Any]]:
    rows = _load_first_available(CYCLONE_FILES)
    normalized = []
    for row in rows:
        try:
            normalized.append(
                {
                    "country": str(row["country"]).strip(),
                    "year": int(row["year"]),
                    "cyclone_count": int(row["cyclone_count"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return [row for row in normalized if row["country"]]


def _safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def _safe_percent_change(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    if math.isclose(start, 0.0, abs_tol=1e-12):
        return None
    return ((end - start) / abs(start)) * 100.0


def _trend_direction(values: list[float], years: list[int]) -> str:
    if len(values) < 2:
        return "flat"
    x_mean = _safe_mean([float(year) for year in years])
    y_mean = _safe_mean(values)
    if x_mean is None or y_mean is None:
        return "flat"
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(years, values))
    denominator = sum((x - x_mean) ** 2 for x in years)
    if math.isclose(denominator, 0.0, abs_tol=1e-12):
        return "flat"
    slope = numerator / denominator
    if slope > 0.001:
        return "increasing"
    if slope < -0.001:
        return "decreasing"
    return "flat"


def _pearson_correlation(x_values: list[float], y_values: list[float]) -> float | None:
    if len(x_values) < 2 or len(x_values) != len(y_values):
        return None
    x_mean = _safe_mean(x_values)
    y_mean = _safe_mean(y_values)
    if x_mean is None or y_mean is None:
        return None
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_den = sum((x - x_mean) ** 2 for x in x_values)
    y_den = sum((y - y_mean) ** 2 for y in y_values)
    if math.isclose(x_den, 0.0, abs_tol=1e-12) or math.isclose(y_den, 0.0, abs_tol=1e-12):
        return None
    return numerator / math.sqrt(x_den * y_den)


def _group_trend_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_year: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_year.setdefault(row["year"], []).append(row)

    grouped = []
    for year in sorted(by_year):
        year_rows = by_year[year]
        grouped.append(
            {
                "year": year,
                "sea_level": _safe_mean([float(row["sea_level"]) for row in year_rows]),
                "temperature": _safe_mean([float(row["temperature"]) for row in year_rows]),
            }
        )
    return [row for row in grouped if row["sea_level"] is not None and row["temperature"] is not None]


def build_chart_context(context: ChartContext) -> dict[str, Any]:
    if context.chart_id == "trend-chart":
        evidence = build_trend_context(context)
    elif context.chart_id == "bubble-chart":
        evidence = build_bubble_context(context)
    elif context.chart_id == "cyclone-chart":
        evidence = build_cyclone_context(context)
    else:
        raise HTTPException(status_code=400, detail="Unsupported chart_id")

    print(
        "build_chart_context() completed:",
        {
            "chart_id": evidence.get("chart_id"),
            "scope": evidence.get("scope"),
        },
        flush=True,
    )

    return evidence


def build_trend_context(context: ChartContext) -> dict[str, Any]:
    assert isinstance(context.selection, TrendSelection)
    rows = load_trend_data()

    if context.selection.region == "Pacific Overall":
        selected_rows = rows
        scope = "Pacific Overall"
    else:
        selected_rows = [row for row in rows if row["country"] == context.selection.region]
        scope = context.selection.region

    print("evidence scope:", scope, flush=True)
    print("selected country/region used for evidence:", scope, flush=True)

    if context.selection.start_year is not None:
        selected_rows = [row for row in selected_rows if row["year"] >= context.selection.start_year]
    if context.selection.end_year is not None:
        selected_rows = [row for row in selected_rows if row["year"] <= context.selection.end_year]

    if not selected_rows:
        raise HTTPException(status_code=404, detail="No trend data found for the requested selection")

    grouped = _group_trend_rows(selected_rows)
    if not grouped:
        raise HTTPException(status_code=404, detail="No trend data available after aggregation")

    years = [row["year"] for row in grouped]
    sea_levels = [row["sea_level"] for row in grouped]
    temperatures = [row["temperature"] for row in grouped]

    first = grouped[0]
    last = grouped[-1]

    return {
        "chart_id": context.chart_id,
        "audience": context.audience,
        "selection": context.selection.model_dump(),
        "scope": scope,
        "data": {
            "year_range": {"start": years[0], "end": years[-1]},
            "points": len(grouped),
            "series": {
                "sea_level": {
                    "min": min(sea_levels),
                    "max": max(sea_levels),
                    "mean": _safe_mean(sea_levels),
                    "start": first["sea_level"],
                    "end": last["sea_level"],
                    "change": last["sea_level"] - first["sea_level"],
                    "percent_change": _safe_percent_change(first["sea_level"], last["sea_level"]),
                    "trend": _trend_direction(sea_levels, years),
                },
                "temperature": {
                    "min": min(temperatures),
                    "max": max(temperatures),
                    "mean": _safe_mean(temperatures),
                    "start": first["temperature"],
                    "end": last["temperature"],
                    "change": last["temperature"] - first["temperature"],
                    "percent_change": _safe_percent_change(first["temperature"], last["temperature"]),
                    "trend": _trend_direction(temperatures, years),
                },
            },
            "notable_years": [
                {
                    "year": row["year"],
                    "sea_level": row["sea_level"],
                    "temperature": row["temperature"],
                }
                for row in sorted(
                    [min(grouped, key=lambda row: row["sea_level"]), max(grouped, key=lambda row: row["sea_level"]), min(grouped, key=lambda row: row["temperature"]), max(grouped, key=lambda row: row["temperature"])],
                    key=lambda row: row["year"],
                )
            ],
        },
    }


def build_bubble_context(context: ChartContext) -> dict[str, Any]:
    assert isinstance(context.selection, BubbleSelection)
    rows = load_bubble_data()

    if context.selection.period != "2010s":
        raise HTTPException(status_code=404, detail="Only the 2010s bubble summary is available")

    if context.selection.region:
        selected_rows = [row for row in rows if row["country"] == context.selection.region]
        scope = context.selection.region
    else:
        selected_rows = rows
        scope = "all countries"

    print("evidence scope:", scope, flush=True)
    print("selected country/region used for evidence:", scope, flush=True)

    if not selected_rows:
        raise HTTPException(status_code=404, detail="No bubble data found for the requested selection")

    cyclone_counts = [float(row["cyclone_count"]) for row in selected_rows]
    people_affected = [float(row["people_affected"]) for row in selected_rows]
    losses = [float(row["economic_loss"]) for row in selected_rows]

    highest_loss = max(selected_rows, key=lambda row: row["economic_loss"])
    highest_people = max(selected_rows, key=lambda row: row["people_affected"])

    return {
        "chart_id": context.chart_id,
        "audience": context.audience,
        "selection": context.selection.model_dump(),
        "scope": scope,
        "data": {
            "period": context.selection.period,
            "country_count": len(selected_rows),
            "totals": {
                "cyclone_count": int(sum(cyclone_counts)),
                "people_affected": int(sum(people_affected)),
                "economic_loss": float(sum(losses)),
            },
            "means": {
                "cyclone_count": _safe_mean(cyclone_counts),
                "people_affected": _safe_mean(people_affected),
                "economic_loss": _safe_mean(losses),
            },
            "extremes": {
                "highest_economic_loss": highest_loss,
                "highest_people_affected": highest_people,
                "lowest_economic_loss": min(selected_rows, key=lambda row: row["economic_loss"]),
                "lowest_people_affected": min(selected_rows, key=lambda row: row["people_affected"]),
            },
            "correlations": {
                "cyclones_vs_people_affected": _pearson_correlation(cyclone_counts, people_affected),
                "cyclones_vs_economic_loss": _pearson_correlation(cyclone_counts, losses),
            },
            "countries": selected_rows,
        },
    }


def build_cyclone_context(context: ChartContext) -> dict[str, Any]:
    assert isinstance(context.selection, CycloneSelection)
    rows = load_cyclone_data()

    if context.selection.region:
        selected_rows = [row for row in rows if row["country"] == context.selection.region]
        scope = context.selection.region
    else:
        selected_rows = rows
        scope = "all countries"

    print("evidence scope:", scope, flush=True)
    print("selected country/region used for evidence:", scope, flush=True)

    if context.selection.start_year is not None:
        selected_rows = [row for row in selected_rows if row["year"] >= context.selection.start_year]
    if context.selection.end_year is not None:
        selected_rows = [row for row in selected_rows if row["year"] <= context.selection.end_year]

    if not selected_rows:
        raise HTTPException(status_code=404, detail="No cyclone data found for the requested selection")

    by_year: dict[int, int] = {}
    by_country: dict[str, int] = {}
    for row in selected_rows:
        by_year[row["year"]] = by_year.get(row["year"], 0) + row["cyclone_count"]
        by_country[row["country"]] = by_country.get(row["country"], 0) + row["cyclone_count"]

    year_series = sorted(by_year.items())
    counts = [count for _, count in year_series]
    years = [year for year, _ in year_series]

    peak_year = max(year_series, key=lambda item: item[1]) if year_series else None
    quiet_year = min(year_series, key=lambda item: item[1]) if year_series else None

    return {
        "chart_id": context.chart_id,
        "audience": context.audience,
        "selection": context.selection.model_dump(),
        "scope": scope,
        "data": {
            "year_range": {"start": years[0], "end": years[-1]},
            "total_cyclones": int(sum(counts)),
            "mean_per_year": _safe_mean([float(count) for count in counts]),
            "peak_year": {"year": peak_year[0], "cyclones": peak_year[1]} if peak_year else None,
            "quiet_year": {"year": quiet_year[0], "cyclones": quiet_year[1]} if quiet_year else None,
            "top_countries": [
                {"country": country, "cyclones": total}
                for country, total in sorted(by_country.items(), key=lambda item: item[1], reverse=True)[:5]
            ],
            "yearly_totals": [
                {"year": year, "cyclones": count}
                for year, count in year_series
            ],
        },
    }
