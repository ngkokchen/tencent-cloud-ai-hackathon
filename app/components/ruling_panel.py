"""Ruling panel component: renders the final ruling as a prominent card."""

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
    """Render the Judge's final ruling as a prominent card."""
    if ruling is None:
        st.info("No ruling available yet.")
        return

    accent, bg, text = DECISION_COLORS.get(ruling.ruling, DECISION_COLORS["no_action"])
    label = DECISION_LABELS.get(ruling.ruling, ruling.ruling.upper())

    # ─── Header bar ──────────────────────────────────────
    st.markdown(
        f"""
        <div style="border: 1px solid {accent}30; border-radius: 12px;
        overflow: hidden; margin-bottom: 0;">
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
                  {ruling.action}
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
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Confidence score ────────────────────────────────
    conf_pct = int(ruling.confidence * 100)
    conf_color = "#1D9E75" if ruling.confidence >= 0.8 else "#EF9F27" if ruling.confidence >= 0.6 else "#E24B4A"
    conf_label = "High" if ruling.confidence >= 0.8 else "Medium" if ruling.confidence >= 0.6 else "Low"

    st.markdown(
        f"""
        <div style="padding: 16px 20px; border-left: 1px solid {accent}30;
        border-right: 1px solid {accent}30;">
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
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ruling.confidence < 0.6:
        st.warning("Low confidence — this case should be flagged for human review (Section 3.2).")

    # ─── Explanations ────────────────────────────────────
    st.markdown(
        f"""
        <div style="border: 1px solid {accent}30; border-top: none;
        border-radius: 0 0 12px 12px; padding: 16px 20px;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
              <div style="font-size: 10px; font-weight: 700; color: #378ADD;
              margin-bottom: 8px; letter-spacing: 0.05em;">
                <span style="margin-right: 4px;">&#128100;</span>FOR THE RIDER
              </div>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.7; margin: 0;">
                {ruling.reasoning_for_rider}
              </p>
            </div>
            <div style="border-left: 1px solid #e8ebef; padding-left: 20px;">
              <div style="font-size: 10px; font-weight: 700; color: #D85A30;
              margin-bottom: 8px; letter-spacing: 0.05em;">
                <span style="margin-right: 4px;">&#128663;</span>FOR THE DRIVER
              </div>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.7; margin: 0;">
                {ruling.reasoning_for_driver}
              </p>
            </div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Policy applied ──────────────────────────────────
    if ruling.policy_applied:
        st.markdown(
            """
            <div style="margin-top: 16px; padding-top: 16px;
            border-top: 1px solid #e8ebef;">
              <span style="font-size: 10px; font-weight: 700; color: #7c8390;
              letter-spacing: 0.1em; text-transform: uppercase;">
                Policy applied
              </span>
            """,
            unsafe_allow_html=True,
        )
        for clause in ruling.policy_applied:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between;
                align-items: center; padding: 6px 0;">
                  <span style="font-size: 11px; color: #202735;">
                    &sect; {clause.clause} &middot; {clause.title}
                  </span>
                  <span style="color: #1D9E75; font-size: 11px;">&#10003;</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── Verification notes ──────────────────────────────
    if ruling.verification_notes:
        st.markdown(
            f"""
            <div style="margin-top: 12px; padding: 10px 14px;
            background: #f5f6f8; border-radius: 8px;">
              <span style="font-size: 10px; color: #7c8390;">
                <span style="margin-right: 4px;">&#128737;</span>
                Verification: {ruling.verification_notes}
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
