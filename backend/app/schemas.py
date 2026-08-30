from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

ChartId = Literal["trend-chart", "bubble-chart", "cyclone-chart"]
Audience = Literal["eli5", "general", "scientist"]


class TrendSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    region: str = Field(min_length=1)
    start_year: int | None = None
    end_year: int | None = None


class BubbleSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    period: str = Field(min_length=1)
    region: str | None = Field(default=None, min_length=1)


class CycloneSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    region: str | None = Field(default=None, min_length=1)
    start_year: int | None = None
    end_year: int | None = None


Selection = Union[TrendSelection, BubbleSelection, CycloneSelection]


class ChartContext(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chart_id: ChartId
    audience: Audience
    selection: Selection

    @model_validator(mode="before")
    @classmethod
    def coerce_selection(cls, data):
        if not isinstance(data, dict):
            return data

        chart_id = data.get("chart_id")
        selection = data.get("selection")

        if chart_id == "trend-chart":
            model = TrendSelection
        elif chart_id == "bubble-chart":
            model = BubbleSelection
        elif chart_id == "cyclone-chart":
            model = CycloneSelection
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
        if self.chart_id == "cyclone-chart" and not isinstance(self.selection, CycloneSelection):
            raise ValueError("cyclone-chart requires cyclone selection fields")

        if isinstance(self.selection, TrendSelection):
            if self.selection.start_year is not None and self.selection.end_year is not None:
                if self.selection.end_year < self.selection.start_year:
                    raise ValueError("end_year must be greater than or equal to start_year")

        if isinstance(self.selection, CycloneSelection):
            if self.selection.start_year is not None and self.selection.end_year is not None:
                if self.selection.end_year < self.selection.start_year:
                    raise ValueError("end_year must be greater than or equal to start_year")

        return self


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: str
    takeaway: str
