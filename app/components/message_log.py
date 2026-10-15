"""Message log component: renders the conversation log in a styled container."""

import html as _html
import textwrap

import streamlit as st

from models.message import AgentMessage

# Color scheme per agent
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


def _h(s: str) -> str:
    """Strip leading indentation from HTML strings."""
    return textwrap.dedent(s).strip()


def _should_show(msg: AgentMessage) -> bool:
    """Return True if the message should be shown in the simplified view."""
    if msg.msg_type in ("tool_call", "tool_result"):
        return False
    return True


def _message_html(msg: AgentMessage, idx: int) -> str:
    """Build HTML for a single message. Returns empty string if filtered out."""
    if not _should_show(msg):
        return ""

    colors = AGENT_COLORS.get(msg.sender, AGENT_COLORS["system"])
    content = msg.content
    if len(content) > 3000:
        content = content[:3000] + "\n... [truncated]"

    content = _html.escape(content)
    content = content.replace("\n", "<br>")
    timestamp_str = msg.timestamp.strftime("%H:%M:%S")

    if msg.msg_type in ("argument", "rebuttal"):
        label = "ARGUMENT" if msg.msg_type == "argument" else "REBUTTAL"
        return _h(f"""
            <div style="border-left: 3px solid {colors['primary']};
            background: {colors['bg']}; padding: 12px 16px; margin: 8px 0;
            border-radius: 0 8px 8px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
              <div style="display: flex; justify-content: space-between;
              align-items: center; margin-bottom: 6px;">
                <span style="font-size: 11px; color: {colors['primary']};
                font-weight: 600;">
                  {colors['icon']} {colors['label']}
                  <span style="font-size: 9px; color: #202735;
                  margin-left: 6px; letter-spacing: 0.05em;">
                    {label}
                  </span>
                </span>
                <span style="font-size: 10px; color: #7c8390;
                font-family: monospace;">{timestamp_str}</span>
              </div>
              <div style="font-size: 13px; line-height: 1.6; color: #202735;">
                {content}
              </div>
            </div>
        """)

    elif msg.msg_type == "ruling":
        return _h(f"""
            <div style="padding: 10px 16px; margin: 4px 0;
            border-bottom: 1px solid #f0f1f3;">
              <div style="display: flex; justify-content: space-between;
              align-items: center; margin-bottom: 4px;">
                <span style="font-size: 11px; color: {colors['primary']};
                font-weight: 600;">
                  {colors['icon']} {colors['label']}
                  <span style="font-size: 9px; color: {colors['primary']};
                  margin-left: 6px; background: {colors['bg']};
                  padding: 1px 6px; border-radius: 3px;">
                    RULING
                  </span>
                </span>
                <span style="font-size: 10px; color: #7c8390;
                font-family: monospace;">{timestamp_str}</span>
              </div>
              <div style="font-size: 12px; color: #202735; margin-top: 4px;
              line-height: 1.5;">
                {content}
              </div>
            </div>
        """)

    elif msg.msg_type == "reasoning":
        return _h(f"""
            <div style="padding: 8px 16px; margin: 2px 0;
            border-bottom: 1px solid #f0f1f3;">
              <div style="display: flex; justify-content: space-between;
              align-items: center;">
                <span style="font-size: 11px; color: {colors['primary']};
                font-weight: 500;">
                  {colors['icon']} {colors['label']}
                </span>
                <span style="font-size: 10px; color: #7c8390;
                font-family: monospace;">{timestamp_str}</span>
              </div>
              <div style="font-size: 12px; color: #9a9da3; font-style: italic;
              margin-top: 4px; line-height: 1.5;">
                {content}
              </div>
            </div>
        """)

    else:
        return _h(f"""
            <div style="padding: 8px 16px; margin: 2px 0;
            border-bottom: 1px solid #f0f1f3;">
              <div style="display: flex; justify-content: space-between;
              align-items: center;">
                <span style="font-size: 11px; color: {colors['primary']};
                font-weight: 500;">
                  {colors['icon']} {colors['label']}
                </span>
                <span style="font-size: 10px; color: #7c8390;
                font-family: monospace;">{timestamp_str}</span>
              </div>
              <div style="font-size: 12px; color: #202735; margin-top: 4px;
              line-height: 1.5;">
                {content}
              </div>
            </div>
        """)


def render_conversation_container(messages: list, start_idx: int = 0) -> None:
    """
    Render the conversation inside a styled container card matching Advocate cases design.
    All HTML is built as a single string so Streamlit wraps it in one element.
    """
    parts = []

    # ─── Container with purple-tinted border ───────────
    parts.append(_h("""
        <div style="border: 1px solid rgba(83,74,183,0.18); border-radius: 12px;
        background: white; margin-bottom: 20px; overflow: hidden;">
    """))

    # ─── Header bar ────────────────────────────────────
    parts.append(_h("""
        <div style="background: #f8f7fc; padding: 16px 20px;
        border-bottom: 1px solid rgba(83,74,183,0.12);">
          <div style="display: flex; justify-content: space-between;
          align-items: center;">
            <span style="font-size: 10px; font-weight: 700;
            color: #534AB7; letter-spacing: 0.12em;">
              <span style="margin-right: 4px;">&#128172;</span>AGENT CONVERSATION
            </span>
            <span style="font-size: 9px; color: #534AB7;
            border: 1px solid rgba(83,74,183,0.18);
            border-radius: 4px; padding: 2px 8px;">
              Real-time
            </span>
          </div>
        </div>
    """))

    # ─── Agent legend bar ──────────────────────────────
    parts.append(_h("""
        <div style="padding: 10px 20px; background: #f5f6f8;
        border-bottom: 1px solid #e8ebef; display: flex; gap: 16px;">
          <span style="font-size: 10px; color: #378ADD;">
            <span style="display: inline-block; width: 6px; height: 6px;
            background: #378ADD; border-radius: 50%; margin-right: 4px;"></span>
            Rider Advocate
          </span>
          <span style="font-size: 10px; color: #D85A30;">
            <span style="display: inline-block; width: 6px; height: 6px;
            background: #D85A30; border-radius: 50%; margin-right: 4px;"></span>
            Driver Advocate
          </span>
          <span style="font-size: 10px; color: #534AB7;">
            <span style="display: inline-block; width: 6px; height: 6px;
            background: #534AB7; border-radius: 50%; margin-right: 4px;"></span>
            Judge
          </span>
        </div>
    """))

    # ─── Messages ──────────────────────────────────────
    parts.append("<div style=\"padding: 8px 0;\">")

    visible_count = 0
    for i, msg in enumerate(messages[start_idx:], start=start_idx):
        if isinstance(msg, dict):
            msg = AgentMessage(**msg)
        html = _message_html(msg, i)
        if html:
            parts.append(html)
            visible_count += 1

    parts.append("</div>")

    # ─── Container footer ──────────────────────────────
    parts.append(_h("""
        <div style="padding: 10px 20px; border-top: 1px solid #e8ebef;
        display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 10px; color: #7c8390;">
            <span style="color: #1D9E75; margin-right: 4px;">&#10003;</span>
            Resolution complete
          </span>
          <span style="font-size: 10px; color: #7c8390;">
            3 agents &middot; Demo
          </span>
        </div>
        </div>
    """))

    # Render everything in one st.markdown call
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_single_message(msg: AgentMessage, idx: int) -> None:
    """Render a single agent message as a styled card (standalone use)."""
    html = _message_html(msg, idx)
    if html:
        st.markdown(html, unsafe_allow_html=True)


def render_message_log(messages: list, start_idx: int = 0) -> int:
    """
    Render a list of AgentMessage objects inside a conversation container.
    Returns the index of the last rendered message.
    """
    render_conversation_container(messages, start_idx)
    return len(messages)


def render_message_log_streaming(log, last_idx: int = 0) -> int:
    """
    Render new messages since last_idx from a ConversationLog.
    Returns the new last_idx.
    """
    messages = log.messages
    render_conversation_container(messages, last_idx)
    return len(messages)
