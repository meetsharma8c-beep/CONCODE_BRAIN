"""Tests for the model-output formatter used by the TripVerse itinerary endpoint."""

import json
import unittest

from src.service import TravelContext, _itinerary_from_model_prose, _json_itinerary


class TravelFormatTests(unittest.TestCase):
    def setUp(self):
        self.context = TravelContext(
            destination="Udaipur",
            duration_days=2,
            total_budget=12_000,
            preferences=["history"],
        )

    def test_keeps_valid_model_json(self):
        result = _json_itinerary('{"itinerary":[{"dayNumber":1,"activities":[]}]}')
        self.assertEqual(json.loads(result)["itinerary"][0]["dayNumber"], 1)

    def test_converts_model_prose_without_new_activities(self):
        prose = """Day 1:
* Morning: Explore a historic city area.
* Evening: Enjoy a vegetarian dinner.

Day 2:
* Morning: Visit a lakeside viewpoint.
* Evening: Relax at a local market.
"""
        result = _itinerary_from_model_prose(prose, self.context)
        itinerary = json.loads(result)["itinerary"]
        self.assertEqual(len(itinerary), 2)
        self.assertEqual(itinerary[0]["activities"][0]["title"], "Explore a historic city area")
        self.assertEqual(itinerary[0]["activities"][1]["type"], "food")

    def test_rejects_incomplete_model_prose(self):
        self.assertIsNone(_itinerary_from_model_prose("Day 1:\n* One activity", self.context))


if __name__ == "__main__":
    unittest.main()
