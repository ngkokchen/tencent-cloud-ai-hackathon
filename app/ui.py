"""
Main Streamlit page: orchestrates the full dispute resolution UI.

Layout:
  Sidebar  — dispute form (sample case picker / custom filing + demo toggle)
  Main area — evidence panel -> live conversation log -> final ruling -> advocate cases
"""

import os
import time

import streamlit as st

from app.components.dispute_form import render_dispute_form
from app.components.message_log import render_message_log
from app.components.ruling_panel import render_ruling_panel
from app.components.evidence_panel import render_evidence_panel
from app.components.advocate_cases_panel import render_advocate_cases_panel
from evidence.loaders import CaseData
from models.message import ConversationLog
from models.ruling import Ruling


# --- Page entry point ------------------------------------------------

def main():
    st.set_page_config(
        page_title="Ryde Dispute Resolver",
        page_icon="S",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()

    # Sidebar form -- returns (case_data, run_mode) or (None, mode)
    case_data, run_mode = render_dispute_form()

    # -- Main area --
    st.title("Ryde Dispute Resolver")
    st.caption("Multi-agent autonomous dispute resolution for ride-hailing")

    if case_data is not None:
        # Button was just clicked -- run resolution and render progressively
        _run_and_render(case_data, run_mode)
    elif "resolution" in st.session_state:
        # Results from a previous run -- render instantly from session state
        _render_stored()
    else:
        _show_landing()


# --- CSS -------------------------------------------------------------

def _inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
        .main .block-container { padding-top: 1rem; max-width: 1200px; }
        .stSidebar .sidebar-content { padding-top: 1rem; }
        h2 { margin-top: 1.5rem !important; font-family: 'Manrope', sans-serif !important; }
        h3 { margin-top: 1rem !important; font-family: 'Manrope', sans-serif !important; }
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
        .stButton>button[kind="primary"] {
            background: #6653ca;
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 4px 10px rgba(102,83,202,0.15);
        }
        .stButton>button[kind="primary"]:hover {
            background: #5a48b8;
            box-shadow: 0 6px 14px rgba(102,83,202,0.22);
        }
        ::selection { background: rgba(102,83,202,0.15); }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Force light theme if browser/system prefers dark — UI designed for light mode only
    st.markdown(
        """
        <style>
        @media (prefers-color-scheme: dark) {
            .stApp { background-color: #ffffff !important; color: #202735 !important; }
            [data-testid="stAppViewContainer"] { background-color: #ffffff !important; }
            .main { background-color: #ffffff !important; }
            .stMarkdown p, .stMarkdown span, .stMarkdown div,
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
                color: inherit;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Run resolution + progressive render -----------------------------

def _run_and_render(case_data: CaseData, run_mode: str):
    """Run the dispute resolution pipeline and render results step by step."""

    # -- Pre-flight checks --
    if run_mode == "live" and not os.getenv("LLM_API_KEY"):
        st.error(
            "**Live mode requires an LLM API key.** "
            "Set `LLM_API_KEY` in your `.env` file."
        )
        st.info(
            "Switch to **Demo mode** (sidebar checkbox) to see the "
            "full system without an API key."
        )
        return

    # -- Dispute summary banner --
    dispute_id = case_data.dispute.get("dispute_id", "N/A")
    dispute_type = case_data.dispute.get("dispute_type", "unknown")
    type_label = dispute_type.replace("_", " ").title()
    ride_id = case_data.dispute.get("ride_id", "N/A")
    pickup = case_data.trip.get("pickup", {}).get("address", "")
    dropoff = case_data.trip.get("dropoff", {}).get("address", "")
    route_text = f"{pickup} → {dropoff}" if pickup and dropoff else f"Trip #{ride_id}"
    dispute_accent = {"route_deviation": "#D85A30", "no_show": "#378ADD"}.get(dispute_type, "#6653ca")

    st.markdown(
        f"""
        <div style="border: 1px solid #e8ebef; border-radius: 12px; overflow: hidden;
        margin-bottom: 16px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; align-items: stretch;">
            <div style="width: 4px; background: {dispute_accent};"></div>
            <div style="padding: 16px 20px; display: flex; flex: 1;
            justify-content: space-between; align-items: center;">
              <div>
                <span style="color: #202735; font-size: 14px; font-weight: 700;">
                  {type_label} <span style="color: #7c8390; font-weight: 400;">#{dispute_id}</span>
                </span>
                <p style="color: #7c8390; font-size: 12px; margin: 4px 0 0 0;">
                  {route_text}
                </p>
              </div>
              <span style="background: #eaf6f0; color: #1D9E75; font-size: 11px;
              font-weight: 600; padding: 4px 10px; border-radius: 6px;">
                Resolved
              </span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Evidence room --
    try:
        render_evidence_panel(case_data)
    except Exception as exc:
        st.warning(f"Evidence panel unavailable: {exc}")

    # -- Run the resolution pipeline --
    log = ConversationLog()

    try:
        with st.spinner("Resolving dispute..."):
            if run_mode == "live":
                from graph.orchestrator import run_dispute_resolution
                from llm.client import LLMClient

                llm = LLMClient()
                ruling, rider_arg, driver_arg, rider_reb, driver_reb = (
                    run_dispute_resolution(case_data, llm, log)
                )
            else:
                from graph.orchestrator import run_demo_resolution

                ruling, rider_arg, driver_arg, rider_reb, driver_reb = (
                    run_demo_resolution(case_data, log, delay=0)
                )
    except Exception as exc:
        st.error(f"Resolution failed: {exc}")
        return

    # -- Agent conversation container --
    messages = log.messages
    render_message_log(messages)

    # -- Final ruling container --
    render_ruling_panel(ruling)

    # -- Advocate cases container --
    render_advocate_cases_panel(rider_arg, driver_arg, rider_reb, driver_reb)

    # -- Persist in session state --
    st.session_state["resolution"] = {
        "ruling": ruling,
        "rider_arg": rider_arg,
        "driver_arg": driver_arg,
        "rider_reb": rider_reb,
        "driver_reb": driver_reb,
        "messages": messages,
        "case": case_data,
        "dispute_id": dispute_id,
    }

    # -- Reset button --
    st.markdown("---")
    st.markdown(
        """
        <div style="display: flex; justify-content: center; margin: 8px 0 16px 0;">
        """,
        unsafe_allow_html=True,
    )
    if st.button("Start New Dispute", type="primary"):
        st.session_state.pop("resolution", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# --- Render stored results (after page rerun) ------------------------

def _render_stored():
    """Render results from session state instantly (no re-run needed)."""
    res = st.session_state["resolution"]
    case: CaseData = res["case"]
    ruling: Ruling = res["ruling"]
    rider_arg: Argument = res["rider_arg"]
    driver_arg: Argument = res["driver_arg"]
    rider_reb: Rebuttal | None = res.get("rider_reb")
    driver_reb: Rebuttal | None = res.get("driver_reb")
    messages = res["messages"]

    dispute_id = res.get("dispute_id", "N/A")
    dispute_type = case.dispute.get("dispute_type", "unknown")
    type_label = dispute_type.replace("_", " ").title()
    ride_id = case.dispute.get("ride_id", "N/A")
    pickup = case.trip.get("pickup", {}).get("address", "")
    dropoff = case.trip.get("dropoff", {}).get("address", "")
    route_text = f"{pickup} → {dropoff}" if pickup and dropoff else f"Trip #{ride_id}"
    dispute_accent = {"route_deviation": "#D85A30", "no_show": "#378ADD"}.get(dispute_type, "#6653ca")

    st.markdown(
        f"""
        <div style="border: 1px solid #e8ebef; border-radius: 12px; overflow: hidden;
        margin-bottom: 16px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; align-items: stretch;">
            <div style="width: 4px; background: {dispute_accent};"></div>
            <div style="padding: 16px 20px; display: flex; flex: 1;
            justify-content: space-between; align-items: center;">
              <div>
                <span style="color: #202735; font-size: 14px; font-weight: 700;">
                  {type_label} <span style="color: #7c8390; font-weight: 400;">#{dispute_id}</span>
                </span>
                <p style="color: #7c8390; font-size: 12px; margin: 4px 0 0 0;">
                  {route_text}
                </p>
              </div>
              <span style="background: #eaf6f0; color: #1D9E75; font-size: 11px;
              font-weight: 600; padding: 4px 10px; border-radius: 6px;">
                Resolved
              </span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Evidence room
    try:
        render_evidence_panel(case)
    except Exception as exc:
        st.warning(f"Evidence panel unavailable: {exc}")

    # Agent conversation container
    render_message_log(messages)

    # Ruling
    render_ruling_panel(ruling)

    # Advocate cases container
    render_advocate_cases_panel(rider_arg, driver_arg, rider_reb, driver_reb)

    # Reset button
    st.markdown("---")
    st.markdown(
        """
        <div style="display: flex; justify-content: center; margin: 8px 0 16px 0;">
        """,
        unsafe_allow_html=True,
    )
    if st.button("Start New Dispute", type="primary"):
        st.session_state.pop("resolution", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# --- Landing page ----------------------------------------------------

def _show_landing():
    """Informational landing page shown when no dispute is selected."""
    st.markdown(
        """
        <div style="border: 1px solid #e8ebef; border-radius: 16px; overflow: hidden;
        background: linear-gradient(135deg, #ffffff 0%, #f8f7fc 100%);
        margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="padding: 32px 36px;">
            <span style="display: inline-block; background: rgba(102,83,202,0.1);
            color: #6653ca; font-size: 10px; font-weight: 700; padding: 4px 12px;
            border-radius: 6px; text-transform: uppercase; letter-spacing: 0.08em;">
              Three Perspectives. One Fair Decision.
            </span>
            <h2 style="font-size: 32px; font-weight: 800; color: #202735;
            margin: 16px 0 12px 0; letter-spacing: -1px;
            font-family: 'Manrope', sans-serif;">
              Less back-and-forth.<br>More moving forward.
            </h2>
            <p style="font-size: 14px; color: #7c8390; line-height: 1.6;
            max-width: 480px;">
              Give every dispute the attention it deserves. Independent advocates
              examine the evidence, challenge assumptions, and bring both sides
              to a reasoned resolution.
            </p>
          </div>
        </div>

        <h3 style="font-size: 18px; font-weight: 700; color: #202735;
        margin-bottom: 4px;">From complaint to clarity</h3>
        <p style="font-size: 12px; color: #7c8390; margin-bottom: 16px;">
          An explainable, three-phase process
        </p>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div style="border: 1px solid #e8ebef; border-radius: 12px;
            padding: 20px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <span style="font-size: 10px; font-weight: 700; color: #6653ca;
              letter-spacing: 0.08em;">01 / GATHER</span>
              <h4 style="font-size: 14px; font-weight: 600; color: #202735;
              margin: 8px 0 6px 0;">Independent investigation</h4>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.5;">
                Rider and driver advocates gather trip, fare, chat, and policy
                evidence in parallel.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div style="border: 1px solid #e8ebef; border-radius: 12px;
            padding: 20px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <span style="font-size: 10px; font-weight: 700; color: #6653ca;
              letter-spacing: 0.08em;">02 / CHALLENGE</span>
              <h4 style="font-size: 14px; font-weight: 600; color: #202735;
              margin: 8px 0 6px 0;">A balanced exchange</h4>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.5;">
                Both advocates present their arguments and test the other side's
                reasoning with rebuttals.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div style="border: 1px solid #e8ebef; border-radius: 12px;
            padding: 20px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <span style="font-size: 10px; font-weight: 700; color: #6653ca;
              letter-spacing: 0.08em;">03 / RESOLVE</span>
              <h4 style="font-size: 14px; font-weight: 600; color: #202735;
              margin: 8px 0 6px 0;">A transparent ruling</h4>
              <p style="font-size: 12px; color: #7c8390; line-height: 1.5;">
                The judge delivers a decision, amount, confidence score, and an
                explanation for each party.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="border: 1px solid #e8ebef; border-radius: 12px;
        padding: 20px; background: white; margin-top: 16px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div>
            <p style="font-size: 14px; font-weight: 600; color: #202735; margin: 0;">
              Ready to hear both sides?
            </p>
            <p style="font-size: 12px; color: #7c8390; margin: 4px 0 0 0;">
              Pick a sample case or file a custom dispute from the sidebar.
            </p>
          </div>
          <div>
            <span style="display: inline-block; background: #f5f6f8;
            color: #7c8390; font-size: 11px; font-weight: 500;
            padding: 4px 10px; border-radius: 6px; margin-right: 4px;">
              Route deviation
            </span>
            <span style="display: inline-block; background: #f5f6f8;
            color: #7c8390; font-size: 11px; font-weight: 500;
            padding: 4px 10px; border-radius: 6px;">
              No-show charge
            </span>
          </div>
        </div>
        <p style="font-size: 11px; color: #7c8390; text-align: center; margin-top: 12px;">
          <b>Demo mode</b> is enabled by default — you can see the full system
          without an API key.
        </p>
        """,
        unsafe_allow_html=True,
    )


# --- Entrypoint ------------------------------------------------------

if __name__ == "__main__":
    main()
