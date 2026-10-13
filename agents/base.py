"""Base agent class: shared logic for tool calling, LLM interaction, and message logging."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from graph.tools import TOOL_REGISTRY, TOOL_DESCRIPTIONS
from llm.client import LLMClient
from models.message import ConversationLog


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a system prompt from agents/prompts/<name>.md."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


class BaseAgent:
    """
    Base class for all agents (Rider Advocate, Driver Advocate, Judge).

    Provides:
      - Tool calling with automatic logging to the shared conversation log
      - LLM interaction with JSON response parsing
      - Message logging for full observability
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: LLMClient,
        log: ConversationLog,
        tools: dict[str, Callable] | None = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm
        self.log = log
        self.tools = tools if tools is not None else TOOL_REGISTRY

    # ─── Logging ───────────────────────────────────────────────

    def _log(
        self,
        msg_type: str,
        content: str,
        recipient: str = "all",
        metadata: dict | None = None,
    ) -> None:
        """Append a message to the shared conversation log."""
        self.log.log(
            sender=self.name,
            msg_type=msg_type,
            content=content,
            recipient=recipient,
            metadata=metadata or {},
        )

    # ─── Tool calling ──────────────────────────────────────────

    def call_tool(self, tool_name: str, **kwargs) -> dict:
        """
        Call a registered tool by name. The call and its result are both
        logged to the conversation log for observability.
        """
        if tool_name not in self.tools:
            result = {"error": f"Unknown tool '{tool_name}'"}
            self._log(
                "tool_call",
                f"Attempted to call unknown tool '{tool_name}'",
                metadata={"tool": tool_name, "args": kwargs, "error": True},
            )
            return result

        tool_fn = self.tools[tool_name]

        # Log the call
        self._log(
            "tool_call",
            f"{tool_name}({', '.join(f'{k}={v!r}' for k, v in kwargs.items())})",
            metadata={"tool": tool_name, "args": kwargs},
        )

        # Execute
        result = tool_fn(**kwargs)

        # Log the result (truncated for readability)
        result_str = json.dumps(result, indent=2, default=str, ensure_ascii=False)
        display = result_str if len(result_str) <= 2000 else result_str[:2000] + "\n... [truncated]"
        self._log(
            "tool_result",
            display,
            metadata={
                "tool": tool_name,
                "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            },
        )

        return result

    # ─── LLM interaction ───────────────────────────────────────

    def llm_decide_tools(
        self,
        dispute_summary: str,
        available_tools: dict[str, str] | None = None,
    ) -> list[str]:
        """
        Ask the LLM which tools to call given the dispute context.
        Returns a list of tool names.
        """
        tool_descs = available_tools or TOOL_DESCRIPTIONS
        tools_text = "\n".join(
            f"- {name}: {desc}" for name, desc in tool_descs.items()
        )

        user_msg = (
            f"## Dispute\n{dispute_summary}\n\n"
            f"## Available tools\n{tools_text}\n\n"
            f"Decide which tools to call to build your case. "
            f"Respond as JSON: {{\"tools_to_call\": [\"tool1\", \"tool2\"], "
            f"\"reasoning\": \"why you chose these tools\"}}"
        )

        self._log("reasoning", "Deciding which tools to call...")
        result = self.llm.chat_json(self.system_prompt, user_msg, temperature=0.2)
        tools = result.get("tools_to_call", [])
        reasoning = result.get("reasoning", "")

        self._log(
            "reasoning",
            f"Selected tools: {tools}. Reason: {reasoning}",
            metadata={"selected_tools": tools},
        )

        return tools

    def llm_analyze(
        self,
        user_message: str,
        temperature: float = 0.3,
    ) -> dict:
        """
        Send analysis prompt to LLM and get structured JSON back.
        The system prompt defines the expected output schema.
        """
        self._log("reasoning", "Analyzing evidence and building argument...")
        result = self.llm.chat_json(self.system_prompt, user_message, temperature=temperature)

        preview = json.dumps(result, indent=2, ensure_ascii=False)
        display = preview if len(preview) <= 1500 else preview[:1500] + "\n... [truncated]"
        self._log("reasoning", display)

        return result

    # ─── Helper ────────────────────────────────────────────────

    def _format_tool_results(self, results: dict[str, dict]) -> str:
        """Format tool call results into a readable text block for the LLM."""
        lines = []
        for tool_name, result in results.items():
            lines.append(f"### {tool_name} result:")
            lines.append("```json")
            lines.append(json.dumps(result, indent=2, default=str, ensure_ascii=False))
            lines.append("```")
            lines.append("")
        return "\n".join(lines)
