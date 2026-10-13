"""
Orchestrator: runs the full multi-agent dispute resolution pipeline.

Two modes:
  - Live mode: LangGraph state machine with parallel advocates + rebuttal
  - Demo mode: rule-based mock outputs (no LLM needed) for UI demos

Both modes follow the same 3-phase diamond topology:
    Phase 1: Rider Advocate ∥ Driver Advocate (gather evidence, build arguments)
    Phase 2: Rider Rebuttal ∥ Driver Rebuttal (counter the opposing argument)
    Phase 3: Judge (weigh both arguments + rebuttals, issue ruling)
"""

import json
import time
from typing import Callable

from evidence.loaders import CaseData, load_case_by_file
from graph.tools import (
    get_route_analysis, get_chat_log, get_fare_breakdown,
    get_user_history, get_policy,
)
from llm.client import LLMClient
from models.argument import Argument, EvidenceItem, PolicyCitation, Rebuttal
from models.message import ConversationLog
from models.ruling import Ruling


# ─── Live mode (LangGraph) ──────────────────────────────────────────

def run_dispute_resolution(
    case_data: CaseData,
    llm: LLMClient,
    log: ConversationLog,
) -> tuple[Ruling, Argument, Argument, Rebuttal, Rebuttal]:
    """
    Run the full LangGraph pipeline with real LLM calls.
    Uses the diamond-shaped state graph with parallel advocates,
    a rebuttal phase, and a judge.

    Returns (ruling, rider_argument, driver_argument,
             rider_rebuttal, driver_rebuttal).
    """
    from graph.langgraph_orchestrator import run_dispute_resolution as _run
    return _run(case_data, llm, log)


# ─── Demo mode (no LLM needed) ──────────────────────────────────────

def run_demo_resolution(
    case_data: CaseData,
    log: ConversationLog,
    delay: float = 0.4,
) -> tuple[Ruling, Argument, Argument, Rebuttal, Rebuttal]:
    """
    Run with rule-based mock outputs. Calls real tools for evidence
    analysis but generates arguments/rebuttals/rulings without LLM calls.
    Useful for UI demos without an API key.

    Returns (ruling, rider_argument, driver_argument,
             rider_rebuttal, driver_rebuttal).
    """
    trip_id = case_data.trip.get("ride_id", case_data.dispute.get("ride_id", ""))
    rider_id = case_data.rider_profile.get("rider_id", "")
    driver_id = case_data.driver_profile.get("driver_id", "")
    dispute_type = case_data.dispute.get("dispute_type", "")

    log.log("system", "system",
            f"Dispute {case_data.dispute.get('dispute_id', 'N/A')} loaded (demo mode). "
            f"Trip: {trip_id}. Starting resolution...")

    # ── Gather evidence via real tools ────────────────────
    log.log("rider_advocate", "reasoning", "Reviewing dispute and selecting tools...")
    time.sleep(delay)

    tools_to_call = ["get_route_analysis", "get_chat_log", "get_fare_breakdown",
                     "get_user_history", "get_policy"]
    log.log("rider_advocate", "reasoning",
            f"Selected tools: {tools_to_call}. Need all evidence to build rider's case.")
    time.sleep(delay)

    # Execute tools (logged via the tool functions)
    route_result = _demo_call_tool(log, "rider_advocate", "get_route_analysis",
                                   {"trip_id": trip_id}, lambda: get_route_analysis(trip_id))
    chat_result = _demo_call_tool(log, "rider_advocate", "get_chat_log",
                                  {"trip_id": trip_id}, lambda: get_chat_log(trip_id))
    fare_result = _demo_call_tool(log, "rider_advocate", "get_fare_breakdown",
                                  {"trip_id": trip_id}, lambda: get_fare_breakdown(trip_id))
    rider_hist = _demo_call_tool(log, "rider_advocate", "get_user_history",
                                  {"user_id": rider_id}, lambda: get_user_history(rider_id))
    driver_hist = _demo_call_tool(log, "rider_advocate", "get_user_history",
                                  {"user_id": driver_id}, lambda: get_user_history(driver_id))
    policy_result = _demo_call_tool(log, "rider_advocate", "get_policy",
                                    {"dispute_type": dispute_type}, lambda: get_policy(dispute_type))

    # ── Generate rider argument ──────────────────────────
    log.log("rider_advocate", "reasoning", "Analyzing evidence and building argument...")
    time.sleep(delay)
    rider_arg = _build_demo_rider_argument(
        case_data, route_result, chat_result, fare_result,
        rider_hist, driver_hist, policy_result,
    )
    log.log("rider_advocate", "argument",
            json.dumps({"claim": rider_arg.claim, "remedy": rider_arg.requested_remedy,
                        "amount": rider_arg.requested_amount,
                        "evidence_count": len(rider_arg.evidence)},
                       indent=2),
            metadata={"claim": rider_arg.claim, "remedy": rider_arg.requested_remedy,
                      "amount": rider_arg.requested_amount})

    # ── Driver advocate phase ─────────────────────────────
    log.log("driver_advocate", "reasoning", "Reviewing dispute and selecting tools...")
    time.sleep(delay)
    log.log("driver_advocate", "reasoning",
            f"Selected tools: {tools_to_call}. Need all evidence to build driver's case.")
    time.sleep(delay)

    # Re-use same tool results (already gathered)
    for name, result in [("get_route_analysis", route_result),
                         ("get_chat_log", chat_result),
                         ("get_fare_breakdown", fare_result),
                         ("get_user_history(rider)", rider_hist),
                         ("get_user_history(driver)", driver_hist),
                         ("get_policy", policy_result)]:
        log.log("driver_advocate", "tool_call",
                f"{name}(...)", metadata={"tool": name})
        time.sleep(delay * 0.5)
        result_str = json.dumps(result, indent=2, default=str, ensure_ascii=False)
        display = result_str if len(result_str) <= 500 else result_str[:500] + "..."
        log.log("driver_advocate", "tool_result", display,
                metadata={"tool": name, "result_keys": list(result.keys()) if isinstance(result, dict) else []})
        time.sleep(delay * 0.5)

    log.log("driver_advocate", "reasoning", "Analyzing evidence and building argument...")
    time.sleep(delay)
    driver_arg = _build_demo_driver_argument(
        case_data, route_result, chat_result, fare_result,
        rider_hist, driver_hist, policy_result,
    )
    log.log("driver_advocate", "argument",
            json.dumps({"claim": driver_arg.claim, "remedy": driver_arg.requested_remedy,
                        "amount": driver_arg.requested_amount,
                        "evidence_count": len(driver_arg.evidence)},
                       indent=2),
            metadata={"claim": driver_arg.claim, "remedy": driver_arg.requested_remedy,
                      "amount": driver_arg.requested_amount})

    # ── Phase 2: Rebuttal phase (parallel) ───────────────
    log.log("system", "system",
            "Phase 2: Rebuttal phase — advocates respond to each other's arguments...")
    time.sleep(delay)

    log.log("rider_advocate", "reasoning",
            "Reviewing the Driver Advocate's argument for rebuttal...")
    time.sleep(delay)
    rider_rebuttal = _build_demo_rider_rebuttal(
        case_data, rider_arg, driver_arg,
        route_result, chat_result, fare_result)
    log.log("rider_advocate", "rebuttal",
            json.dumps({"counterpoints": rider_rebuttal.counterpoints,
                        "revised_claim": rider_rebuttal.revised_claim},
                       indent=2),
            metadata={"type": "rebuttal",
                      "counterpoints": len(rider_rebuttal.counterpoints)})
    time.sleep(delay)

    log.log("driver_advocate", "reasoning",
            "Reviewing the Rider Advocate's argument for rebuttal...")
    time.sleep(delay)
    driver_rebuttal = _build_demo_driver_rebuttal(
        case_data, rider_arg, driver_arg,
        route_result, chat_result, fare_result)
    log.log("driver_advocate", "rebuttal",
            json.dumps({"counterpoints": driver_rebuttal.counterpoints,
                        "revised_claim": driver_rebuttal.revised_claim},
                       indent=2),
            metadata={"type": "rebuttal",
                      "counterpoints": len(driver_rebuttal.counterpoints)})
    time.sleep(delay)

    # ── Phase 3: Judge phase ──────────────────────────────
    log.log("judge", "reasoning",
            "Reviewing both advocates' arguments and rebuttals...")
    time.sleep(delay)
    verify_tools = ["get_route_analysis", "get_fare_breakdown", "get_policy"]
    log.log("judge", "reasoning",
            f"Selecting verification tools: {verify_tools}. Need to independently verify key claims.")
    time.sleep(delay)

    for name, fn, args in [
        ("get_route_analysis", get_route_analysis, {"trip_id": trip_id}),
        ("get_fare_breakdown", get_fare_breakdown, {"trip_id": trip_id}),
        ("get_policy", get_policy, {"dispute_type": dispute_type}),
    ]:
        log.log("judge", "tool_call", f"{name}(...)", metadata={"tool": name})
        time.sleep(delay * 0.5)
        result = fn(**args)
        result_str = json.dumps(result, indent=2, default=str, ensure_ascii=False)
        display = result_str if len(result_str) <= 500 else result_str[:500] + "..."
        log.log("judge", "tool_result", display,
                metadata={"tool": name, "result_keys": list(result.keys()) if isinstance(result, dict) else []})
        time.sleep(delay * 0.5)

    log.log("judge", "reasoning", "Weighing both cases against evidence and policy...")
    time.sleep(delay)
    ruling = _build_demo_ruling(
        case_data, route_result, chat_result, fare_result,
        rider_hist, driver_hist, policy_result,
        rider_arg, driver_arg,
    )
    log.log("judge", "ruling",
            json.dumps({"ruling": ruling.ruling, "action": ruling.action,
                        "amount": ruling.amount, "confidence": ruling.confidence},
                       indent=2),
            metadata={"ruling": ruling.ruling, "action": ruling.action,
                      "amount": ruling.amount, "confidence": ruling.confidence})

    log.log("system", "system",
            f"Resolution complete. Ruling: {ruling.ruling}, "
            f"amount: ${ruling.amount:.2f}, confidence: {ruling.confidence:.2f}")

    return ruling, rider_arg, driver_arg, rider_rebuttal, driver_rebuttal


def _demo_call_tool(log, agent, tool_name, args, fn):
    """Call a tool and log the call + result (demo mode helper)."""
    log.log(agent, "tool_call", f"{tool_name}({', '.join(f'{k}={v!r}' for k, v in args.items())})",
            metadata={"tool": tool_name, "args": args})
    time.sleep(0.2)
    result = fn()
    result_str = json.dumps(result, indent=2, default=str, ensure_ascii=False)
    display = result_str if len(result_str) <= 500 else result_str[:500] + "..."
    log.log(agent, "tool_result", display,
            metadata={"tool": tool_name, "result_keys": list(result.keys()) if isinstance(result, dict) else []})
    time.sleep(0.2)
    return result


def _build_demo_rider_argument(case, route, chat, fare, rider_hist, driver_hist, policy):
    """Generate a realistic pro-rider argument from tool results."""
    dispute_type = case.dispute.get("dispute_type", "")
    evidence = []
    policy_cited = []

    if dispute_type == "route_deviation":
        dev = route.get("extra_distance_pct", 0)
        cat = route.get("deviation_category", "")
        evidence.append(EvidenceItem(
            source="gps", fact=f"Route deviation: {dev}% ({cat})",
            reference="extra_distance_pct", supports="rider"))
        if not route.get("traffic_exception_applies", False):
            evidence.append(EvidenceItem(
                source="gps", fact="No traffic exception applies — optimal route was clear",
                reference="traffic_exception_applies=False", supports="rider"))
        if not chat.get("driver_responded_to_rider", False):
            evidence.append(EvidenceItem(
                source="chat", fact="Driver did not respond to rider's questions about route",
                reference="driver_responded_to_rider=False", supports="rider"))
        overcharge = fare.get("overcharge_amount", 0)
        evidence.append(EvidenceItem(
            source="fare", fact=f"Fare overcharge: ${overcharge:.2f} vs expected optimal",
            reference="overcharge_amount", supports="rider"))
        if driver_hist.get("risk_indicators"):
            evidence.append(EvidenceItem(
                source="history", fact=f"Driver has {len(driver_hist['risk_indicators'])} risk indicator(s)",
                reference="risk_indicators", supports="rider"))
        policy_cited.append(PolicyCitation(
            clause="1.3", title="Deviation Thresholds and Refund Tiers",
            relevance=f"Deviation of {dev}% falls in '{cat}' category"))
        policy_cited.append(PolicyCitation(
            clause="1.5", title="Communication Requirement",
            relevance="Driver did not communicate the deviation to rider"))
        remedy = "refund"
        amount = overcharge
        claim = f"Driver deviated {dev}% from optimal route, inflating fare by ${overcharge:.2f}"
    else:  # no_show
        wait_min = case.trip.get("driver_wait_time_min", 0)
        rider_dist = case.raw.get("rider_distance_from_pickup_m", 999)
        evidence.append(EvidenceItem(
            source="gps", fact=f"Rider was {rider_dist}m from pickup point",
            reference="rider_distance_from_pickup_m", supports="rider"))
        evidence.append(EvidenceItem(
            source="gps", fact=f"Driver waited only {wait_min} minutes",
            reference="driver_wait_time_min", supports="rider"))
        if not chat.get("driver_responded_to_rider", False):
            evidence.append(EvidenceItem(
                source="chat", fact="Driver did not respond to rider's messages",
                reference="driver_responded_to_rider=False", supports="rider"))
        evidence.append(EvidenceItem(
            source="fare", fact=f"No-show fee of ${fare.get('cancellation_fee', 0):.2f} charged",
            reference="cancellation_fee", supports="rider"))
        policy_cited.append(PolicyCitation(
            clause="2.5", title="Early Departure Rule",
            relevance=f"Driver left after {wait_min} min, below 5-min minimum"))
        policy_cited.append(PolicyCitation(
            clause="2.8", title="Disputed No-Show — Rider Present",
            relevance=f"Rider was {rider_dist}m from pickup"))
        remedy = "refund"
        amount = fare.get("cancellation_fee", 5.0)
        claim = f"Driver left after only {wait_min} min — rider was at pickup, fee should be refunded"

    return Argument(
        agent="rider_advocate", claim=claim, evidence=evidence,
        policy_cited=policy_cited, requested_remedy=remedy,
        requested_amount=amount,
        reasoning=f"Based on {len(evidence)} pieces of evidence, the rider's claim is supported. "
                  f"Policy sections {', '.join(p.clause for p in policy_cited)} apply.",
        tools_called=["get_route_analysis", "get_chat_log", "get_fare_breakdown",
                      "get_user_history", "get_policy"],
    )


def _build_demo_driver_argument(case, route, chat, fare, rider_hist, driver_hist, policy):
    """Generate a realistic pro-driver argument from tool results."""
    dispute_type = case.dispute.get("dispute_type", "")
    evidence = []
    policy_cited = []

    if dispute_type == "route_deviation":
        dev = route.get("extra_distance_pct", 0)
        cat = route.get("deviation_category", "")
        if route.get("traffic_exception_applies", False):
            evidence.append(EvidenceItem(
                source="gps", fact="Traffic exception applies — optimal route was heavily congested",
                reference="traffic_exception_applies=True", supports="driver"))
            policy_cited.append(PolicyCitation(
                clause="1.4", title="Traffic Exception",
                relevance="Optimal route avg speed < 20 km/h, deviation < 15%"))
        if chat.get("driver_initiated_contact", False):
            evidence.append(EvidenceItem(
                source="chat", fact="Driver proactively communicated the route change",
                reference="driver_initiated_contact=True", supports="driver"))
        evidence.append(EvidenceItem(
            source="fare", fact=f"Overcharge is only ${fare.get('overcharge_amount', 0):.2f} — minimal impact",
            reference="overcharge_amount", supports="driver"))
        evidence.append(EvidenceItem(
            source="history", fact=f"Driver has {driver_hist.get('total_rides', 0)} rides, rating {driver_hist.get('rating', 0)}/5.0",
            reference="rating", supports="driver"))
        if cat in ("within_tolerance", "traffic_justified"):
            remedy = "no_action"
            amount = 0.0
            policy_cited.append(PolicyCitation(
                clause="1.3", title="Deviation Thresholds",
                relevance=f"Deviation of {dev}% is within tolerance or traffic-justified"))
        else:
            remedy = "no_action"
            amount = 0.0
            policy_cited.append(PolicyCitation(
                clause="1.6", title="Driver Defense",
                relevance="Driver acted in good faith to avoid traffic"))
        claim = f"Driver's route choice was justified — deviation was {dev}%, within acceptable limits"
    else:  # no_show
        wait_min = case.trip.get("driver_wait_time_min", 0)
        rider_dist = case.raw.get("rider_distance_from_pickup_m", 999)
        if wait_min >= 5:
            evidence.append(EvidenceItem(
                source="gps", fact=f"Driver waited {wait_min} minutes (exceeds 5-min requirement)",
                reference="driver_wait_time_min", supports="driver"))
        if chat.get("driver_initiated_contact", False):
            evidence.append(EvidenceItem(
                source="chat", fact="Driver attempted to contact rider via chat",
                reference="driver_initiated_contact=True", supports="driver"))
        if rider_dist > 50:
            evidence.append(EvidenceItem(
                source="gps", fact=f"Rider was {rider_dist}m from pickup (> 50m threshold)",
                reference="rider_distance_from_pickup_m", supports="driver"))
        if rider_hist.get("recurring_pattern", False):
            evidence.append(EvidenceItem(
                source="history", fact=f"Rider has {rider_hist.get('recent_dispute_count', 0)} no-shows in 90 days (recurring pattern)",
                reference="recurring_pattern=True", supports="driver"))
        evidence.append(EvidenceItem(
            source="history", fact=f"Driver has {driver_hist.get('total_rides', 0)} rides, rating {driver_hist.get('rating', 0)}/5.0",
            reference="rating", supports="driver"))
        policy_cited.append(PolicyCitation(
            clause="2.3", title="Driver Wait Time Requirement",
            relevance=f"Driver waited {wait_min} minutes"))
        policy_cited.append(PolicyCitation(
            clause="2.7", title="Genuine No-Show",
            relevance="All conditions for genuine no-show met"))
        remedy = "no_action"
        amount = 0.0
        claim = f"Driver followed all protocols — waited {wait_min} min, contacted rider, no-show fee is valid"

    return Argument(
        agent="driver_advocate", claim=claim, evidence=evidence,
        policy_cited=policy_cited, requested_remedy=remedy,
        requested_amount=amount,
        reasoning=f"Based on {len(evidence)} pieces of evidence, the driver acted appropriately. "
                  f"Policy sections {', '.join(p.clause for p in policy_cited)} support the driver.",
        tools_called=["get_route_analysis", "get_chat_log", "get_fare_breakdown",
                      "get_user_history", "get_policy"],
    )


def _build_demo_ruling(case, route, chat, fare, rider_hist, driver_hist,
                        policy, rider_arg, driver_arg):
    """Generate a realistic ruling from evidence and both arguments."""
    dispute_type = case.dispute.get("dispute_type", "")
    policy_applied = []

    if dispute_type == "route_deviation":
        dev = route.get("extra_distance_pct", 0)
        cat = route.get("deviation_category", "")
        traffic = route.get("traffic_exception_applies", False)

        if cat == "traffic_justified" or cat == "within_tolerance":
            ruling = "no_action"
            amount = 0.0
            action = "No refund — route deviation was justified"
            confidence = 0.78 if cat == "traffic_justified" else 0.85
            policy_applied.append(PolicyCitation(
                clause="1.3", title="Deviation Thresholds",
                relevance=f"Deviation {dev}% within tolerance or traffic-justified"))
            if traffic:
                policy_applied.append(PolicyCitation(
                    clause="1.4", title="Traffic Exception",
                    relevance="Optimal route avg speed < 20 km/h, all exception conditions met"))
        else:
            ruling = "refund"
            amount = fare.get("overcharge_amount", 0)
            action = f"Refund ${amount:.2f} to rider"
            confidence = 0.92 if dev > 30 else 0.82
            policy_applied.append(PolicyCitation(
                clause="1.3", title="Deviation Thresholds",
                relevance=f"Deviation of {dev}% exceeds threshold"))
            if not chat.get("driver_responded_to_rider", False):
                policy_applied.append(PolicyCitation(
                    clause="1.5", title="Communication Requirement",
                    relevance="Driver did not communicate deviation to rider"))

        rider_reason = (
            f"Your dispute has been reviewed. The GPS data shows a {dev}% route deviation "
            f"(category: {cat}). "
        )
        if ruling == "refund":
            rider_reason += f"You will receive a refund of ${amount:.2f}."
        else:
            rider_reason += "However, the deviation was justified by traffic conditions. No refund is due."

        driver_reason = (
            f"Section 1.3 applies: deviation of {dev}% (category: {cat}). "
        )
        if ruling == "refund":
            driver_reason += f"Refund of ${amount:.2f} issued to rider."
            if not chat.get("driver_responded_to_rider", False):
                driver_reason += " Section 1.5: you did not communicate the deviation to the rider."
        else:
            driver_reason += "Section 1.4 traffic exception applies. No refund required."

    else:  # no_show
        wait_min = case.trip.get("driver_wait_time_min", 0)
        rider_dist = case.raw.get("rider_distance_from_pickup_m", 999)

        if wait_min < 5 or rider_dist <= 50:
            ruling = "refund"
            amount = fare.get("cancellation_fee", 5.0)
            action = f"Refund ${amount:.2f} no-show fee to rider"
            confidence = 0.93
            if wait_min < 5:
                policy_applied.append(PolicyCitation(
                    clause="2.5", title="Early Departure Rule",
                    relevance=f"Driver left after {wait_min} min, below 5-min minimum"))
            if rider_dist <= 50:
                policy_applied.append(PolicyCitation(
                    clause="2.8", title="Disputed No-Show — Rider Present",
                    relevance=f"Rider was {rider_dist}m from pickup (< 50m)"))
        else:
            ruling = "no_action"
            amount = 0.0
            action = "No-show fee upheld — driver followed protocol"
            confidence = 0.90
            policy_applied.append(PolicyCitation(
                clause="2.7", title="Genuine No-Show",
                relevance="Driver waited >= 5 min, attempted contact, rider > 50m away"))
            if rider_hist.get("recurring_pattern", False):
                policy_applied.append(PolicyCitation(
                    clause="2.9", title="Recurring No-Show Pattern",
                    relevance=f"Rider has {rider_hist.get('recent_dispute_count', 0)} no-shows in 90 days"))

        rider_reason = (
            f"Your no-show dispute has been reviewed. "
            f"The driver waited {wait_min} minutes, and you were {rider_dist}m from the pickup point. "
        )
        if ruling == "refund":
            rider_reason += f"The no-show fee of ${amount:.2f} will be refunded to you."
        else:
            rider_reason += "The no-show fee is upheld as the driver followed all required protocols."

        driver_reason = (
            f"Section 2.3 reviewed: you waited {wait_min} minutes. "
        )
        if ruling == "refund":
            driver_reason += f"However, the fee is voided (${amount:.2f} refunded to rider)."
            if wait_min < 5:
                driver_reason += " Section 2.5: you left before the 5-minute minimum."
        else:
            driver_reason += "Section 2.7: all genuine no-show conditions met. Fee upheld."
            if rider_hist.get("recurring_pattern", False):
                driver_reason += " Section 2.9: rider has recurring no-show pattern."

    return Ruling(
        ruling=ruling, action=action, amount=amount, confidence=confidence,
        reasoning_for_rider=rider_reason,
        reasoning_for_driver=driver_reason,
        policy_applied=policy_applied,
        tools_called=["get_route_analysis", "get_fare_breakdown", "get_policy"],
        verification_notes="Independently verified GPS deviation, fare calculation, and policy applicability.",
    )


# ─── Demo rebuttal generators ──────────────────────────────────────

def _build_demo_rider_rebuttal(case, rider_arg, driver_arg, route, chat, fare):
    """Generate a realistic pro-rider rebuttal from the driver's argument."""
    dispute_type = case.dispute.get("dispute_type", "")
    counterpoints = []

    if dispute_type == "route_deviation":
        if route.get("traffic_exception_applies", False):
            counterpoints.append(
                "Driver cites traffic, but GPS data shows the optimal route had "
                "light congestion — the detour was unnecessary."
            )
        else:
            counterpoints.append(
                "Driver's claim of acceptable deviation is false — "
                f"{route.get('extra_distance_pct', 0)}% exceeds all tolerance thresholds."
            )
        if not chat.get("driver_responded_to_rider", False):
            counterpoints.append(
                "Driver claims good communication, but chat logs show "
                "they never responded to the rider's route questions (Section 1.5)."
            )
        overcharge = fare.get("overcharge_amount", 0)
        counterpoints.append(
            f"Fare impact is not minimal — ${overcharge:.2f} overcharge "
            "directly resulted from the unauthorized deviation."
        )
        revised_claim = rider_arg.claim
        revised_remedy = rider_arg.requested_remedy
        revised_amount = rider_arg.requested_amount
    else:  # no_show
        wait_min = case.trip.get("driver_wait_time_min", 0)
        rider_dist = case.raw.get("rider_distance_from_pickup_m", 999)
        if wait_min < 5:
            counterpoints.append(
                f"Driver waited only {wait_min} minutes — Section 2.5 requires "
                "a minimum 5-minute wait before leaving."
            )
        if rider_dist <= 50:
            counterpoints.append(
                f"Rider was {rider_dist}m from pickup — within the 50m radius. "
                "This was not a genuine no-show (Section 2.8)."
            )
        if not chat.get("driver_responded_to_rider", False):
            counterpoints.append(
                "Driver did not respond to rider's messages — "
                "contact was not genuinely attempted."
            )
        revised_claim = rider_arg.claim
        revised_remedy = rider_arg.requested_remedy
        revised_amount = rider_arg.requested_amount

    return Rebuttal(
        agent="rider_advocate",
        counterpoints=counterpoints,
        revised_claim=revised_claim,
        revised_remedy=revised_remedy,
        revised_amount=revised_amount,
        reasoning=f"After reviewing the driver's argument, {len(counterpoints)} "
                  "key counterpoints undermine their position. The original "
                  "remedy stands.",
    )


def _build_demo_driver_rebuttal(case, rider_arg, driver_arg, route, chat, fare):
    """Generate a realistic pro-driver rebuttal from the rider's argument."""
    dispute_type = case.dispute.get("dispute_type", "")
    counterpoints = []

    if dispute_type == "route_deviation":
        if route.get("traffic_exception_applies", False):
            counterpoints.append(
                "Rider cites deviation percentage, but Section 1.4 traffic "
                "exception applies — the optimal route was heavily congested."
            )
        else:
            dev = route.get("extra_distance_pct", 0)
            if dev <= 15:
                counterpoints.append(
                    f"Rider exaggerates the impact — {dev}% deviation is within "
                    "the minor tolerance band (Section 1.3)."
                )
            else:
                counterpoints.append(
                    "Rider focuses on deviation but ignores that the driver "
                    "acted in good faith (Section 1.6)."
                )
        if chat.get("driver_initiated_contact", False):
            counterpoints.append(
                "Driver proactively communicated with the rider — "
                "the rider was informed of the route change."
            )
        counterpoints.append(
            "Driver has a strong record with no prior route deviation "
            "complaints — this was an isolated incident."
        )
        revised_claim = driver_arg.claim
        revised_remedy = driver_arg.requested_remedy
        revised_amount = driver_arg.requested_amount
    else:  # no_show
        wait_min = case.trip.get("driver_wait_time_min", 0)
        rider_dist = case.raw.get("rider_distance_from_pickup_m", 999)
        if wait_min >= 5:
            counterpoints.append(
                f"Driver waited {wait_min} minutes — exceeding the 5-minute "
                "requirement (Section 2.3). The no-show fee is valid."
            )
        if rider_dist > 50:
            counterpoints.append(
                f"Rider was {rider_dist}m from pickup — well beyond the 50m "
                "radius. This qualifies as a genuine no-show (Section 2.7)."
            )
        if chat.get("driver_initiated_contact", False):
            counterpoints.append(
                "Driver attempted to contact the rider via chat — "
                "all contact requirements were met."
            )
        revised_claim = driver_arg.claim
        revised_remedy = driver_arg.requested_remedy
        revised_amount = driver_arg.requested_amount

    return Rebuttal(
        agent="driver_advocate",
        counterpoints=counterpoints,
        revised_claim=revised_claim,
        revised_remedy=revised_remedy,
        revised_amount=revised_amount,
        reasoning=f"After reviewing the rider's argument, {len(counterpoints)} "
                  "key counterpoints support the driver. The original "
                  "remedy stands.",
    )
