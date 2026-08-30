from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.climate import build_bubble_context, build_cyclone_context, build_trend_context
from backend.app.main import app
from backend.app.schemas import ChartContext, ExplanationResponse


class ChartContextTests(unittest.TestCase):
    def test_valid_trend_context(self) -> None:
        context = ChartContext.model_validate(
            {
                "chart_id": "trend-chart",
                "audience": "general",
                "selection": {
                    "region": "Pacific Overall",
                    "start_year": None,
                    "end_year": None,
                },
            }
        )

        self.assertEqual(context.chart_id, "trend-chart")
        self.assertEqual(context.audience, "general")
        self.assertEqual(context.selection.region, "Pacific Overall")

    def test_invalid_chart_id_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ChartContext.model_validate(
                {
                    "chart_id": "unknown-chart",
                    "audience": "general",
                    "selection": {},
                }
            )

    def test_invalid_audience_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ChartContext.model_validate(
                {
                    "chart_id": "trend-chart",
                    "audience": "curious",
                    "selection": {
                        "region": "Pacific Overall",
                        "start_year": None,
                        "end_year": None,
                    },
                }
            )

    def test_selection_range_is_validated(self) -> None:
        with self.assertRaises(ValidationError):
            ChartContext.model_validate(
                {
                    "chart_id": "trend-chart",
                    "audience": "general",
                    "selection": {
                        "region": "Pacific Overall",
                        "start_year": 2020,
                        "end_year": 2010,
                    },
                }
            )


class ClimateProcessingTests(unittest.TestCase):
    def test_trend_context_is_deterministic(self) -> None:
        context = ChartContext.model_validate(
            {
                "chart_id": "trend-chart",
                "audience": "general",
                "selection": {
                    "region": "Pacific Overall",
                    "start_year": None,
                    "end_year": None,
                },
            }
        )

        evidence = build_trend_context(context)

        self.assertEqual(evidence["chart_id"], "trend-chart")
        self.assertEqual(evidence["scope"], "Pacific Overall")
        self.assertEqual(evidence["data"]["year_range"], {"start": 1994, "end": 2023})
        self.assertEqual(evidence["data"]["points"], 30)
        self.assertIn(evidence["data"]["series"]["sea_level"]["trend"], {"increasing", "decreasing", "flat"})

    def test_bubble_context_aggregates_expected_totals(self) -> None:
        context = ChartContext.model_validate(
            {
                "chart_id": "bubble-chart",
                "audience": "general",
                "selection": {
                    "period": "2010s",
                    "region": None,
                },
            }
        )

        evidence = build_bubble_context(context)

        self.assertEqual(evidence["scope"], "all countries")
        self.assertEqual(evidence["data"]["country_count"], 21)
        self.assertEqual(evidence["data"]["totals"]["cyclone_count"], 355)
        self.assertEqual(evidence["data"]["totals"]["people_affected"], 2588223)
        self.assertAlmostEqual(evidence["data"]["totals"]["economic_loss"], 309257040.87, places=2)

    def test_cyclone_context_aggregates_expected_totals(self) -> None:
        context = ChartContext.model_validate(
            {
                "chart_id": "cyclone-chart",
                "audience": "general",
                "selection": {
                    "region": None,
                    "start_year": None,
                    "end_year": None,
                },
            }
        )

        evidence = build_cyclone_context(context)

        self.assertEqual(evidence["scope"], "all countries")
        self.assertEqual(evidence["data"]["year_range"], {"start": 2006, "end": 2025})
        self.assertEqual(evidence["data"]["total_cyclones"], 218)
        self.assertGreater(len(evidence["data"]["top_countries"]), 0)


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_explain_endpoint_returns_structured_json(self) -> None:
        payload = {
            "chart_id": "trend-chart",
            "audience": "general",
            "selection": {
                "region": "Pacific Overall",
                "start_year": None,
                "end_year": None,
            },
        }

        fake_evidence = {"chart_id": "trend-chart", "data": {"example": True}}
        fake_response = ExplanationResponse(
            explanation="The selected period shows a steady rise.",
            takeaway="The pattern matters because it points to a persistent change.",
        )

        with patch("backend.app.main.build_chart_context", return_value=fake_evidence) as build_mock, patch(
            "backend.app.main.generate_explanation",
            return_value=fake_response,
        ) as gemini_mock:
            response = self.client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "explanation": "The selected period shows a steady rise.",
                "takeaway": "The pattern matters because it points to a persistent change.",
            },
        )
        build_mock.assert_called_once()
        gemini_mock.assert_called_once_with(
            ChartContext.model_validate(payload),
            fake_evidence,
        )

    def test_explain_endpoint_rejects_invalid_chart_id(self) -> None:
        payload = {
            "chart_id": "bad-chart",
            "audience": "general",
            "selection": {},
        }

        with patch("backend.app.main.generate_explanation") as gemini_mock:
            response = self.client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(gemini_mock.call_count, 0)


if __name__ == "__main__":
    unittest.main()
