"""Message log component: renders the conversation log as a color-coded timeline."""

import streamlit as st

from models.message import AgentMessage

# Color scheme per agent (dark theme compatible)
AGENT_COLORS = {
    "rider_advocate": {
        "primary": "#378ADD",
        "label": "Rider Advocate",
        "bg": "rgba(55,138,221,0.08)",
        "icon": "&#128100;",
    },
    "driver_advocate": {
        "primary": "#D85A30",
        "label": "Driver Advocate",
        "bg": "rgba(216,90,48,0.08)",
        "icon": "&#128663;",
    },
    "judge": {
        "primary": "#534AB7",
        "label": "Judge",
        "bg": "rgba(83,74,183,0.08)",
        "icon": "&#9878;",
    },
    "system": {
        "primary": "#888780",
        "label": "System",
        "bg": "rgba(136,135,128,0.06)",
        "icon": "&#9881;",
    },
}

MSG_TYPE_STYLES = {
    "tool_call": ("TOOL", "#f5f6f8", "#7c8390"),
    "tool_result": ("RESULT", "#f5f6f8", "#7c8390"),
    "reasoning": ("THINK", "transparent", "#7c8390"),
    "argument": ("ARGUMENT", "transparent", "#202735"),
    "rebuttal": ("REBUTTAL", "transparent", "#202735"),
    "ruling": ("RULING", "transparent", "#202735"),
    "system": ("SYS", "#f5f6f8", "#7c8390"),
}


def render_single_message(msg: AgentMessage, idx: int) -> None:
    """Render a single agent message as a styled card."""
    colors = AGENT_COLORS.get(msg.sender, AGENT_COLORS["system"])
    type_label, _type_bg, type_text = MSG_TYPE_STYLES.get(
        msg.msg_type, (msg.msg_type.upper(), "transparent", "#7c8390")
    )

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

    elif msg.msg_type in ("argument", "rebuttal", "ruling"):
        # Arguments and rulings get highlighted boxes
        st.markdown(
            f"""<div style="border-left: 3px solid {colors['primary']};
            background: {colors['bg']}; padding: 12px 16px; margin: 8px 0;
            border-radius: 0 8px 8px 0;">
            <div style="display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 6px;">
              <span style="font-size: 11px; color: {colors['primary']};
              font-weight: 600;">
                {colors['icon']} {colors['label']}
                <span style="font-size: 9px; color: {type_text};
                margin-left: 6px; letter-spacing: 0.05em;">
                  {type_label}
                </span>
              </span>
              <span style="font-size: 10px; color: #7c8390;
              font-family: monospace;">{timestamp_str}</span>
            </div>
            <div style="font-size: 13px; line-height: 1.6; color: #202735;">
              {content}
            </div>
            </div>""",
            unsafe_allow_html=True,
        )

    elif msg.msg_type == "reasoning":
        # Reasoning is muted and italic
        st.markdown(
            f"""<div style="padding: 6px 16px; margin: 4px 0;">
            <div style="display: flex; justify-content: space-between;
            align-items: center;">
              <span style="font-size: 11px; color: {colors['primary']};
              font-weight: 500;">
                {colors['icon']} {colors['label']}
                <span style="font-size: 9px; color: #7c8390;
                margin-left: 6px; background: #f5f6f8;
                padding: 1px 6px; border-radius: 3px;">
                  {type_label}
                </span>
              </span>
              <span style="font-size: 10px; color: #7c8390;
              font-family: monospace;">{timestamp_str}</span>
            </div>
            <div style="font-size: 12px; color: #9a9da3; font-style: italic;
            margin-top: 4px; line-height: 1.5;">
              {content}
            </div>
            </div>""",
            unsafe_allow_html=True,
        )

    else:
        # tool_call and system messages — compact
        st.markdown(
            f"""<div style="padding: 6px 16px; margin: 4px 0;">
            <div style="display: flex; justify-content: space-between;
            align-items: center;">
              <span style="font-size: 11px; color: {colors['primary']};
              font-weight: 500;">
                {colors['icon']} {colors['label']}
                <span style="font-size: 9px; color: #7c8390;
                margin-left: 6px; background: #f5f6f8;
                padding: 1px 6px; border-radius: 3px;">
                  {type_label}
                </span>
              </span>
              <span style="font-size: 10px; color: #7c8390;
              font-family: monospace;">{timestamp_str}</span>
            </div>
            <div style="font-size: 12px; color: #202735; margin-top: 4px;
            line-height: 1.5;">
              {content}
            </div>
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
