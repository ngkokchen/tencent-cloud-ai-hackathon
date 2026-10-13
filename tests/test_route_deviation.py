"""Tests for route deviation dispute resolution (demo mode)."""

import pytest

from config.settings import SAMPLES_DIR
from evidence.loaders import load_case_by_file
from graph.orchestrator import run_demo_resolution
from models.argument import Argument, Rebuttal
from models.message import ConversationLog
from models.ruling import Ruling


@pytest.fixture
def clear_case():
    return load_case_by_file(SAMPLES_DIR / "route_deviation_clear.json")

@pytest.fixture
def borderline_case():
    return load_case_by_file(SAMPLES_DIR / "route_deviation_borderline.json")


def test_clear_deviation_finds_rider_at_fault(clear_case):
    """Clear route deviation (>30%) should result in a refund."""
    log = ConversationLog()
    ruling, rider_arg, driver_arg, rider_reb, driver_reb = run_demo_resolution(
        clear_case, log, delay=0
    )

    # Ruling
    assert isinstance(ruling, Ruling)
    assert ruling.ruling == "refund"
    assert ruling.amount == pytest.approx(6.38, abs=0.01)
    assert ruling.confidence >= 0.85
    assert ruling.confidence <= 1.0
    assert len(ruling.policy_applied) >= 1

    # Ruling explanations exist
    assert len(ruling.reasoning_for_rider) > 10
    assert len(ruling.reasoning_for_driver) > 10

    # Rider advocate argues for refund
    assert isinstance(rider_arg, Argument)
    assert rider_arg.agent == "rider_advocate"
    assert rider_arg.requested_remedy == "refund"
    assert rider_arg.requested_amount > 0
    assert len(rider_arg.evidence) >= 2
    assert len(rider_arg.policy_cited) >= 1

    # Driver advocate argues for no action
    assert isinstance(driver_arg, Argument)
    assert driver_arg.agent == "driver_advocate"

    # Rebuttals
    assert isinstance(rider_reb, Rebuttal)
    assert rider_reb.agent == "rider_advocate"
    assert len(rider_reb.counterpoints) >= 1

    assert isinstance(driver_reb, Rebuttal)
    assert driver_reb.agent == "driver_advocate"
    assert len(driver_reb.counterpoints) >= 1


def test_borderline_deviation_traffic_justified_no_refund(borderline_case):
    """Borderline deviation with traffic exception should result in no action."""
    log = ConversationLog()
    ruling, rider_arg, driver_arg, rider_reb, driver_reb = run_demo_resolution(
        borderline_case, log, delay=0
    )

    # Ruling
    assert ruling.ruling == "no_action"
    assert ruling.amount == 0.0
    assert ruling.confidence >= 0.70

    # Driver advocate should cite traffic exception
    assert len(driver_arg.evidence) >= 1
    driver_facts = [e.fact for e in driver_arg.evidence]
    assert any("traffic" in f.lower() or "justified" in f.lower() for f in driver_facts)

    # Rebuttals still produced
    assert len(rider_reb.counterpoints) >= 1
    assert len(driver_reb.counterpoints) >= 1


def test_route_deviation_log_has_all_phases(clear_case):
    """The conversation log should capture all 3 phases."""
    log = ConversationLog()
    run_demo_resolution(clear_case, log, delay=0)

    senders = {m.sender for m in log.messages}
    assert "rider_advocate" in senders
    assert "driver_advocate" in senders
    assert "judge" in senders
    assert "system" in senders

    msg_types = {m.msg_type for m in log.messages}
    assert "argument" in msg_types
    assert "rebuttal" in msg_types
    assert "ruling" in msg_types
    assert "tool_call" in msg_types
    assert "tool_result" in msg_types
    assert "reasoning" in msg_types
