"""Tests for the inter-agent conversation log (message logging)."""

import pytest

from config.settings import SAMPLES_DIR
from evidence.loaders import load_case_by_file
from graph.orchestrator import run_demo_resolution
from models.message import AgentMessage, ConversationLog


@pytest.fixture
def case():
    return load_case_by_file(SAMPLES_DIR / "route_deviation_clear.json")


def test_log_starts_empty():
    log = ConversationLog()
    assert len(log) == 0
    assert log.messages == []


def test_log_appends_messages(case):
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    assert len(log) > 0
    assert len(log.messages) == len(log)  # messages property returns a copy

    # Every entry should be an AgentMessage
    for msg in log.messages:
        assert isinstance(msg, AgentMessage)


def test_log_has_all_senders(case):
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    senders = {m.sender for m in log.messages}
    assert senders == {"rider_advocate", "driver_advocate", "judge", "system"}


def test_log_has_all_msg_types(case):
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    types = {m.msg_type for m in log.messages}
    expected_types = {"system", "reasoning", "tool_call", "tool_result",
                      "argument", "rebuttal", "ruling"}
    assert expected_types.issubset(types)


def test_log_chronological_order(case):
    """Messages should be in chronological (append) order."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    timestamps = [m.timestamp for m in log.messages]
    assert timestamps == sorted(timestamps)


def test_first_message_is_system(case):
    """First message should be a system message about loading the dispute."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    first = log.messages[0]
    assert first.sender == "system"
    assert first.msg_type == "system"
    assert "loaded" in first.content.lower() or "dispute" in first.content.lower()


def test_last_message_is_system_completion(case):
    """Last message should be a system message about resolution completion."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    last = log.messages[-1]
    assert last.sender == "system"
    assert last.msg_type == "system"
    assert "complete" in last.content.lower() or "ruling" in last.content.lower()


def test_ruling_message_exists(case):
    """There should be exactly one ruling message from the judge."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    rulings = [m for m in log.messages if m.msg_type == "ruling"]
    assert len(rulings) == 1
    assert rulings[0].sender == "judge"


def test_argument_messages_exist(case):
    """Both advocates should produce an argument message."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    args = [m for m in log.messages if m.msg_type == "argument"]
    arg_senders = {m.sender for m in args}
    assert "rider_advocate" in arg_senders
    assert "driver_advocate" in arg_senders


def test_rebuttal_messages_exist(case):
    """Both advocates should produce a rebuttal message."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    rebs = [m for m in log.messages if m.msg_type == "rebuttal"]
    reb_senders = {m.sender for m in rebs}
    assert "rider_advocate" in reb_senders
    assert "driver_advocate" in reb_senders


def test_tool_calls_have_metadata(case):
    """Tool call messages should include tool name in metadata."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    tool_calls = [m for m in log.messages if m.msg_type == "tool_call"]
    assert len(tool_calls) > 0
    for tc in tool_calls:
        assert "tool" in tc.metadata


def test_as_dicts_returns_serializable(case):
    """as_dicts should return a list of dicts suitable for JSON serialization."""
    log = ConversationLog()
    run_demo_resolution(case, log, delay=0)

    dicts = log.as_dicts()
    assert len(dicts) == len(log)
    for d in dicts:
        assert isinstance(d, dict)
        assert "sender" in d
        assert "msg_type" in d
        assert "content" in d
