"""Inter-agent message model for the shared conversation log."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """A single entry in the shared conversation log between agents."""
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: Literal["rider_advocate", "driver_advocate", "judge", "system"]
    recipient: Literal["rider_advocate", "driver_advocate", "judge", "all"] = "all"
    msg_type: Literal[
        "tool_call", "tool_result", "reasoning",
        "argument", "rebuttal", "ruling", "system",
    ]
    content: str
    metadata: dict = Field(default_factory=dict)


class ConversationLog:
    """Shared, append-only conversation log observable by the UI."""

    def __init__(self, on_message=None):
        self._messages: list[AgentMessage] = []
        self._on_message = on_message  # callback(msg) for real-time UI updates

    def append(self, msg: AgentMessage) -> None:
        self._messages.append(msg)
        if self._on_message:
            self._on_message(msg)

    def log(
        self,
        sender: str,
        msg_type: str,
        content: str,
        recipient: str = "all",
        metadata: dict | None = None,
    ) -> AgentMessage:
        msg = AgentMessage(
            sender=sender,
            recipient=recipient,
            msg_type=msg_type,
            content=content,
            metadata=metadata or {},
        )
        self._messages.append(msg)
        if self._on_message:
            self._on_message(msg)
        return msg

    @property
    def messages(self) -> list[AgentMessage]:
        return list(self._messages)

    def as_dicts(self) -> list[dict]:
        return [m.model_dump() for m in self._messages]

    def __len__(self) -> int:
        return len(self._messages)
