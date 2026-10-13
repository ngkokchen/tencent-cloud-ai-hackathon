"""Ruling model: the Judge's final decision."""

from pydantic import BaseModel, Field

from models.argument import PolicyCitation


class Ruling(BaseModel):
    """The Judge's final ruling on a dispute."""
    ruling: str           # "refund", "compensation", "no_action"
    action: str           # short description, e.g. "Refund $6.38 to rider"
    amount: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0)   # 0.0-1.0
    reasoning_for_rider: str     # natural-language explanation for the rider
    reasoning_for_driver: str    # natural-language explanation for the driver
    policy_applied: list[PolicyCitation] = Field(default_factory=list)

    # Verification info
    tools_called: list[str] = Field(default_factory=list)
    verification_notes: str = ""  # what the judge independently verified
