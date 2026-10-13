"""
Tool functions exposed to agents.

Each tool takes a simple ID argument, loads the relevant data from sample
JSON files, runs domain-specific analysis, and returns a structured dict
that agents can cite in their arguments.

Tools:
    get_route_analysis(trip_id)    — GPS deviation, stops, traffic exception
    get_chat_log(trip_id)          — messages with sentiment + threat flags
    get_fare_breakdown(trip_id)     — component validation, anomalies, overcharge
    get_user_history(user_id)      — dispute patterns, rating, risk indicators
    get_policy(dispute_type)       — relevant policy clauses with section numbers

Usage in LangGraph:
    from graph.tools import TOOL_REGISTRY
    # Each tool returns a dict; agents call them and log the result to message_log.
"""

import re
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from evidence.loaders import load_case_by_ride_id, load_case_by_user_id
from evidence.gps import analyze_route
from evidence.chat import analyze_chat
from evidence.fare import analyze_fare
from evidence.history import analyze_user_history
from config.settings import POLICY_FILE


# ─── get_route_analysis ──────────────────────────────────────────────

def get_route_analysis(trip_id: str) -> dict:
    """
    Compare actual vs optimal route for a trip.

    Returns extra_distance_pct, deviation_category (within_tolerance /
    minor / significant / major / traffic_justified), time_difference_min,
    unexpected_stops, traffic_exception_applies, and a human-readable summary.
    """
    case = load_case_by_ride_id(trip_id)
    if case is None:
        return {"error": f"No case found for trip_id '{trip_id}'"}

    result = analyze_route(case.trip)
    return {
        "tool": "get_route_analysis",
        "trip_id": trip_id,
        "optimal_distance_km": result.optimal_distance_km,
        "actual_distance_km": result.actual_distance_km,
        "extra_distance_km": result.extra_distance_km,
        "extra_distance_pct": result.extra_distance_pct,
        "deviation_category": result.deviation_category,
        "estimated_duration_min": result.estimated_duration_min,
        "actual_duration_min": result.actual_duration_min,
        "time_difference_min": result.time_difference_min,
        "unexpected_stops": result.unexpected_stops,
        "optimal_route_points": result.optimal_route_points,
        "actual_route_points": result.actual_route_points,
        "traffic_optimal_speed_kmh": result.traffic_optimal_speed_kmh,
        "traffic_actual_speed_kmh": result.traffic_actual_speed_kmh,
        "traffic_optimal_congestion": result.traffic_optimal_congestion,
        "traffic_actual_congestion": result.traffic_actual_congestion,
        "traffic_exception_applies": result.traffic_exception_applies,
        "summary": result.summary,
    }


# ─── get_chat_log ────────────────────────────────────────────────────

def get_chat_log(trip_id: str) -> dict:
    """
    Retrieve chat logs between rider, driver, and system for a trip.
    Each message includes a sentiment label (positive / neutral / negative /
    hostile) and a threat flag. Also extracts evidence-relevant key exchanges
    and tracks contact dynamics (who initiated, did driver respond).
    """
    case = load_case_by_ride_id(trip_id)
    if case is None:
        return {"error": f"No case found for trip_id '{trip_id}'"}

    dispute_type = case.dispute.get("dispute_type", "")
    result = analyze_chat(case.chat_logs, trip_id, dispute_type)
    return {
        "tool": "get_chat_log",
        "trip_id": trip_id,
        "messages": result.messages,
        "total_messages": result.total_messages,
        "rider_messages": result.rider_messages,
        "driver_messages": result.driver_messages,
        "system_messages": result.system_messages,
        "sentiment_summary": result.sentiment_summary,
        "threat_detected": result.threat_detected,
        "threat_messages": result.threat_messages,
        "key_exchanges": result.key_exchanges,
        "rider_initiated_contact": result.rider_initiated_contact,
        "driver_initiated_contact": result.driver_initiated_contact,
        "driver_responded_to_rider": result.driver_responded_to_rider,
        "summary": result.summary,
    }


# ─── get_fare_breakdown ─────────────────────────────────────────────

def get_fare_breakdown(trip_id: str) -> dict:
    """
    Retrieve and validate fare breakdown for a trip.
    Validates that components add up (base + distance + time + surge - promo
    + cancellation = total), flags surge > 1.5x and promo anomalies, and
    computes overcharge vs expected optimal fare.
    """
    case = load_case_by_ride_id(trip_id)
    if case is None:
        return {"error": f"No case found for trip_id '{trip_id}'"}

    result = analyze_fare(case.fare_breakdown, trip_id)
    return {
        "tool": "get_fare_breakdown",
        "trip_id": trip_id,
        "base_fare": result.base_fare,
        "distance_charge": result.distance_charge,
        "distance_km": result.distance_km,
        "time_charge": result.time_charge,
        "time_min": result.time_min,
        "subtotal": result.subtotal,
        "surge_multiplier": result.surge_multiplier,
        "surge_charge": result.surge_charge,
        "promo_discount": result.promo_discount,
        "cancellation_fee": result.cancellation_fee,
        "total": result.total,
        "currency": result.currency,
        "expected_total_optimal": result.expected_total_optimal,
        "overcharge_amount": result.overcharge_amount,
        "anomalies": result.anomalies,
        "component_validation": result.component_validation,
        "summary": result.summary,
    }


# ─── get_user_history ───────────────────────────────────────────────

def get_user_history(user_id: str) -> dict:
    """
    Retrieve dispute history, rating, and profile for a rider or driver.
    Returns account age, rating, total rides, completion rate (driver),
    past disputes with outcomes, recurring pattern flag (3+ in 90 days),
    and risk indicators.
    """
    case = load_case_by_user_id(user_id)
    if case is None:
        return {"error": f"No case found for user_id '{user_id}'"}

    # Determine rider vs driver
    if case.rider_profile.get("rider_id") == user_id:
        profile = case.rider_profile
        user_type = "rider"
    elif case.driver_profile.get("driver_id") == user_id:
        profile = case.driver_profile
        user_type = "driver"
    else:
        return {"error": f"user_id '{user_id}' not found in case profiles"}

    result = analyze_user_history(profile, user_type)
    return {
        "tool": "get_user_history",
        "user_id": result.user_id,
        "user_type": result.user_type,
        "name": result.name,
        "account_age_days": result.account_age_days,
        "rating": result.rating,
        "total_rides": result.total_rides,
        "completion_rate": result.completion_rate,
        "past_disputes": result.past_disputes,
        "dispute_count": result.dispute_count,
        "recent_dispute_count": result.recent_dispute_count,
        "recurring_pattern": result.recurring_pattern,
        "dispute_outcomes": result.dispute_outcomes,
        "risk_indicators": result.risk_indicators,
        "summary": result.summary,
    }


# ─── get_policy ─────────────────────────────────────────────────────

_POLICY_CACHE: str | None = None


def _load_policy_text() -> str:
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        _POLICY_CACHE = POLICY_FILE.read_text(encoding="utf-8")
    return _POLICY_CACHE


def _parse_policy_sections(text: str) -> list[dict]:
    """Parse the policy markdown into top-level sections."""
    sections = []
    current_num = None
    current_title = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        match = re.match(r"^##\s+(\d+)\.\s+(.+)", line)
        if match:
            if current_num is not None:
                sections.append({
                    "section_number": current_num,
                    "title": current_title,
                    "text": "\n".join(current_lines).strip(),
                })
            current_num = match.group(1)
            current_title = match.group(2)
            current_lines = []
        elif current_num is not None:
            current_lines.append(line)

    if current_num is not None:
        sections.append({
            "section_number": current_num,
            "title": current_title,
            "text": "\n".join(current_lines).strip(),
        })

    return sections


def _extract_key_clauses(section_text: str, section_num: str) -> list[dict]:
    """Extract ### sub-section headers as citeable clauses."""
    clauses = []
    for line in section_text.split("\n"):
        match = re.match(r"^###\s+(\d+\.\d+)\s+(.+)", line)
        if match:
            clauses.append({
                "clause": match.group(1),
                "title": match.group(2),
                "section": section_num,
            })
    return clauses


def get_policy(dispute_type: str) -> dict:
    """
    Retrieve relevant company policy clauses for a dispute type.

    For 'route_deviation': returns Section 1 (Route Deviation) + Section 3 (General).
    For 'no_show': returns Section 2 (No-Show) + Section 3 (General).
    For unknown types: returns all sections.

    Each section includes its full text and a list of citeable sub-clauses
    (e.g. '1.3 Deviation Thresholds', '2.5 Early Departure Rule').
    """
    text = _load_policy_text()
    all_sections = _parse_policy_sections(text)

    # Determine which sections to return
    if dispute_type == "route_deviation":
        primary = {"1"}
    elif dispute_type == "no_show":
        primary = {"2"}
    else:
        primary = {"1", "2"}

    # Always include Section 3 (General Provisions)
    relevant_nums = primary | {"3"}

    relevant = [s for s in all_sections if s["section_number"] in relevant_nums]

    # Extract key clauses from relevant sections
    key_clauses = []
    for sec in relevant:
        key_clauses.extend(_extract_key_clauses(sec["text"], sec["section_number"]))

    summary = (
        f"Retrieved {len(relevant)} section(s) for '{dispute_type}'. "
        f"{len(key_clauses)} citeable clauses available. "
        f"Section 3 (General Provisions) always included for confidence & remedy rules."
    )

    return {
        "tool": "get_policy",
        "dispute_type": dispute_type,
        "sections": relevant,
        "key_clauses": key_clauses,
        "full_text_available": True,
        "summary": summary,
    }


# ─── Tool Registry ───────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, Callable] = {
    "get_route_analysis": get_route_analysis,
    "get_chat_log": get_chat_log,
    "get_fare_breakdown": get_fare_breakdown,
    "get_user_history": get_user_history,
    "get_policy": get_policy,
}

# Tool descriptions for agent system prompts
TOOL_DESCRIPTIONS = {
    "get_route_analysis": (
        "Compare actual vs optimal GPS route. Returns extra_distance_pct, "
        "deviation_category, unexpected_stops, traffic_exception flag. "
        "Arg: trip_id (e.g. 'RIDE-7821')"
    ),
    "get_chat_log": (
        "Retrieve chat logs with per-message sentiment and threat detection. "
        "Returns key_exchanges relevant to the dispute. "
        "Arg: trip_id (e.g. 'RIDE-7821')"
    ),
    "get_fare_breakdown": (
        "Validate fare components and flag anomalies (surge, promo, overcharge). "
        "Returns overcharge_amount vs expected optimal fare. "
        "Arg: trip_id (e.g. 'RIDE-7821')"
    ),
    "get_user_history": (
        "Retrieve rider or driver history: past disputes, rating, account age, "
        "recurring pattern flag, risk indicators. "
        "Arg: user_id (e.g. 'R-8821' for rider, 'D-3401' for driver)"
    ),
    "get_policy": (
        "Retrieve relevant policy clauses for a dispute type. Returns section "
        "text and citeable sub-clauses (e.g. '1.3 Deviation Thresholds'). "
        "Arg: dispute_type ('route_deviation' or 'no_show')"
    ),
}
