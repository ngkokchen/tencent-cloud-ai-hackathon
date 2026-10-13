"""Dispute form component: sample case selection or custom dispute filing."""

import streamlit as st

from evidence.loaders import list_available_cases, load_case_by_file
from evidence.loaders import CaseData


def render_dispute_form() -> tuple[CaseData | None, str]:
    """
    Render the dispute selection form in the sidebar.

    Returns:
        (case_data, run_mode) where run_mode is "demo" or "live",
        or (None, "demo") if nothing selected yet.
    """
    st.sidebar.title("Ryde Dispute Resolver")
    st.sidebar.caption("Multi-agent autonomous dispute resolution")

    mode = st.sidebar.radio(
        "Choose input method",
        ["Pick sample case", "File custom dispute"],
        label_visibility="collapsed",
    )

    demo_mode = st.sidebar.checkbox(
        "Demo mode (no LLM API key needed)",
        value=True,
        help="If checked, uses rule-based mock agent outputs. "
             "Uncheck to call the real LLM (requires API key in .env).",
    )

    case_data = None
    run_mode = "demo" if demo_mode else "live"

    if mode == "Pick sample case":
        cases = list_available_cases()
        if not cases:
            st.sidebar.warning("No sample cases found.")
            return None, "demo"

        labels = [
            f"{c['dispute_id']} — {c['label']}"
            for c in cases
        ]
        selected_idx = st.sidebar.selectbox(
            "Select a dispute case",
            range(len(labels)),
            format_func=lambda i: labels[i],
        )

        selected = cases[selected_idx]
        st.sidebar.markdown(f"**Route:** {selected['route']}")
        st.sidebar.markdown(f"**Summary:** {selected['summary']}")

        if st.sidebar.button("Resolve Dispute", type="primary", use_container_width=True):
            from pathlib import Path
            from config.settings import SAMPLES_DIR
            case_file = SAMPLES_DIR / selected["file"]
            case_data = load_case_by_file(case_file)

    else:
        # Custom dispute form
        st.sidebar.markdown("### File a new dispute")

        dispute_type = st.sidebar.selectbox(
            "Dispute type",
            ["route_deviation", "no_show"],
            format_func=lambda x: "Route deviation" if x == "route_deviation" else "No-show charge",
        )

        trip_id = st.sidebar.text_input("Trip ID", value="RIDE-CUSTOM-001")
        complaint = st.sidebar.text_area(
            "Complaint description",
            value="Driver took a longer route than expected.",
            height=80,
        )

        rider_id = st.sidebar.text_input("Rider ID", value="R-CUST-001")
        driver_id = st.sidebar.text_input("Driver ID", value="D-CUST-001")

        if st.sidebar.button("Resolve Dispute", type="primary", use_container_width=True):
            # Build a minimal CaseData from the custom input
            case_data = CaseData(
                dispute={
                    "dispute_id": "CUSTOM-001",
                    "dispute_type": dispute_type,
                    "filed_by": "rider",
                    "ride_id": trip_id,
                    "claim": complaint,
                    "requested_remedy": {"type": "refund", "amount": 0.0},
                },
                trip={"ride_id": trip_id},
                chat_logs=[],
                fare_breakdown={},
                rider_profile={"rider_id": rider_id, "name": "Custom Rider",
                               "account_age_days": 365, "rating": 4.5,
                               "total_rides": 50, "past_disputes": []},
                driver_profile={"driver_id": driver_id, "name": "Custom Driver",
                                "account_age_days": 365, "rating": 4.5,
                                "total_rides": 500, "completion_rate": 0.95,
                                "past_disputes": []},
                raw={},
                file_path="custom",
            )

    return case_data, run_mode
