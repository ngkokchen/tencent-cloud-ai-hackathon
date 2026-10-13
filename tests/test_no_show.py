"""Tests for no-show dispute resolution (demo mode)."""

import pytest

from config.settings import SAMPLES_DIR
from evidence.loaders import load_case_by_file
from graph.orchestrator import run_demo_resolution
from models.argument import Argument, Rebuttal
from models.message import ConversationLog
from models.ruling import Ruling


@pytest.fixture
def genuine_case():
    return load_case_by_file(SAMPLES_DIR / "no_show_genuine.json")

@pytest.fixture
def disputed_case():
    return load_case_by_file(SAMPLES_DIR / "no_show_disputed.json")


def test_genuine_no_show_fee_upheld(genuine_case):
    """Genuine no-show (driver waited >=5 min, rider far away) should uphold fee."""
    log = ConversationLog()
    ruling, rider_arg, driver_arg, rider_reb, driver_reb = run_demo_resolution(
        genuine_case, log, delay=0
    )

    # Ruling
    assert isinstance(ruling, Ruling)
    assert ruling.ruling == "no_action"
    assert ruling.amount == 0.0
    assert ruling.confidence >= 0.85

    # Driver advocate argues fee is valid
    assert isinstance(driver_arg, Argument)
    assert driver_arg.agent == "driver_advocate"
    assert driver_arg.requested_remedy == "no_action"

    # Driver should have evidence about wait time
    driver_facts = [e.fact for e in driver_arg.evidence]
    assert any("waited" in f.lower() or "wait" in f.lower() for f in driver_facts)

    # Rebuttals
    assert isinstance(rider_reb, Rebuttal)
    assert isinstance(driver_reb, Rebuttal)
    assert len(rider_reb.counterpoints) >= 1
    assert len(driver_reb.counterpoints) >= 1


def test_disputed_no_show_rider_present_refund(disputed_case):
    """Disputed no-show (driver left early, rider present) should refund."""
    log = ConversationLog()
    ruling, rider_arg, driver_arg, rider_reb, driver_reb = run_demo_resolution(
        disputed_case, log, delay=0
    )

    # Ruling
    assert isinstance(ruling, Ruling)
    assert ruling.ruling == "refund"
    assert ruling.amount == pytest.approx(5.00, abs=0.01)
    assert ruling.confidence >= 0.90

    # Should cite early departure rule
    policy_clauses = [p.clause for p in ruling.policy_applied]
    assert "2.5" in policy_clauses  # Early Departure Rule

    # Rider advocate argues for refund
    assert isinstance(rider_arg, Argument)
    assert rider_arg.agent == "rider_advocate"
    assert rider_arg.requested_remedy == "refund"
    assert rider_arg.requested_amount > 0

    # Rebuttals
    assert isinstance(rider_reb, Rebuttal)
    assert isinstance(driver_reb, Rebuttal)
    assert len(rider_reb.counterpoints) >= 1
    assert len(driver_reb.counterpoints) >= 1


def test_no_show_log_has_all_phases(disputed_case):
    """The conversation log should capture all 3 phases for no-show too."""
    log = ConversationLog()
    run_demo_resolution(disputed_case, log, delay=0)

    senders = {m.sender for m in log.messages}
    assert "rider_advocate" in senders
    assert "driver_advocate" in senders
    assert "judge" in senders
    assert "system" in senders

    msg_types = {m.msg_type for m in log.messages}
    assert "argument" in msg_types
    assert "rebuttal" in msg_types
    assert "ruling" in msg_types
