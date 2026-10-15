"""Advocate cases panel: renders rider & driver arguments + rebuttals in a styled container."""

import html as _html
import textwrap

import streamlit as st

from models.argument import Argument, Rebuttal


def _h(s: str) -> str:
    """Strip leading indentation from HTML strings so Streamlit doesn't treat them as code blocks."""
    return textwrap.dedent(s).strip()


def render_advocate_cases_panel(
    rider_arg: Argument | None,
    driver_arg: Argument | None,
    rider_reb: Rebuttal | None,
    driver_reb: Rebuttal | None,
) -> None:
    """Render both advocate cases inside a styled container card matching the Final ruling design."""
    if rider_arg is None and driver_arg is None:
        st.info("No advocate arguments available yet.")
        return

    parts = []

    # ─── Container with tinted border ──────────────────
    parts.append(_h("""
        <div style="border: 1px solid rgba(102,83,202,0.18); border-radius: 12px;
        background: white; margin-bottom: 20px; overflow: hidden;">
    """))

    # ─── Header bar ────────────────────────────────────
    parts.append(_h("""
        <div style="background: #f8f7fc; padding: 16px 20px;
        border-bottom: 1px solid rgba(102,83,202,0.12);">
          <div style="display: flex; justify-content: space-between;
          align-items: center;">
            <span style="font-size: 10px; font-weight: 700;
            color: #6653ca; letter-spacing: 0.12em;">
              <span style="margin-right: 4px;">&#9878;</span>ADVOCATE CASES
            </span>
            <span style="font-size: 9px; color: #6653ca;
            border: 1px solid rgba(102,83,202,0.18);
            border-radius: 4px; padding: 2px 8px;">
              Both sides represented
            </span>
          </div>
        </div>
    """))

    # ─── Body ──────────────────────────────────────────
    parts.append("<div style=\"padding: 20px;\">")

    # ─── Two-column grid ───────────────────────────────
    parts.append(_h("""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
    """))

    # --- Rider advocate ---
    parts.append(_render_advocate_column(rider_arg, rider_reb, "rider"))

    # --- Driver advocate ---
    parts.append(_render_advocate_column(driver_arg, driver_reb, "driver"))

    parts.append("</div></div></div>")

    # Render everything in one call
    st.markdown("".join(parts), unsafe_allow_html=True)


def _render_advocate_column(arg: Argument | None, reb: Rebuttal | None, side: str) -> str:
    """Build HTML for one advocate column (rider or driver)."""
    if side == "rider":
        accent = "#378ADD"
        label = "RIDER ADVOCATE"
        border_side = ""
    else:
        accent = "#D85A30"
        label = "DRIVER ADVOCATE"
        border_side = 'border-left: 1px solid #e8ebef; padding-left: 16px;'

    if arg is None:
        return _h(f"""
            <div style="{border_side}">
              <div style="height: 3px; background: {accent}; border-radius: 2px; margin-bottom: 12px;"></div>
              <p style="font-size: 11px; font-weight: 700; color: {accent}; margin: 0 0 8px 0;">{label}</p>
              <p style="font-size: 11px; color: #7c8390; margin: 0;">No argument submitted.</p>
            </div>
        """)

    remedy_labels = {"refund": "Refund", "compensation": "Compensation", "no_action": "No Action"}
    remedy_label = remedy_labels.get(arg.requested_remedy, arg.requested_remedy)
    amount_str = f" (${arg.requested_amount:.2f})" if arg.requested_amount > 0 else ""
    claim = _html.escape(arg.claim)
    reasoning = _html.escape(arg.reasoning).replace("\n", "<br>") if arg.reasoning else ""

    # Tags
    tags_html = ""
    if arg.evidence:
        tags_html += (
            f"<span style='display: inline-block; background: rgba(102,83,202,0.08); "
            f"color: #6653ca; font-size: 10px; font-weight: 600; padding: 2px 8px; "
            f"border-radius: 4px; margin-right: 4px;'>{len(arg.evidence)} evidence items</span>"
        )
    if arg.policy_cited:
        clauses = ", ".join(_html.escape(p.clause) for p in arg.policy_cited)
        tags_html += (
            f"<span style='display: inline-block; background: #f5f6f8; "
            f"color: #7c8390; font-size: 10px; font-weight: 600; padding: 2px 8px; "
            f"border-radius: 4px; margin-right: 4px;'>{clauses}</span>"
        )

    # Evidence items HTML
    evidence_html = ""
    if arg.evidence:
        evidence_rows = ""
        for ev in arg.evidence:
            evidence_rows += _h(f"""
                <div style="display: flex; gap: 8px; margin: 4px 0;
                font-size: 11px; line-height: 1.5;">
                  <span style="color: #7c8390; white-space: nowrap;">
                    {_html.escape(ev.source)}
                  </span>
                  <span style="color: #202735;">{_html.escape(ev.fact)}</span>
                </div>
            """)
        evidence_html = _h(f"""
            <p style="font-size: 10px; font-weight: 700; color: #7c8390;
            letter-spacing: 0.1em; text-transform: uppercase; margin: 10px 0 6px 0;">
              Evidence
            </p>
            {evidence_rows}
        """)

    # Policy citations HTML
    policy_html = ""
    if arg.policy_cited:
        policy_rows = ""
        for pol in arg.policy_cited:
            policy_rows += _h(f"""
                <div style="font-size: 11px; line-height: 1.5; margin: 4px 0;">
                  <span style="color: #202735; font-weight: 600;">
                    &sect; {_html.escape(pol.clause)} &middot; {_html.escape(pol.title)}
                  </span>
                  <p style="color: #7c8390; margin: 2px 0 0 0;">
                    {_html.escape(pol.relevance)}
                  </p>
                </div>
            """)
        policy_html = _h(f"""
            <p style="font-size: 10px; font-weight: 700; color: #7c8390;
            letter-spacing: 0.1em; text-transform: uppercase; margin: 10px 0 6px 0;">
              Policy cited
            </p>
            {policy_rows}
        """)

    # Rebuttal HTML
    rebuttal_html = ""
    if reb and (reb.counterpoints or reb.reasoning):
        cp_items = ""
        for cp in reb.counterpoints:
            cp_items += f'<p style="font-size: 11px; color: #202735; margin: 0 0 4px 0; line-height: 1.5;">&middot; {_html.escape(cp)}</p>'
        reasoning_text = ""
        if reb.reasoning:
            reasoning_text = f'<p style="font-size: 11px; color: #9a9da3; margin: 6px 0 0 0; font-style: italic; line-height: 1.5;">{_html.escape(reb.reasoning)}</p>'
        rebuttal_html = _h(f"""
            <div style="margin-top: 12px; padding: 10px 12px;
            background: rgba(102,83,202,0.04); border-radius: 8px;
            border-left: 2px solid #6653ca;">
              <p style="font-size: 11px; font-weight: 600; color: #6653ca; margin: 0 0 6px 0;">
                Rebuttal
              </p>
              {cp_items}
              {reasoning_text}
            </div>
        """)

    # Full argument details toggle (HTML details/summary)
    details_html = ""
    if reasoning or evidence_html or policy_html:
        details_html = _h(f"""
            <details style="margin-top: 12px;">
              <summary style="font-size: 11px; font-weight: 600; color: #202735;
              cursor: pointer; list-style: none; display: flex; align-items: center;">
                <span style="margin-right: 4px; color: #7c8390;">&#9654;</span>
                Full argument details
              </summary>
              <div style="margin-top: 10px; padding: 12px;
              background: #f5f6f8; border-radius: 6px;">
                {reasoning and f'<p style="font-size: 11px; color: #202735; line-height: 1.6; margin: 0 0 10px 0;">{reasoning}</p>' or ''}
                {evidence_html}
                {policy_html}
              </div>
            </details>
        """)

    return _h(f"""
        <div style="{border_side}">
          <div style="height: 3px; background: {accent}; border-radius: 2px; margin-bottom: 12px;"></div>
          <p style="font-size: 11px; font-weight: 700; color: {accent}; margin: 0 0 12px 0;">
            {label}
          </p>
          <p style="font-size: 13px; font-weight: 600; color: #202735; margin: 0 0 4px 0;">
            {claim}
          </p>
          <p style="font-size: 12px; color: #7c8390; margin: 0 0 8px 0;">
            Requested: <b style="color: #202735;">{remedy_label}{amount_str}</b>
          </p>
          {tags_html and f'<div style="margin-bottom: 4px;">{tags_html}</div>' or ''}
          {details_html}
          {rebuttal_html}
        </div>
    """)
