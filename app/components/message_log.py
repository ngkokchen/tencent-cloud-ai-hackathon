"""Message log component: renders the conversation log as a color-coded timeline."""

import json
import streamlit as st

from models.message import AgentMessage

# Color scheme per agent (dark theme compatible)
AGENT_COLORS = {
    "rider_advocate": {"primary": "#378ADD", "label": "Rider Advocate", "bg": "rgba(55,138,221,0.08)"},
    "driver_advocate": {"primary": "#D85A30", "label": "Driver Advocate", "bg": "rgba(216,90,48,0.08)"},
    "judge": {"primary": "#534AB7", "label": "Judge", "bg": "rgba(83,74,183,0.08)"},
    "system": {"primary": "#888780", "label": "System", "bg": "rgba(136,135,128,0.06)"},
}

MSG_TYPE_ICONS = {
    "tool_call": "TOOL",
    "tool_result": "RESULT",
    "reasoning": "THINK",
    "argument": "ARGUMENT",
    "ruling": "RULING",
    "system": "SYS",
}


def render_single_message(msg: AgentMessage, idx: int) -> None:
    """Render a single agent message as a styled card."""
    colors = AGENT_COLORS.get(msg.sender, AGENT_COLORS["system"])
    icon = MSG_TYPE_ICONS.get(msg.msg_type, msg.msg_type.upper())

    # Truncate long content for display
    content = msg.content
    if len(content) > 3000:
        content = content[:3000] + "\n... [truncated]"

    timestamp_str = msg.timestamp.strftime("%H:%M:%S")

    # Build the message card HTML
    if msg.msg_type == "tool_result":
        # Tool results go in an expander
        tool_name = msg.metadata.get("tool", "unknown")
        label = f"[{timestamp_str}] {colors['label']} — {tool_name} result"
        with st.expander(label, expanded=False):
            st.code(content, language="json")
    elif msg.msg_type in ("argument", "ruling"):
        # Arguments and rulings get highlighted boxes
        st.markdown(
            f"""<div style="border-left: 3px solid {colors['primary']};
            background: {colors['bg']}; padding: 10px 14px; margin: 6px 0;
            border-radius: 0 6px 6px 0;">
            <div style="font-size: 12px; color: {colors['primary']}; font-weight: 500;
            margin-bottom: 4px;">
            {timestamp_str} &middot; {colors['label']} &middot; {icon}
            </div>
            <div style="font-size: 13px; white-space: pre-wrap;
            font-family: monospace; color: inherit;">{content}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    elif msg.msg_type == "reasoning":
        # Reasoning is muted and italic
        st.markdown(
            f"""<div style="padding: 4px 14px; margin: 2px 0;">
            <span style="font-size: 12px; color: {colors['primary']}; font-weight: 500;">
            {timestamp_str} &middot; {colors['label']}</span>
            <span style="font-size: 11px; color: #888; margin-left: 6px;">{icon}</span>
            <div style="font-size: 13px; color: #aaa; font-style: italic;
            margin-top: 2px;">{content}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        # tool_call and system messages — compact
        st.markdown(
            f"""<div style="padding: 4px 14px; margin: 2px 0;">
            <span style="font-size: 12px; color: {colors['primary']}; font-weight: 500;">
            {timestamp_str} &middot; {colors['label']}</span>
            <span style="font-size: 11px; color: #888; margin-left: 6px;
            background: {colors['bg']}; padding: 1px 6px; border-radius: 3px;">{icon}</span>
            <div style="font-size: 13px; color: inherit; margin-top: 2px;
            font-family: monospace;">{content}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_message_log(messages: list, start_idx: int = 0) -> int:
    """
    Render a list of AgentMessage objects as a color-coded timeline.
    Returns the index of the last rendered message.
    """
    for i, msg in enumerate(messages[start_idx:], start=start_idx):
        if isinstance(msg, dict):
            msg = AgentMessage(**msg)
        render_single_message(msg, i)
    return len(messages)


def render_message_log_streaming(log, last_idx: int = 0) -> int:
    """
    Render new messages since last_idx from a ConversationLog.
    Returns the new last_idx.
    """
    messages = log.messages
    for i in range(last_idx, len(messages)):
        render_single_message(messages[i], i)
    return len(messages)
