"""
CONCODE Neural Brain -- TripVerse Travel Intelligence (Universal v3.0 bridge)

Deterministic verification and repair layer applied to model-generated
TripVerse itineraries. It never invents activities; it only validates and
corrects structure and arithmetic:

  1. Day-count critic: trims surplus days, renumbers days sequentially.
  2. Budget critic: scales activity costs so the itinerary stays within the
     food-and-activities share of the traveler's total budget.
  3. Cost sanitation: coerces non-numeric or negative costs to integers >= 0.
  4. Exact budget breakdown: integer allocation that always sums to the total.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

# Share of the total budget available for food and activities (matches the
# TripVerse client allocation: food 20% + activities 10%).
FOOD_ACTIVITY_SHARE = 0.30

_DOMESTIC_RATIOS = (("transport", 0.28), ("stays", 0.35), ("food", 0.20), ("activities", 0.10))
_INTERNATIONAL_RATIOS = (("transport", 0.38), ("stays", 0.30), ("food", 0.18), ("activities", 0.10))
_INTERNATIONAL_HINTS = (
    "dubai", "tokyo", "japan", "paris", "london", "singapore", "bali", "europe",
    "thailand", "bangkok", "maldives", "usa", "new york", "switzerland",
)


def _to_cost(value: Any) -> int:
    """Coerce a model-written cost into a non-negative integer."""
    try:
        number = float(str(value).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, int(round(number)))


_CAMEL_TO_SNAKE_KEYS = {
    "durationDays": "duration_days",
    "totalBudget": "total_budget",
    "travelersCount": "travelers_count",
    "travelerType": "traveler_type",
    "specialRequests": "special_requests",
    "transportMode": "transport_mode",
    "accommodationType": "accommodation_type",
    "foodPreference": "food_preference",
    "knownDestinationHighlights": "known_destination_highlights",
    "transportOptions": "transport_options",
    "transportDeals": "transport_options",
}


def normalize_camel_case_context(raw: Any) -> Any:
    """Map camelCase keys sent by TripVerse frontend/Vite proxy to snake_case."""
    if not isinstance(raw, dict):
        return raw
    normalized = dict(raw)
    for camel_key, snake_key in _CAMEL_TO_SNAKE_KEYS.items():
        if camel_key in normalized and snake_key not in normalized:
            normalized[snake_key] = normalized[camel_key]
    return normalized


def recover_truncated_itinerary_json(reply: str) -> Optional[str]:
    """
    Salvage valid model-generated itinerary JSON when surrounded by prose or
    truncated at the token limit, without inventing any activities.
    """
    candidate = reply.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].strip()

    start = candidate.find("{")
    if start < 0:
        return None
    fragment = candidate[start:]

    closing_suffixes = ("", "}", "]}", "}]}", "]}]}")
    # Walk backwards across '}' positions to find the longest valid prefix
    brace_positions = [idx for idx, ch in enumerate(fragment) if ch == "}"]
    for pos in reversed(brace_positions):
        prefix = fragment[: pos + 1]
        for suffix in closing_suffixes:
            try:
                parsed = json.loads(prefix + suffix)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue
            itinerary = parsed.get("itinerary")
            if not isinstance(itinerary, list) or not itinerary:
                continue
            valid_days = [
                d for d in itinerary
                if isinstance(d, dict) and isinstance(d.get("activities"), list) and len(d.get("activities")) > 0
            ]
            if valid_days:
                parsed["itinerary"] = valid_days
                return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    return None



def exact_budget_breakdown(total_budget: float, destination: str, currency: str = "INR") -> Dict[str, Any]:
    """Integer allocation whose components always sum exactly to the total."""
    total = max(0, int(round(total_budget)))
    is_international = any(hint in (destination or "").lower() for hint in _INTERNATIONAL_HINTS)
    ratios = _INTERNATIONAL_RATIOS if is_international else _DOMESTIC_RATIOS
    breakdown: Dict[str, Any] = {name: int(total * ratio) for name, ratio in ratios}
    breakdown["buffer"] = total - sum(breakdown.values())
    norm_currency = (currency or "INR").upper()
    currency_symbol = "₹" if norm_currency == "INR" else norm_currency
    breakdown.update({
        "total": total,
        "isEstimate": True,
        "currency": norm_currency,
        "currencySymbol": currency_symbol,
    })
    return breakdown


def build_structured_itinerary(
    itinerary_json: str,
    destination: str,
    duration_days: int,
    total_budget: float,
    food_preference: str = "all",
    currency: str = "INR",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Build both the raw `itinerary` day array (used by TripVerse's plannerEngine)
    and the rich `structured_itinerary` object (used by TripVerse's chat UI).
    """
    parsed = json.loads(itinerary_json)
    raw_days: List[Dict[str, Any]] = [d for d in parsed.get("itinerary", []) if isinstance(d, dict)]
    dest_label = destination or "your destination"
    norm_currency = (currency or "INR").upper()
    currency_symbol = "₹" if norm_currency == "INR" else norm_currency

    structured_days: List[Dict[str, Any]] = []
    for day in raw_days:
        acts = [a for a in day.get("activities", []) if isinstance(a, dict)]
        morning = acts[0].get("description") or acts[0].get("title") if len(acts) > 0 else f"Explore {dest_label} morning highlights."
        afternoon = acts[1].get("description") or acts[1].get("title") if len(acts) > 1 else f"Regional lunch and afternoon sightseeing in {dest_label}."
        evening = acts[2].get("description") or acts[2].get("title") if len(acts) > 2 else f"Sunset viewpoint and relaxed evening walk in {dest_label}."
        food_act = next((a for a in acts if a.get("type") == "food"), None)
        food_text = (
            food_act.get("title") or food_act.get("description")
            if food_act else f"Regional {food_preference or 'local'} specialties"
        )
        day_cost = int(day.get("dayEstimatedCost") or sum(_to_cost(a.get("estimatedCost")) for a in acts))
        structured_days.append({
            "dayNumber": day.get("dayNumber", 1),
            "title": day.get("title") or f"Day {day.get('dayNumber', 1)} in {dest_label}",
            "theme": day.get("theme") or "Cultural & Scenic Highlights",
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "food": food_text,
            "cost": day_cost,
            "activities": acts,
        })

    structured = {
        "destination": dest_label,
        "durationDays": len(raw_days) or max(1, duration_days),
        "targetBudget": int(round(total_budget)),
        "totalCost": sum(d["cost"] for d in structured_days),
        "currencySymbol": currency_symbol,
        "days": structured_days,
    }
    return raw_days, structured


def verify_itinerary(
    itinerary_json: str,
    duration_days: int,
    total_budget: float,
) -> Tuple[str, List[str], float]:
    """
    Validate and repair a structured itinerary.

    Returns (repaired_json, issues_fixed, critic_score). The critic score is
    1.0 when no repair was needed and decreases with each correction.
    """
    parsed = json.loads(itinerary_json)
    days: List[Dict[str, Any]] = [d for d in parsed.get("itinerary", []) if isinstance(d, dict)]
    issues: List[str] = []

    if duration_days > 0 and len(days) > duration_days:
        issues.append(f"trimmed {len(days) - duration_days} surplus day(s)")
        days = days[:duration_days]
    if duration_days > 0 and len(days) < duration_days:
        issues.append(f"model returned {len(days)} of {duration_days} requested day(s)")

    total_cost = 0
    for index, day in enumerate(days, start=1):
        if day.get("dayNumber") != index:
            if "renumbered days" not in issues:
                issues.append("renumbered days")
            day["dayNumber"] = index
        activities = [a for a in day.get("activities", []) if isinstance(a, dict)]
        for activity in activities:
            original = activity.get("estimatedCost")
            cost = _to_cost(original)
            if original != cost:
                if "sanitized costs" not in issues:
                    issues.append("sanitized costs")
                activity["estimatedCost"] = cost
            total_cost += cost
        day["activities"] = activities

    cap = int(total_budget * FOOD_ACTIVITY_SHARE) if total_budget > 0 else 0
    if cap and total_cost > cap:
        scale = cap / total_cost
        issues.append(f"scaled costs from {total_cost} to within {cap} budget cap")
        total_cost = 0
        for day in days:
            for activity in day["activities"]:
                activity["estimatedCost"] = int(activity["estimatedCost"] * scale)
                total_cost += activity["estimatedCost"]

    for day in days:
        day["dayEstimatedCost"] = sum(a["estimatedCost"] for a in day["activities"])

    parsed["itinerary"] = days
    critic_score = max(0.0, round(1.0 - 0.1 * len(issues), 2))
    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":")), issues, critic_score


def traveler_memory_context(memory: Any, session_id: str, query: str) -> str:
    """Recall prior verified TripVerse episodes for this traveler session."""
    if memory is None:
        return ""
    recalled = memory.recall_similar(f"tripverse {session_id} {query}", top_k=2)
    lines = [
        f"- Earlier request: {item['goal'][:160]} | Outcome: {item['solution_summary'][:160]}"
        for item in recalled
        if "tripverse" in item.get("guilds", [])
    ]
    return "\n".join(lines)


def summarize_for_memory(mode: str, reply: str, destination: str) -> Optional[str]:
    """Produce a compact summary of a travel reply for episodic memory."""
    if mode == "itinerary":
        try:
            days = json.loads(reply).get("itinerary", [])
            titles = "; ".join(str(d.get("title", "")) for d in days[:4])
            return f"{len(days)}-day {destination} itinerary: {titles}"
        except (json.JSONDecodeError, AttributeError):
            return None
    return reply.strip()[:300] or None
