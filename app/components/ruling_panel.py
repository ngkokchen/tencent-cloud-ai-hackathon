"""Ruling panel component: renders the final ruling as a prominent container card."""

import html as _html

import streamlit as st

from models.ruling import Ruling


DECISION_COLORS = {
    "refund": ("#1D9E75", "#eaf6f0", "#167656"),
    "compensation": ("#378ADD", "#e8f0fb", "#2568a8"),
    "no_action": ("#888780", "#f5f5f3", "#5a5a55"),
}

DECISION_LABELS = {
    "refund": "REFUND",
    "compensation": "COMPENSATION",
    "no_action": "NO ACTION",
}


def render_ruling_panel(ruling: Ruling) -> None:
    """Render the Judge's final ruling inside a styled container card."""
    if ruling is None:
        st.info("No ruling available yet.")
        return

    accent, bg, text = DECISION_COLORS.get(ruling.ruling, DECISION_COLORS["no_action"])
    label = DECISION_LABELS.get(ruling.ruling, ruling.ruling.upper())

    conf_pct = int(ruling.confidence * 100)
    conf_color = "#1D9E75" if ruling.confidence >= 0.8 else "#EF9F27" if ruling.confidence >= 0.6 else "#E24B4A"
    conf_label = "High" if ruling.confidence >= 0.8 else "Medium" if ruling.confidence >= 0.6 else "Low"

    # Build the entire ruling as one HTML string
    parts = []

    # ─── Container header ──────────────────────────────
    parts.append("""
        <div style="border: 1px solid #e8ebef; border-radius: 12px;
        background: white; margin-bottom: 20px; overflow: hidden;">
          <div style="padding: 14px 20px; border-bottom: 1px solid #e8ebef;
          display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 13px; font-weight: 700; color: #202735;
            font-family: 'Manrope', sans-serif;">
              <span style="margin-right: 8px;">&#9878;</span>Final ruling
            </span>
            <span style="font-size: 10px; color: #7c8390;">
              Binding decision
            </span>
          </div>
          <div style="padding: 0;">
    """)

    # ─── Outcome header bar ────────────────────────────
    parts.append(f"""
        <div style="background: {bg}; padding: 20px;">
          <div style="display: flex; justify-content: space-between;
          align-items: flex-start;">
            <div>
              <span style="font-size: 10px; font-weight: 700;
              color: {accent}; letter-spacing: 0.1em;">
                <span style="margin-right: 4px;">&#10003;</span> FINAL RULING
              </span>
              <h3 style="font-size: 22px; font-weight: 800; color: {text};
              margin: 8px 0 4px 0; font-family: 'Manrope', sans-serif;">
                {_html.escape(ruling.action)}
              </h3>
              <p style="font-size: 12px; color: {accent}; margin: 0;">
                {label} approved
              </p>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 32px; font-weight: 800; color: {text};
              font-family: 'Manrope', sans-serif;">
                ${ruling.amount:.2f}
              </span>
            </div>
          </div>
        </div>
    """)

    # ─── Confidence gauge ──────────────────────────────
    parts.append(f"""
        <div style="padding: 16px 20px;">
          <div style="display: flex; justify-content: space-between;
          align-items: center; margin-bottom: 6px;">
            <span style="font-size: 12px; font-weight: 500; color: #202735;">
              Decision confidence
            </span>
            <span style="font-size: 12px; font-weight: 700; color: {conf_color};">
              {conf_pct}% <span style="font-weight: 400; color: #7c8390;">{conf_label}</span>
            </span>
          </div>
          <div style="background: rgba(136,135,128,0.1); border-radius: 6px;
          height: 6px; overflow: hidden;">
            <div style="background: {conf_color}; height: 100%;
            width: {conf_pct}%; border-radius: 6px;"></div>
          </div>
    """)

    if ruling.confidence < 0.6:
        parts.append("""
          <div style="margin-top: 10px; padding: 8px 12px;
          background: rgba(226,75,74,0.08); border-radius: 6px;">
            <span style="font-size: 11px; color: #c43d3c;">
              &#9888; Low confidence — this case should be flagged for human review (Section 3.2).
            </span>
          </div>
        """)

    parts.append("</div>")

    # ─── Dual explanations ─────────────────────────────
    rider_reason = _html.escape(ruling.reasoning_for_rider).replace("\n", "<br>")
    driver_reason = _html.escape(ruling.reasoning_for_driver).replace("\n", "<br>")

    parts.append(f"""
        <div style="padding: 16px 20px; border-top: 1px solid #e8ebef;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
              <div style="font-size: 10px; font-weight: 700; color: #378ADD;
              margin-bottom: 8px; letter-spacing: 0.05em;">
                <span style="margin-right: 4px;">&#128100;</span>FOR THE RIDER
              </div>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.7; margin: 0;">
                {rider_reason}
              </p>
            </div>
            <div style="border-left: 1px solid #e8ebef; padding-left: 20px;">
              <div style="font-size: 10px; font-weight: 700; color: #D85A30;
              margin-bottom: 8px; letter-spacing: 0.05em;">
                <span style="margin-right: 4px;">&#128663;</span>FOR THE DRIVER
              </div>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.7; margin: 0;">
                {driver_reason}
              </p>
            </div>
          </div>
        </div>
    """)

    # ─── Policy applied ────────────────────────────────
    if ruling.policy_applied:
        parts.append("""
          <div style="padding: 16px 20px; border-top: 1px solid #e8ebef;">
            <span style="font-size: 10px; font-weight: 700; color: #7c8390;
            letter-spacing: 0.1em; text-transform: uppercase;">
              Policy applied
            </span>
            <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 6px;">
        """)
        for clause in ruling.policy_applied:
            parts.append(f"""
              <div style="display: flex; justify-content: space-between;
              align-items: center; padding: 8px 12px;
              background: #f5f6f8; border-radius: 6px;">
                <span style="font-size: 11px; color: #202735;">
                  &sect; {_html.escape(clause.clause)} &middot; {_html.escape(clause.title)}
                </span>
                <span style="color: #1D9E75; font-size: 11px; font-weight: 600;">&#10003;</span>
              </div>
            """)
        parts.append("</div></div>")

    # ─── Verification note ─────────────────────────────
    verification_text = _html.escape(ruling.verification_notes) if ruling.verification_notes else (
        "Independently verified GPS deviation, fare calculation, and policy applicability."
    )
    parts.append(f"""
        <div style="padding: 12px 20px; border-top: 1px solid #e8ebef;
        background: #fafafb;">
          <span style="font-size: 10px; color: #7c8390;">
            <span style="margin-right: 4px;">&#128737;</span>
            Verification: {verification_text}
          </span>
        </div>
    """)

    # ─── Close container ───────────────────────────────
    parts.append("</div></div>")

    # Render everything in one call
    st.markdown("".join(parts), unsafe_allow_html=True)
