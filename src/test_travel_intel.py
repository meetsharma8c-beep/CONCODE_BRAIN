"""Tests for the TripVerse itinerary critic and exact budget allocation."""

import json
import unittest

from src.brain.travel_intel import (
    exact_budget_breakdown,
    normalize_camel_case_context,
    recover_truncated_itinerary_json,
    verify_itinerary,
)


class TravelIntelTests(unittest.TestCase):
    def test_breakdown_sums_exactly_to_total(self):
        for total in (12_345, 99_999, 7):
            b = exact_budget_breakdown(total, "Udaipur")
            parts = b["transport"] + b["stays"] + b["food"] + b["activities"] + b["buffer"]
            self.assertEqual(parts, total)

    def test_trims_days_renumbers_and_caps_budget(self):
        raw = json.dumps({"itinerary": [
            {"dayNumber": 3, "activities": [{"estimatedCost": "5,000"}, {"estimatedCost": -10}]},
            {"dayNumber": 1, "activities": [{"estimatedCost": 6000}]},
            {"dayNumber": 9, "activities": [{"estimatedCost": 100}]},
        ]})
        fixed, issues, score = verify_itinerary(raw, duration_days=2, total_budget=10_000)
        days = json.loads(fixed)["itinerary"]
        self.assertEqual([d["dayNumber"] for d in days], [1, 2])
        total = sum(a["estimatedCost"] for d in days for a in d["activities"])
        self.assertLessEqual(total, 3_000)
        self.assertTrue(all(a["estimatedCost"] >= 0 for d in days for a in d["activities"]))
        self.assertLess(score, 1.0)
        self.assertTrue(issues)

    def test_clean_itinerary_scores_perfectly(self):
        raw = json.dumps({"itinerary": [{"dayNumber": 1, "activities": [{"estimatedCost": 500}]}]})
        _, issues, score = verify_itinerary(raw, duration_days=1, total_budget=10_000)
        self.assertEqual(issues, [])
        self.assertEqual(score, 1.0)

    def test_recovers_truncated_itinerary_json(self):
        truncated = (
            '{"itinerary":[{"dayNumber":1,"title":"Udaipur Day Trip","activities":['
            '{"time":"9:00 AM","title":"City Palace","type":"attraction","estimatedCost":200},'
            '{"time":"4:30 PM","title":"Lake Pichola","type":"viewpoint","description":"Enjoy the '
        )
        recovered = recover_truncated_itinerary_json(truncated)
        self.assertIsNotNone(recovered)
        days = json.loads(recovered)["itinerary"]
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0]["activities"][0]["title"], "City Palace")

    def test_normalizes_camel_case_context(self):
        mapped = normalize_camel_case_context({"durationDays": 3, "totalBudget": 25000})
        self.assertEqual(mapped["duration_days"], 3)
        self.assertEqual(mapped["total_budget"], 25000)



if __name__ == "__main__":
    unittest.main()
