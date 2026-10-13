"""Fare breakdown analysis: component validation, anomaly detection, overcharge calc."""

from dataclasses import dataclass, field

from config.settings import (
    BASE_FARE,
    DISTANCE_RATE_PER_KM,
    TIME_RATE_PER_MIN,
    SURGE_ANOMALY_THRESHOLD,
)


@dataclass
class FareAnalysis:
    trip_id: str
    base_fare: float
    distance_charge: float
    distance_km: float
    time_charge: float
    time_min: float
    subtotal: float
    surge_multiplier: float
    surge_charge: float
    promo_discount: float
    cancellation_fee: float
    total: float
    currency: str
    expected_total_optimal: float
    overcharge_amount: float
    anomalies: list          # [{component, issue, severity}]
    component_validation: dict   # {component: {expected, actual, valid}}
    summary: str


def validate_fare_components(fare: dict) -> dict:
    """
    Validate that each fare component is internally consistent.
    Checks: distance_charge = distance_km * rate, time_charge = time_min * rate,
    subtotal = base + distance + time, surge = subtotal * (mult - 1),
    total = subtotal + surge - promo + cancellation.
    """
    validation = {}

    # Distance charge
    expected_dist = round(fare.get("distance_km", 0) * DISTANCE_RATE_PER_KM, 2)
    actual_dist = fare.get("distance_charge", 0)
    validation["distance_charge"] = {
        "expected": expected_dist,
        "actual": actual_dist,
        "valid": abs(expected_dist - actual_dist) < 0.10,
    }

    # Time charge
    expected_time = round(fare.get("time_min", 0) * TIME_RATE_PER_MIN, 2)
    actual_time = fare.get("time_charge", 0)
    validation["time_charge"] = {
        "expected": expected_time,
        "actual": actual_time,
        "valid": abs(expected_time - actual_time) < 0.10,
    }

    # Subtotal = base + distance + time
    expected_subtotal = round(BASE_FARE + actual_dist + actual_time, 2)
    actual_subtotal = fare.get("subtotal", 0)
    validation["subtotal"] = {
        "expected": expected_subtotal,
        "actual": actual_subtotal,
        "valid": abs(expected_subtotal - actual_subtotal) < 0.10,
    }

    # Surge charge = subtotal * (multiplier - 1)
    surge_mult = fare.get("surge_multiplier", 1.0)
    expected_surge = round(actual_subtotal * (surge_mult - 1.0), 2) if surge_mult > 1.0 else 0.0
    actual_surge = fare.get("surge_charge", 0)
    validation["surge_charge"] = {
        "expected": expected_surge,
        "actual": actual_surge,
        "valid": abs(expected_surge - actual_surge) < 0.10,
    }

    # Total = subtotal + surge - promo + cancellation
    expected_total = round(
        actual_subtotal + actual_surge
        - fare.get("promo_discount", 0)
        + fare.get("cancellation_fee", 0),
        2,
    )
    actual_total = fare.get("total", 0)
    validation["total"] = {
        "expected": expected_total,
        "actual": actual_total,
        "valid": abs(expected_total - actual_total) < 0.10,
    }

    return validation


def detect_anomalies(fare: dict) -> list:
    """Flag surge multiplier > threshold, excessive promo, cancellation fee presence."""
    anomalies = []

    surge = fare.get("surge_multiplier", 1.0)
    if surge > SURGE_ANOMALY_THRESHOLD:
        anomalies.append({
            "component": "surge_multiplier",
            "issue": f"Surge {surge}x exceeds threshold {SURGE_ANOMALY_THRESHOLD}x",
            "severity": "warning",
        })

    promo = fare.get("promo_discount", 0)
    if promo > 0 and promo > fare.get("subtotal", 0) * 0.5:
        anomalies.append({
            "component": "promo_discount",
            "issue": f"Promo ${promo:.2f} exceeds 50% of subtotal",
            "severity": "info",
        })

    cancellation = fare.get("cancellation_fee", 0)
    if cancellation > 0:
        anomalies.append({
            "component": "cancellation_fee",
            "issue": f"Cancellation/no-show fee ${cancellation:.2f} applied",
            "severity": "info",
        })

    return anomalies


def analyze_fare(fare: dict, trip_id: str = "") -> FareAnalysis:
    """
    Full fare analysis: validate components, detect anomalies,
    compute overcharge vs expected optimal fare.
    """
    validation = validate_fare_components(fare)
    anomalies = detect_anomalies(fare)

    expected_optimal = fare.get("expected_total_optimal", 0)
    total = fare.get("total", 0)
    overcharge = round(total - expected_optimal, 2) if expected_optimal > 0 else 0.0

    if overcharge > 0:
        anomalies.append({
            "component": "total",
            "issue": (
                f"Total ${total:.2f} exceeds expected optimal ${expected_optimal:.2f} "
                f"by ${overcharge:.2f}"
            ),
            "severity": "critical",
        })

    # Build human-readable summary
    parts = [
        f"Total: ${fare.get('total', 0):.2f} {fare.get('currency', 'SGD')}",
        f"base ${fare.get('base_fare', 0):.2f}",
        f"distance ${fare.get('distance_charge', 0):.2f} ({fare.get('distance_km', 0)}km)",
        f"time ${fare.get('time_charge', 0):.2f} ({fare.get('time_min', 0)}min)",
    ]
    if fare.get("surge_multiplier", 1.0) > 1.0:
        parts.append(f"surge {fare.get('surge_multiplier', 1.0)}x (${fare.get('surge_charge', 0):.2f})")
    if fare.get("promo_discount", 0) > 0:
        parts.append(f"promo -${fare.get('promo_discount', 0):.2f}")
    if fare.get("cancellation_fee", 0) > 0:
        parts.append(f"cancellation ${fare.get('cancellation_fee', 0):.2f}")
    if overcharge > 0:
        parts.append(f"overcharge vs optimal: ${overcharge:.2f}")
    if anomalies:
        parts.append(f"{len(anomalies)} anomaly/anomalies")
    summary = ". ".join(parts) + "."

    return FareAnalysis(
        trip_id=trip_id,
        base_fare=fare.get("base_fare", 0),
        distance_charge=fare.get("distance_charge", 0),
        distance_km=fare.get("distance_km", 0),
        time_charge=fare.get("time_charge", 0),
        time_min=fare.get("time_min", 0),
        subtotal=fare.get("subtotal", 0),
        surge_multiplier=fare.get("surge_multiplier", 1.0),
        surge_charge=fare.get("surge_charge", 0),
        promo_discount=fare.get("promo_discount", 0),
        cancellation_fee=fare.get("cancellation_fee", 0),
        total=fare.get("total", 0),
        currency=fare.get("currency", "SGD"),
        expected_total_optimal=expected_optimal,
        overcharge_amount=overcharge,
        anomalies=anomalies,
        component_validation=validation,
        summary=summary,
    )
