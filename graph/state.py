"""
LangGraph state schema for the dispute resolution pipeline.

Defines the diamond-shaped state graph:
    START → [rider_advocate ∥ driver_advocate]
          → [rider_rebuttal ∥ driver_rebuttal]
          → judge → END
"""

from __future__ import annotations

from typing import Optional, TypedDict

from evidence.loaders import CaseData
from llm.client import LLMClient
from models.argument import Argument, Rebuttal
from models.message import ConversationLog
from models.ruling import Ruling


class DisputeState(TypedDict, total=False):
    """Shared state passed through the LangGraph pipeline."""

    # Inputs
    case: CaseData
    llm: LLMClient
    log: ConversationLog

    # Phase 1 outputs (parallel advocates)
    rider_argument: Argument
    driver_argument: Argument

    # Phase 2 outputs (parallel rebuttals)
    rider_rebuttal: Rebuttal
    driver_rebuttal: Rebuttal

    # Phase 3 output
    ruling: Ruling
