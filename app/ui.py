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
from app.components.message_log import render_single_message
from app.components.ruling_panel import render_ruling_panel
from app.components.evidence_panel import render_evidence_panel
from evidence.loaders import CaseData
from models.argument import Argument, Rebuttal
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
        .main .block-container { padding-top: 1rem; max-width: 1100px; }
        .stSidebar .sidebar-content { padding-top: 1rem; }
        h2 { margin-top: 1.5rem !important; }
        h3 { margin-top: 1rem !important; }
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
    st.success(f"**Dispute {dispute_id}** - Type: {type_label}")

    # -- Evidence panel (collapsible) --
    with st.expander("Evidence Summary", expanded=False):
        try:
            render_evidence_panel(case_data)
        except Exception as exc:
            st.warning(f"Evidence panel unavailable: {exc}")

    st.markdown("---")

    # -- Conversation log header --
    st.header("Agent Conversation Log")
    st.caption("Every message between agents is logged in real time.")

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

    # -- Render messages progressively (step by step) --
    messages = log.messages
    log_area = st.container()

    for i, msg in enumerate(messages):
        with log_area:
            render_single_message(msg, i)

        # Visual pacing -- longer pauses for arguments/rulings
        if msg.msg_type in ("argument", "rebuttal", "ruling"):
            time.sleep(0.4)
        elif msg.msg_type in ("tool_call", "tool_result"):
            time.sleep(0.15)
        else:
            time.sleep(0.12)

    # -- Final ruling --
    st.markdown("---")
    st.header("Final Ruling")
    render_ruling_panel(ruling)

    # -- Advocate case summaries --
    st.markdown("---")
    st.header("Advocate Cases")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Rider Advocate")
        _render_argument_summary(rider_arg)
        if rider_reb:
            _render_rebuttal_summary(rider_reb)
    with col2:
        st.markdown("#### Driver Advocate")
        _render_argument_summary(driver_arg)
        if driver_reb:
            _render_rebuttal_summary(driver_reb)

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
    if st.button("Start New Dispute"):
        st.session_state.pop("resolution", None)
        st.rerun()


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
    st.success(f"**Dispute {dispute_id}** - Type: {type_label}")

    # Evidence panel
    with st.expander("Evidence Summary", expanded=False):
        try:
            render_evidence_panel(case)
        except Exception as exc:
            st.warning(f"Evidence panel unavailable: {exc}")

    st.markdown("---")

    # Conversation log (all at once)
    st.header("Agent Conversation Log")
    st.caption("Every message between agents is logged in real time.")
    for i, msg in enumerate(messages):
        render_single_message(msg, i)

    # Ruling
    st.markdown("---")
    st.header("Final Ruling")
    render_ruling_panel(ruling)

    # Advocate summaries
    st.markdown("---")
    st.header("Advocate Cases")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Rider Advocate")
        _render_argument_summary(rider_arg)
        if rider_reb:
            _render_rebuttal_summary(rider_reb)
    with col2:
        st.markdown("#### Driver Advocate")
        _render_argument_summary(driver_arg)
        if driver_reb:
            _render_rebuttal_summary(driver_reb)

    # Reset button
    st.markdown("---")
    if st.button("Start New Dispute"):
        st.session_state.pop("resolution", None)
        st.rerun()


# --- Helper: rebuttal summary ----------------------------------------

def _render_rebuttal_summary(reb: Rebuttal):
    """Render a concise summary of an advocate's rebuttal."""
    st.markdown("**Rebuttal:**")
    for cp in reb.counterpoints:
        st.markdown(f"- {cp}")
    if reb.reasoning:
        st.caption(reb.reasoning)


# --- Helper: argument summary ----------------------------------------

def _render_argument_summary(arg: Argument):
    """Render a concise summary of an advocate's structured argument."""
    remedy_labels = {
        "refund": "Refund",
        "compensation": "Compensation",
        "no_action": "No Action",
    }
    remedy_label = remedy_labels.get(arg.requested_remedy, arg.requested_remedy)
    amount_str = f" (${arg.requested_amount:.2f})" if arg.requested_amount > 0 else ""

    st.markdown(f"**Claim:** {arg.claim}")
    st.markdown(f"**Requested:** {remedy_label}{amount_str}")
    st.markdown(f"**Evidence items:** {len(arg.evidence)}")

    clauses = ", ".join(p.clause for p in arg.policy_cited) or "None"
    st.markdown(f"**Policy clauses cited:** {clauses}")

    with st.expander("Full argument details"):
        st.json(arg.model_dump())


# --- Landing page ----------------------------------------------------

def _show_landing():
    """Informational landing page shown when no dispute is selected."""
    st.markdown(
        """
        ## How it works

        This system uses **three AI agents** to autonomously resolve
        ride-hailing disputes:

        | Agent | Role | Bias |
        |-------|------|------|
        | **Rider Advocate** | Gathers evidence supporting the rider's claim | Pro-rider |
        | **Driver Advocate** | Gathers evidence supporting the driver's position | Pro-driver |
        | **Judge** | Weighs both cases, applies company policy, issues binding ruling | Neutral |

        ### Resolution process

        1.  **Both advocates** independently call evidence tools
            (GPS route, chat logs, fare breakdown, user history, company policy)
        2.  Each advocate builds a **structured argument** citing specific
            policy clauses and evidence items
        3.  Each advocate reviews the opponent's argument and produces
            **counterpoints** (rebuttal phase)
        4.  The **Judge** reviews both arguments and rebuttals, independently
            verifies key claims via tools, and issues a ruling

        ### Supported dispute types

        - **Route deviation** - driver took a longer route than the optimal path
        - **No-show charge** - rider disputes a no-show / cancellation fee

        ### Ruling output

        The Judge produces:

        - **Decision** - refund / compensation / no action
        - **Amount** - dollar figure for the remedy
        - **Confidence score** - 0.0 to 1.0 (below 0.6 flags for human review)
        - **Dual explanations** - separate natural-language reasoning for
          rider and driver

        ---

        **Pick a sample case or file a custom dispute from the sidebar**,
        then click **Resolve Dispute**.

        > **Demo mode** is enabled by default - you can see the full
        > system without an API key. Uncheck it to use real LLM-powered agents
        > (requires `LLM_API_KEY` in `.env`).
        """
    )


# --- Entrypoint ------------------------------------------------------

if __name__ == "__main__":
    main()
