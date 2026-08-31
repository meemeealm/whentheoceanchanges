from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, FieldValidationInfo, field_validator, model_validator
from pydantic.alias_generators import to_camel

class BaseSchema(BaseModel):
    """Base model allowing camelCase inputs from js/ and ignoring unexpected frontend fields."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",  # Prevents frontend metadata from throwing 422 errors
        str_strip_whitespace=True,
    )


ChartId = Literal["trend-chart", "bubble-chart", "heatmap", "cyclone-chart"]


class TrendSelection(BaseSchema):
    region: str = Field(min_length=1)
    start_year: int | None = None
    end_year: int | None = None


class BubbleSelection(BaseSchema):
    period: str = Field(min_length=1)
    region: str | None = Field(default=None, min_length=1)


class HeatmapSelection(BaseSchema):
    region: str | None = Field(default=None, min_length=1)
    start_year: int | None = None
    end_year: int | None = None


Selection = Union[TrendSelection, BubbleSelection, HeatmapSelection]


class ChartContext(BaseSchema):
    chart_id: ChartId
    audience: str = Field(
        default="general",
        description="Target audience style: 'eli5', 'scientist', or 'general'",
    )
    selection: Selection

    @field_validator("audience", mode="before")
    @classmethod
    def validate_audience(cls, value):
        if value is None or value == "":
            return "general"

        if not isinstance(value, str):
            raise ValueError("audience must be a string")

        normalized = value.strip().lower()

        if normalized not in {"eli5", "general", "scientist"}:
            raise ValueError("audience must be one of: eli5, general, scientist")

        return normalized

    @model_validator(mode="before")
    @classmethod
    def coerce_selection(cls, data):
        if not isinstance(data, dict):
            return data

        # Handle both camelCase and snake_case keys from frontend payload
        chart_id = data.get("chart_id") or data.get("chartId")
        selection = data.get("selection")

        if chart_id == "trend-chart":
            model = TrendSelection
        elif chart_id == "bubble-chart":
            model = BubbleSelection
        elif chart_id in {"heatmap", "cyclone-chart"}:
            model = HeatmapSelection
        else:
            return data

        if not isinstance(selection, model):
            data = dict(data)
            data["selection"] = model.model_validate(selection)

        return data

    @model_validator(mode="after")
    def validate_selection_match(self):
        if self.chart_id == "trend-chart" and not isinstance(self.selection, TrendSelection):
            raise ValueError("trend-chart requires trend selection fields")
        if self.chart_id == "bubble-chart" and not isinstance(self.selection, BubbleSelection):
            raise ValueError("bubble-chart requires bubble selection fields")
        if self.chart_id in {"heatmap", "cyclone-chart"} and not isinstance(self.selection, HeatmapSelection):
            raise ValueError("heatmap requires heatmap selection fields")

        if isinstance(self.selection, (TrendSelection, HeatmapSelection)):
            if self.selection.start_year is not None and self.selection.end_year is not None:
                if self.selection.end_year < self.selection.start_year:
                    raise ValueError("end_year must be greater than or equal to start_year")

        return self


class ExplanationResponse(BaseSchema):
    explanation: str = Field(
        ...,
        description="Single paragraph explanation of the chart findings."
    )
    takeaway: str = Field(
        default="",
        description="Short key takeaway from the chart findings."
    )

    @field_validator("explanation", "takeaway", mode="before")
    @classmethod
    def truncate_llm_text(
        cls,
        value: str,
        info: FieldValidationInfo,
    ) -> str:
        """Safely truncates AI outputs instead of throwing backend 500 errors."""
        max_length = 300 if info.field_name == "explanation" else 200

        if isinstance(value, str) and len(value) > max_length:
            return value[: max_length - 3] + "..."
        return value
