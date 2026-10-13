"""Chat log analysis: per-message sentiment, threat detection, evidence extraction."""

from dataclasses import dataclass, field

# Keyword lists for lightweight sentiment classification
NEGATIVE_KEYWORDS = [
    "angry", "unacceptable", "terrible", "worst", "horrible",
    "complaint", "dispute", "ridiculous", "scam", "cheat",
    "wrong", "not right", "longer than", "too long",
    "where are you", "still waiting", "doesn't seem right",
    "way too long", "unacceptable",
]
HOSTILE_KEYWORDS = [
    "sue", "lawyer", "police", "threat", "violence",
    "danger", "unsafe", "illegal", "report you",
]
POSITIVE_KEYWORDS = [
    "thanks", "thank you", "great", "good", "excellent",
    "appreciate", "sorry", "no problem", "fine", "trust",
]

# Keywords that make a message evidence-relevant
EVIDENCE_KEYWORDS = [
    "route", "way", "going", "direction", "lost", "wrong way", "longer",
    "shortcut", "detour", "jam", "traffic",
    "waiting", "wait", "arrived", "arrival", "where are you", "here",
    "cancel", "no-show", "late", "early", "left",
    "dispute", "complaint", "unacceptable", "trust",
    "fee", "charge", "refund", "fare", "pay",
]


@dataclass
class ChatAnalysis:
    trip_id: str
    messages: list                 # [{sender, timestamp, message, sentiment, threat_flag}]
    total_messages: int
    rider_messages: int
    driver_messages: int
    system_messages: int
    sentiment_summary: str         # predominantly_negative / mixed_with_negativity / neutral_or_positive
    threat_detected: bool
    threat_messages: list          # raw message texts that triggered threat flag
    key_exchanges: list            # evidence-relevant messages
    rider_initiated_contact: bool
    driver_initiated_contact: bool
    driver_responded_to_rider: bool
    summary: str


def classify_sentiment(message: str) -> tuple[str, bool]:
    """
    Classify a single message's sentiment.
    Returns (sentiment_label, threat_flag).
    Priority: hostile > negative > positive > neutral.
    """
    msg_lower = message.lower()

    for kw in HOSTILE_KEYWORDS:
        if kw in msg_lower:
            return ("hostile", True)

    for kw in NEGATIVE_KEYWORDS:
        if kw in msg_lower:
            return ("negative", False)

    for kw in POSITIVE_KEYWORDS:
        if kw in msg_lower:
            return ("positive", False)

    return ("neutral", False)


def is_evidence_relevant(message: str) -> bool:
    """Determine if a message contains evidence-relevant content."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in EVIDENCE_KEYWORDS)


def analyze_chat(chat_logs: list, trip_id: str = "", dispute_type: str = "") -> ChatAnalysis:
    """
    Full chat analysis: classify sentiment per message, detect threats,
    extract evidence-relevant exchanges, and track contact dynamics.
    """
    messages = []
    threat_messages = []
    key_exchanges = []

    rider_first_msg = None
    driver_first_msg = None
    rider_asked_driver = False
    driver_responded = False

    for entry in chat_logs:
        msg = entry.get("message", "")
        sender = entry.get("sender", "")
        sentiment, threat = classify_sentiment(msg)

        messages.append({
            "sender": sender,
            "timestamp": entry.get("timestamp", ""),
            "message": msg,
            "sentiment": sentiment,
            "threat_flag": threat,
        })

        if threat:
            threat_messages.append(msg)

        if is_evidence_relevant(msg):
            key_exchanges.append({
                "sender": sender,
                "timestamp": entry.get("timestamp", ""),
                "message": msg,
                "sentiment": sentiment,
            })

        # Track who initiated contact first
        if sender == "rider" and rider_first_msg is None:
            rider_first_msg = entry.get("timestamp")
            rider_asked_driver = any(kw in msg.lower() for kw in ["where", "here", "see you", "arrived"])
        if sender == "driver" and driver_first_msg is None:
            driver_first_msg = entry.get("timestamp")

        # Track if driver responded to rider's messages
        if sender == "driver" and rider_asked_driver:
            driver_responded = True

    rider_count = sum(1 for m in messages if m["sender"] == "rider")
    driver_count = sum(1 for m in messages if m["sender"] == "driver")
    system_count = sum(1 for m in messages if m["sender"] == "system")

    # Overall sentiment
    user_sentiments = [m["sentiment"] for m in messages if m["sender"] != "system"]
    if not user_sentiments:
        sentiment_summary = "no_messages"
    else:
        neg_count = sum(1 for s in user_sentiments if s in ("negative", "hostile"))
        if neg_count > len(user_sentiments) * 0.5:
            sentiment_summary = "predominantly_negative"
        elif neg_count > 0:
            sentiment_summary = "mixed_with_negativity"
        else:
            sentiment_summary = "neutral_or_positive"

    summary_parts = [
        f"{len(messages)} messages ({rider_count} rider, {driver_count} driver, {system_count} system)",
        f"sentiment: {sentiment_summary}",
        f"{len(threat_messages)} threat(s)",
        f"{len(key_exchanges)} evidence-relevant exchange(s)",
    ]
    if rider_first_msg and driver_first_msg:
        if rider_first_msg <= driver_first_msg:
            summary_parts.append("rider initiated contact first")
        else:
            summary_parts.append("driver initiated contact first")
    if rider_asked_driver and not driver_responded:
        summary_parts.append("WARNING: rider contacted driver but driver did not respond")
    summary = ". ".join(summary_parts) + "."

    return ChatAnalysis(
        trip_id=trip_id,
        messages=messages,
        total_messages=len(messages),
        rider_messages=rider_count,
        driver_messages=driver_count,
        system_messages=system_count,
        sentiment_summary=sentiment_summary,
        threat_detected=len(threat_messages) > 0,
        threat_messages=threat_messages,
        key_exchanges=key_exchanges,
        rider_initiated_contact=rider_first_msg is not None,
        driver_initiated_contact=driver_first_msg is not None,
        driver_responded_to_rider=driver_responded,
        summary=summary,
    )
