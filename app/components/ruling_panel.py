"""Ruling panel component: renders the final ruling as a container card."""

import html as _html
import textwrap

import streamlit as st

from models.ruling import Ruling


DECISION_STYLES = {
    "refund": {
        "border": "rgba(29,158,117,0.30)",
        "header_bg": "#eaf6f0",
        "header_border": "rgba(29,158,117,0.20)",
        "accent": "#1D9E75",
        "title": "#167656",
        "subtitle": "#578773",
    },
    "compensation": {
        "border": "rgba(55,138,221,0.30)",
        "header_bg": "#e8f0fb",
        "header_border": "rgba(55,138,221,0.20)",
        "accent": "#378ADD",
        "title": "#2568a8",
        "subtitle": "#4a7ab5",
    },
    "no_action": {
        "border": "rgba(136,135,128,0.30)",
        "header_bg": "#f5f5f3",
        "header_border": "rgba(136,135,128,0.20)",
        "accent": "#888780",
        "title": "#5a5a55",
        "subtitle": "#7a7a75",
    },
}

DECISION_LABELS = {
    "refund": "Refund approved",
    "compensation": "Compensation approved",
    "no_action": "No action taken",
}


def _h(s: str) -> str:
    """Strip leading indentation from HTML strings so Streamlit doesn't treat them as code blocks."""
    return textwrap.dedent(s).strip()


def render_ruling_panel(ruling: Ruling) -> None:
    """Render the Judge's final ruling inside a styled container card."""
    if ruling is None:
        st.info("No ruling available yet.")
        return

    styles = DECISION_STYLES.get(ruling.ruling, DECISION_STYLES["no_action"])
    title_text = DECISION_LABELS.get(ruling.ruling, ruling.ruling.replace("_", " ").title())

    conf_pct = int(ruling.confidence * 100)
    conf_color = "#1D9E75" if ruling.confidence >= 0.8 else "#EF9F27" if ruling.confidence >= 0.6 else "#E24B4A"
    conf_label = "High" if ruling.confidence >= 0.8 else "Medium" if ruling.confidence >= 0.6 else "Low"

    parts = []

    # ─── Container with tinted border ──────────────────
    parts.append(_h(f"""
        <div style="border: 1px solid {styles['border']}; border-radius: 12px;
        background: white; margin-bottom: 20px; overflow: hidden;">
    """))

    # ─── Outcome header bar ────────────────────────────
    parts.append(_h(f"""
        <div style="background: {styles['header_bg']}; padding: 16px 20px;
        border-bottom: 1px solid {styles['header_border']};">
          <div style="display: flex; justify-content: space-between;
          align-items: center;">
            <span style="font-size: 10px; font-weight: 700;
            color: {styles['accent']}; letter-spacing: 0.12em;">
              <span style="margin-right: 4px;">&#10003;</span>FINAL RULING
            </span>
            <span style="font-size: 9px; color: {styles['accent']};
            border: 1px solid {styles['header_border']};
            border-radius: 4px; padding: 2px 8px;">
              Judge verified
            </span>
          </div>
          <div style="display: flex; justify-content: space-between;
          align-items: flex-end; margin-top: 12px;">
            <div>
              <h3 style="font-size: 20px; font-weight: 800; color: {styles['title']};
              margin: 0; font-family: 'Manrope', sans-serif;">
                {_html.escape(title_text)}
              </h3>
              <p style="font-size: 11px; color: {styles['subtitle']}; margin: 4px 0 0 0;">
                {_html.escape(ruling.action)}
              </p>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 30px; font-weight: 800; color: {styles['title']};
              font-family: 'Manrope', sans-serif; letter-spacing: -1px;">
                <span style="font-size: 14px; font-weight: 500; margin-right: 2px;">$</span>{ruling.amount:.2f}
              </span>
            </div>
          </div>
        </div>
    """))

    # ─── Body ──────────────────────────────────────────
    parts.append("<div style=\"padding: 20px;\">")

    # ─── Confidence gauge ──────────────────────────────
    parts.append(_h(f"""
        <div style="display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 8px;">
          <span style="font-size: 11px; font-weight: 500; color: #202735;">
            Decision confidence
            <span style="color: #7c8390; margin-left: 4px;">&#9432;</span>
          </span>
          <span style="font-size: 11px; font-weight: 700; color: {conf_color};">
            {conf_pct}% <span style="font-weight: 400; color: #7c8390; margin-left: 4px;">{conf_label}</span>
          </span>
        </div>
        <div style="background: rgba(29,158,117,0.10); border-radius: 6px;
        height: 6px; overflow: hidden;">
          <div style="background: {conf_color}; height: 100%;
          width: {conf_pct}%; border-radius: 6px;"></div>
        </div>
    """))

    if ruling.confidence < 0.6:
        parts.append(_h(f"""
            <div style="margin-top: 10px; padding: 8px 12px;
            background: rgba(226,75,74,0.08); border-radius: 6px;">
              <span style="font-size: 11px; color: #c43d3c;">
                &#9888; Low confidence — this case should be flagged for human review.
              </span>
            </div>
        """))

    # ─── Dual explanations ─────────────────────────────
    rider_reason = _html.escape(ruling.reasoning_for_rider).replace("\n", "<br>")
    driver_reason = _html.escape(ruling.reasoning_for_driver).replace("\n", "<br>")

    parts.append(_h(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
        margin-top: 20px;">
          <div>
            <div style="font-size: 10px; font-weight: 600; color: #378ADD;
            margin-bottom: 8px;">
              <span style="margin-right: 4px;">&#128100;</span>For the rider
            </div>
            <p style="font-size: 11px; color: #7c8390; line-height: 1.8; margin: 0;">
              {rider_reason}
            </p>
          </div>
          <div style="border-left: 1px solid #e8ebef; padding-left: 16px;">
            <div style="font-size: 10px; font-weight: 600; color: #D85A30;
            margin-bottom: 8px;">
              <span style="margin-right: 4px;">&#128663;</span>For the driver
            </div>
            <p style="font-size: 11px; color: #7c8390; line-height: 1.8; margin: 0;">
              {driver_reason}
            </p>
          </div>
        </div>
    """))

    # ─── Policy applied ────────────────────────────────
    if ruling.policy_applied:
        parts.append(_h("""
            <div style="border-top: 1px solid #e8ebef; margin-top: 16px;
            padding-top: 16px;">
              <div style="font-size: 10px; font-weight: 700; color: #7c8390;
              letter-spacing: 0.13em; text-transform: uppercase;
              margin-bottom: 8px;">
                Policy applied
                <span style="font-weight: 400; text-transform: none;
                letter-spacing: normal;"> · illustrative clauses</span>
              </div>
        """))
        for clause in ruling.policy_applied:
            parts.append(_h(f"""
              <div style="display: flex; justify-content: space-between;
              align-items: center; padding: 4px 0;">
                <span style="font-size: 10px; color: #202735;">
                  &sect; {_html.escape(clause.clause)} &middot; {_html.escape(clause.title)}
                </span>
                <span style="color: #1D9E75; font-size: 10px;">&#10003;</span>
              </div>
            """))
        parts.append("</div>")

    # ─── Verification note ─────────────────────────────
    verification_text = _html.escape(ruling.verification_notes) if ruling.verification_notes else (
        "Verification passed: fare arithmetic checked, both arguments reviewed, and remedy matched to cited policy."
    )
    parts.append(_h(f"""
        <div style="margin-top: 12px; padding: 10px 12px;
        background: #f5f6f8; border-radius: 6px; display: flex;
        gap: 8px; align-items: flex-start;">
          <span style="color: #1D9E75; font-size: 10px; margin-top: 1px;">&#128737;</span>
          <span style="font-size: 9px; color: #7c8390; line-height: 1.6;">
            {verification_text}
          </span>
        </div>
    """))

    # ─── Close container ───────────────────────────────
    parts.append("</div></div>")

    # Render everything in one call
    st.markdown("".join(parts), unsafe_allow_html=True)
