"""Ruling panel component: renders the final ruling as a prominent card."""

import streamlit as st

from models.ruling import Ruling


DECISION_COLORS = {
    "refund": "#1D9E75",
    "compensation": "#378ADD",
    "no_action": "#888780",
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

    color = DECISION_COLORS.get(ruling.ruling, "#888780")
    label = DECISION_LABELS.get(ruling.ruling, ruling.ruling.upper())

    # ─── Header bar ──────────────────────────────────────
    st.markdown(f"""
    <div style="border: 1px solid {color}40; border-radius: 12px; overflow: hidden;
    margin-bottom: 16px;">
      <div style="background: {color}; padding: 16px 20px; display: flex;
      justify-content: space-between; align-items: center;">
        <span style="color: white; font-size: 20px; font-weight: 600;">{label}</span>
        <span style="color: white; font-size: 24px; font-weight: 600;">
        ${ruling.amount:.2f}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Action line ─────────────────────────────────────
    st.markdown(f"**{ruling.action}**")

    # ─── Confidence score ────────────────────────────────
    conf_pct = int(ruling.confidence * 100)
    conf_color = "#1D9E75" if ruling.confidence >= 0.8 else "#EF9F27" if ruling.confidence >= 0.6 else "#E24B4A"

    st.markdown(f"""
    <div style="margin: 12px 0;">
      <div style="font-size: 13px; color: #888; margin-bottom: 4px;">
      Confidence score</div>
      <div style="background: rgba(136,135,128,0.15); border-radius: 6px;
      height: 24px; overflow: hidden;">
        <div style="background: {conf_color}; height: 100%; width: {conf_pct}%;
        display: flex; align-items: center; justify-content: flex-end;
        padding-right: 8px; font-size: 12px; color: white; font-weight: 500;">
        {ruling.confidence:.2f}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if ruling.confidence < 0.6:
        st.warning("Low confidence — this case should be flagged for human review (Section 3.2).")

    # ─── Explanations ────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### For the rider")
        st.info(ruling.reasoning_for_rider)

    with col2:
        st.markdown("#### For the driver")
        st.info(ruling.reasoning_for_driver)

    # ─── Policy applied ──────────────────────────────────
    if ruling.policy_applied:
        st.markdown("#### Policy applied")
        for clause in ruling.policy_applied:
            st.markdown(
                f"- **Section {clause.clause}** — {clause.title}: "
                f"*{clause.relevance}*"
            )

    # ─── Verification notes ──────────────────────────────
    if ruling.verification_notes:
        st.caption(f"Verification: {ruling.verification_notes}")
