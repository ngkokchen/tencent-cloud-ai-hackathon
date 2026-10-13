"""GPS route analysis: haversine distance, deviation detection, unexpected stops."""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from config.settings import (
    DEVIATION_TOLERANCE_PCT,
    DEVIATION_MINOR_PCT,
    DEVIATION_SIGNIFICANT_PCT,
    STOP_RADIUS_M,
    STOP_MIN_DURATION_S,
    TRAFFIC_EXCEPTION_SPEED_KMH,
    TRAFFIC_EXCEPTION_MAX_DEVIATION_PCT,
)


@dataclass
class RouteAnalysis:
    trip_id: str
    optimal_distance_km: float
    actual_distance_km: float
    extra_distance_km: float
    extra_distance_pct: float
    deviation_category: str          # within_tolerance / minor / significant / major / traffic_justified
    estimated_duration_min: float
    actual_duration_min: float
    time_difference_min: float
    unexpected_stops: list            # [{lat, lng, duration_min, timestamp, note}]
    optimal_route_points: int
    actual_route_points: int
    traffic_optimal_speed_kmh: Optional[float]
    traffic_actual_speed_kmh: Optional[float]
    traffic_optimal_congestion: Optional[str]
    traffic_actual_congestion: Optional[str]
    traffic_exception_applies: bool
    summary: str


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two GPS points in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def route_total_distance(route_points: list[dict]) -> float:
    """Sum haversine distances across a sequence of GPS waypoints."""
    total = 0.0
    for i in range(1, len(route_points)):
        total += haversine_km(
            route_points[i - 1]["lat"], route_points[i - 1]["lng"],
            route_points[i]["lat"], route_points[i]["lng"],
        )
    return round(total, 2)


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp, handling +08:00 offset."""
    return datetime.fromisoformat(ts)


def detect_unexpected_stops(route_points: list[dict]) -> list[dict]:
    """
    Detect stationary points where the vehicle stayed within STOP_RADIUS_M
    for at least STOP_MIN_DURATION_S seconds.
    """
    stops = []
    for i in range(1, len(route_points)):
        dist_m = haversine_km(
            route_points[i - 1]["lat"], route_points[i - 1]["lng"],
            route_points[i]["lat"], route_points[i]["lng"],
        ) * 1000

        if dist_m < STOP_RADIUS_M:
            try:
                t1 = _parse_ts(route_points[i - 1]["timestamp"])
                t2 = _parse_ts(route_points[i]["timestamp"])
                duration_s = (t2 - t1).total_seconds()
            except (ValueError, KeyError):
                continue

            if duration_s >= STOP_MIN_DURATION_S:
                stops.append({
                    "lat": route_points[i]["lat"],
                    "lng": route_points[i]["lng"],
                    "duration_min": round(duration_s / 60, 1),
                    "timestamp": route_points[i]["timestamp"],
                    "note": route_points[i].get("note", ""),
                })
    return stops


def categorize_deviation(pct: float) -> str:
    """Map deviation percentage to policy category (Section 1.3)."""
    if pct <= DEVIATION_TOLERANCE_PCT:
        return "within_tolerance"
    elif pct <= DEVIATION_MINOR_PCT:
        return "minor"
    elif pct <= DEVIATION_SIGNIFICANT_PCT:
        return "significant"
    else:
        return "major"


def check_traffic_exception(traffic: dict, deviation_pct: float) -> bool:
    """
    Check if the traffic exception applies (policy Section 1.4).
    All three conditions must hold:
      1. optimal route avg speed < 20 km/h
      2. deviation <= 15%
      3. (communication check is done by the agent, not here)
    """
    if not traffic:
        return False
    optimal_speed = traffic.get("optimal_route_avg_speed_kmh", 999)
    if optimal_speed >= TRAFFIC_EXCEPTION_SPEED_KMH:
        return False
    if deviation_pct > TRAFFIC_EXCEPTION_MAX_DEVIATION_PCT:
        return False
    return True


def analyze_route(trip: dict) -> RouteAnalysis:
    """
    Full route analysis: compute distances from GPS waypoints,
    detect stops, check traffic exception, categorize deviation.
    """
    optimal_route = trip.get("optimal_route", [])
    actual_route = trip.get("actual_route", [])

    # Compute from GPS points if available, fall back to stored values
    computed_optimal = route_total_distance(optimal_route) if optimal_route else 0.0
    computed_actual = route_total_distance(actual_route) if actual_route else 0.0

    # Prefer pre-calculated values (they're authoritative in sample data)
    optimal_dist = trip.get("estimated_distance_km", computed_optimal)
    actual_dist = trip.get("actual_distance_km", computed_actual)

    extra_km = round(actual_dist - optimal_dist, 2)
    extra_pct = round((extra_km / optimal_dist * 100) if optimal_dist > 0 else 0.0, 1)

    est_duration = trip.get("estimated_duration_min", 0)
    actual_duration = trip.get("actual_duration_min", 0)
    time_diff = actual_duration - est_duration

    stops = detect_unexpected_stops(actual_route) if actual_route else []

    traffic = trip.get("traffic_conditions", {})
    traffic_exception = check_traffic_exception(traffic, extra_pct)

    category = categorize_deviation(extra_pct)
    # If traffic exception applies and deviation is minor, reclassify
    if traffic_exception and category == "minor":
        category = "traffic_justified"

    summary_parts = [
        f"Actual route {actual_dist:.1f}km vs optimal {optimal_dist:.1f}km",
        f"({extra_pct:+.1f}% deviation, category: {category})",
        f"Time: {actual_duration}min vs est {est_duration}min (+{time_diff}min)",
    ]
    if stops:
        summary_parts.append(f"{len(stops)} unexpected stop(s)")
    if traffic_exception:
        summary_parts.append("Traffic exception may apply (optimal route was congested)")
    summary = ". ".join(summary_parts) + "."

    return RouteAnalysis(
        trip_id=trip.get("ride_id", ""),
        optimal_distance_km=round(optimal_dist, 2),
        actual_distance_km=round(actual_dist, 2),
        extra_distance_km=extra_km,
        extra_distance_pct=extra_pct,
        deviation_category=category,
        estimated_duration_min=est_duration,
        actual_duration_min=actual_duration,
        time_difference_min=time_diff,
        unexpected_stops=stops,
        optimal_route_points=len(optimal_route),
        actual_route_points=len(actual_route),
        traffic_optimal_speed_kmh=traffic.get("optimal_route_avg_speed_kmh"),
        traffic_actual_speed_kmh=traffic.get("actual_route_avg_speed_kmh"),
        traffic_optimal_congestion=traffic.get("optimal_route_congestion"),
        traffic_actual_congestion=traffic.get("actual_route_congestion"),
        traffic_exception_applies=traffic_exception,
        summary=summary,
    )
