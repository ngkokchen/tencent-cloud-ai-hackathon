"""
LangGraph orchestrator: diamond-shaped multi-agent pipeline with parallel
advocates, a rebuttal phase, and a judge.

Graph topology:
    START → rider_advocate ─┐
          → driver_advocate ─┤
                               ↓
    rider_advocate → rider_rebuttal ─┐
    driver_advocate → driver_rebuttal ─┤
                                       ↓
                                    judge → END

Both advocates run in parallel (Phase 1).  Then each advocate produces a
rebuttal after seeing the other's argument (Phase 2, also parallel).
Finally the Judge weighs everything and issues a ruling (Phase 3).
"""

import json
from typing import Optional

from langgraph.graph import StateGraph, END, START

from agents.driver_advocate import DriverAdvocate
from agents.judge import Judge
from agents.rider_advocate import RiderAdvocate
from evidence.loaders import CaseData
from graph.state import DisputeState
from llm.client import LLMClient
from models.argument import Argument, Rebuttal
from models.message import ConversationLog
from models.ruling import Ruling


# ─── Node functions ─────────────────────────────────────────────────

def _rider_advocate_node(state: DisputeState) -> dict:
    """Phase 1: Rider Advocate gathers evidence and builds an argument."""
    case: CaseData = state["case"]
    llm: LLMClient = state["llm"]
    log: ConversationLog = state["log"]

    log.log("system", "system",
            "Phase 1: Rider Advocate gathering evidence (parallel)...")

    agent = RiderAdvocate(llm, log)
    argument = agent.run(case)
    return {"rider_argument": argument}


def _driver_advocate_node(state: DisputeState) -> dict:
    """Phase 1: Driver Advocate gathers evidence and builds an argument."""
    case: CaseData = state["case"]
    llm: LLMClient = state["llm"]
    log: ConversationLog = state["log"]

    log.log("system", "system",
            "Phase 1: Driver Advocate gathering evidence (parallel)...")

    agent = DriverAdvocate(llm, log)
    argument = agent.run(case)
    return {"driver_argument": argument}


def _rider_rebuttal_node(state: DisputeState) -> dict:
    """Phase 2: Rider Advocate rebuts the Driver Advocate's argument."""
    case: CaseData = state["case"]
    llm: LLMClient = state["llm"]
    log: ConversationLog = state["log"]
    own_arg: Argument = state["rider_argument"]
    opp_arg: Argument = state["driver_argument"]

    log.log("system", "system",
            "Phase 2: Rider Advocate preparing rebuttal...")

    agent = RiderAdvocate(llm, log)
    rebuttal = agent.rebut(case, own_arg, opp_arg)
    return {"rider_rebuttal": rebuttal}


def _driver_rebuttal_node(state: DisputeState) -> dict:
    """Phase 2: Driver Advocate rebuts the Rider Advocate's argument."""
    case: CaseData = state["case"]
    llm: LLMClient = state["llm"]
    log: ConversationLog = state["log"]
    own_arg: Argument = state["driver_argument"]
    opp_arg: Argument = state["rider_argument"]

    log.log("system", "system",
            "Phase 2: Driver Advocate preparing rebuttal...")

    agent = DriverAdvocate(llm, log)
    rebuttal = agent.rebut(case, own_arg, opp_arg)
    return {"driver_rebuttal": rebuttal}


def _judge_node(state: DisputeState) -> dict:
    """Phase 3: Judge reviews both arguments + rebuttals and issues a ruling."""
    case: CaseData = state["case"]
    llm: LLMClient = state["llm"]
    log: ConversationLog = state["log"]
    rider_arg: Argument = state["rider_argument"]
    driver_arg: Argument = state["driver_argument"]
    rider_rebuttal: Optional[Rebuttal] = state.get("rider_rebuttal")
    driver_rebuttal: Optional[Rebuttal] = state.get("driver_rebuttal")

    log.log("system", "system",
            "Phase 3: Judge reviewing both cases and rebuttals...")

    judge = Judge(llm, log)
    ruling = judge.run(case, rider_arg, driver_arg,
                       rider_rebuttal, driver_rebuttal)

    log.log("system", "system",
            f"Resolution complete. Ruling: {ruling.ruling}, "
            f"amount: ${ruling.amount:.2f}, confidence: {ruling.confidence:.2f}")

    return {"ruling": ruling}


# ─── Build the graph ───────────────────────────────────────────────

def build_dispute_graph() -> StateGraph:
    """
    Compile the LangGraph state machine for dispute resolution.

    Returns a compiled graph that can be invoked with:
        graph.invoke({"case": case_data, "llm": llm, "log": log})
    """
    graph = StateGraph(DisputeState)

    # Register nodes
    graph.add_node("rider_advocate", _rider_advocate_node)
    graph.add_node("driver_advocate", _driver_advocate_node)
    graph.add_node("rider_rebuttal", _rider_rebuttal_node)
    graph.add_node("driver_rebuttal", _driver_rebuttal_node)
    graph.add_node("judge", _judge_node)

    # Phase 1: parallel advocates
    graph.add_edge(START, "rider_advocate")
    graph.add_edge(START, "driver_advocate")

    # Phase 2: each advocate rebuts the other's argument
    graph.add_edge("rider_advocate", "rider_rebuttal")
    graph.add_edge("driver_advocate", "driver_rebuttal")

    # Phase 3: both rebuttals feed into the judge
    graph.add_edge("rider_rebuttal", "judge")
    graph.add_edge("driver_rebuttal", "judge")

    # Judge is terminal
    graph.add_edge("judge", END)

    return graph.compile()


# ─── Convenience entry point ────────────────────────────────────────

def run_dispute_resolution(
    case_data: CaseData,
    llm: LLMClient,
    log: ConversationLog,
) -> tuple[Ruling, Argument, Argument, Rebuttal, Rebuttal]:
    """
    Run the full LangGraph pipeline with real LLM calls.

    Returns:
        (ruling, rider_argument, driver_argument,
         rider_rebuttal, driver_rebuttal)
    """
    log.log("system", "system",
            f"Dispute {case_data.dispute.get('dispute_id', 'N/A')} loaded. "
            f"Starting LangGraph multi-agent resolution (3 phases, diamond topology)...")

    app = build_dispute_graph()
    result = app.invoke({
        "case": case_data,
        "llm": llm,
        "log": log,
    })

    ruling = result["ruling"]
    rider_arg = result["rider_argument"]
    driver_arg = result["driver_argument"]
    rider_reb = result.get("rider_rebuttal")
    driver_reb = result.get("driver_rebuttal")

    return ruling, rider_arg, driver_arg, rider_reb, driver_reb
