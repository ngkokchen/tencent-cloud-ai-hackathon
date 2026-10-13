"""User history analysis: dispute patterns, ratings, recurring flags."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class UserHistory:
    user_id: str
    user_type: str               # "rider" or "driver"
    name: str
    account_age_days: int
    rating: float
    total_rides: int
    completion_rate: float       # driver only, 0 for rider
    past_disputes: list         # [{dispute_id, type, outcome, amount, date}]
    dispute_count: int
    recent_dispute_count: int    # within 90 days
    recurring_pattern: bool      # 3+ in 90 days (policy Section 1.7 / 2.9)
    dispute_outcomes: dict       # {outcome: count}
    risk_indicators: list        # [{indicator, detail}]
    summary: str


def _parse_date(date_str: str) -> datetime | None:
    """Try to parse a date string; return None on failure."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S+08:00"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def analyze_user_history(profile: dict, user_type: str = "rider") -> UserHistory:
    """
    Analyze a rider or driver profile: count disputes, detect recurring
    patterns, flag risk indicators.
    """
    past_raw = profile.get("past_disputes", [])

    past_disputes = []
    for d in past_raw:
        past_disputes.append({
            "dispute_id": d.get("dispute_id", ""),
            "type": d.get("type", ""),
            "outcome": d.get("outcome", ""),
            "amount": d.get("amount", 0),
            "date": d.get("date", ""),
        })

    # Count recent disputes (within 90 days)
    # Use a fixed reference date for reproducibility
    now = datetime(2026, 10, 13)
    cutoff = now - timedelta(days=90)

    recent_count = 0
    recent_disputes = []
    for d in past_disputes:
        d_date = _parse_date(d.get("date", ""))
        if d_date and d_date >= cutoff:
            recent_count += 1
            recent_disputes.append(d)

    recurring = recent_count >= 3

    # Outcome distribution
    outcomes: dict[str, int] = {}
    for d in past_disputes:
        outcome = d.get("outcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    # Risk indicators
    risks = []
    rating = profile.get("rating", 0)
    if rating < 4.0:
        risks.append({
            "indicator": "low_rating",
            "detail": f"Rating {rating}/5.0 is below 4.0 threshold",
        })
    if recurring:
        risks.append({
            "indicator": "recurring_dispute_pattern",
            "detail": f"{recent_count} disputes in last 90 days (threshold: 3)",
        })
    if user_type == "driver":
        comp_rate = profile.get("completion_rate", 1.0)
        if comp_rate < 0.85:
            risks.append({
                "indicator": "low_completion_rate",
                "detail": f"Completion rate {comp_rate*100:.0f}% is below 85%",
            })
    account_age = profile.get("account_age_days", 0)
    if account_age < 90:
        risks.append({
            "indicator": "new_account",
            "detail": f"Account only {account_age} days old (< 90 day threshold)",
        })

    # Refund/penalty outcome count
    penalty_outcomes = sum(1 for o, c in outcomes.items()
                           if o in ("refund", "warning", "compensation"))
    if penalty_outcomes >= 2:
        risks.append({
            "indicator": "multiple_penalties",
            "detail": f"{penalty_outcomes} past dispute(s) resulted in penalties",
        })

    # Build summary
    name = profile.get("name", "N/A")
    uid = profile.get(f"{user_type}_id", "N/A")
    total_rides = profile.get("total_rides", 0)

    summary_parts = [
        f"{user_type.capitalize()} {name} ({uid})",
        f"account age {account_age} days",
        f"rating {rating}/5.0",
        f"{total_rides} total rides",
        f"{len(past_disputes)} past dispute(s)",
        f"{recent_count} within 90 days",
    ]
    if user_type == "driver":
        comp_rate = profile.get("completion_rate", 0)
        summary_parts.append(f"completion rate {comp_rate*100:.0f}%")
    if recurring:
        summary_parts.append("RECURRING PATTERN FLAGGED")
    if risks:
        summary_parts.append(f"{len(risks)} risk indicator(s)")
    summary = ". ".join(summary_parts) + "."

    return UserHistory(
        user_id=uid,
        user_type=user_type,
        name=name,
        account_age_days=account_age,
        rating=rating,
        total_rides=total_rides,
        completion_rate=profile.get("completion_rate", 0),
        past_disputes=past_disputes,
        dispute_count=len(past_disputes),
        recent_dispute_count=recent_count,
        recurring_pattern=recurring,
        dispute_outcomes=outcomes,
        risk_indicators=risks,
        summary=summary,
    )
