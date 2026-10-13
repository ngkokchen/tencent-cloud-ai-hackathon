"""Argument model: the structured case each advocate produces."""

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """A single piece of evidence cited in an advocate's argument."""
    source: str          # "gps", "chat", "fare", "history", "policy"
    fact: str            # what the evidence shows
    reference: str       # specific data point or tool output field
    supports: str         # "rider" or "driver"


class PolicyCitation(BaseModel):
    """A policy clause cited by an advocate or judge."""
    clause: str           # e.g. "1.3"
    title: str            # e.g. "Deviation Thresholds and Refund Tiers"
    relevance: str        # why this clause applies to this case


class Argument(BaseModel):
    """The structured case produced by an advocate agent."""
    agent: str            # "rider_advocate" or "driver_advocate"
    claim: str            # one-sentence summary of the case
    evidence: list[EvidenceItem] = Field(default_factory=list)
    policy_cited: list[PolicyCitation] = Field(default_factory=list)
    requested_remedy: str        # "refund", "compensation", "no_action"
    requested_amount: float = 0.0
    reasoning: str               # full argument text

    # Track which tools were called
    tools_called: list[str] = Field(default_factory=list)
    tool_reasoning: str = ""     # why these tools were selected
