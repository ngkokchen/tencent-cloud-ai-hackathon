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
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
          <div style="width: 32px; height: 32px; border-radius: 8px;
          background: #202735; color: white; display: flex;
          align-items: center; justify-content: center; font-size: 14px;">
            &#128739;
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 800; color: #202735;
            letter-spacing: -0.5px;">ryde<span style="color: #6653ca;">.</span></div>
            <div style="font-size: 9px; color: #7c8390; letter-spacing: 0.08em;">
              DISPUTE RESOLVER
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.sidebar.markdown(
            f"""
            <div style="border-left: 2px solid #e8ebef; margin-left: 4px;
            padding-left: 16px; margin-top: 12px; position: relative;">
              <div style="position: absolute; left: -5px; top: 4px;
              width: 8px; height: 8px; border-radius: 50%;
              background: white; border: 2px solid #6653ca;"></div>
              <p style="font-size: 10px; color: #7c8390; margin: 0 0 2px 0;">
                PICKUP
              </p>
              <p style="font-size: 12px; color: #202735; margin: 0 0 12px 0;">
                {selected['route'].split(' → ')[0] if ' → ' in selected['route'] else selected['route']}
              </p>
              <div style="position: absolute; left: -5px; bottom: 4px;
              width: 8px; height: 8px; border-radius: 2px;
              background: #202735;"></div>
              <p style="font-size: 10px; color: #7c8390; margin: 0 0 2px 0;">
                DROPOFF
              </p>
              <p style="font-size: 12px; color: #202735; margin: 0;">
                {selected['route'].split(' → ')[1] if ' → ' in selected['route'] else 'N/A'}
              </p>
            </div>
            <p style="font-size: 11px; color: #7c8390; line-height: 1.6; margin-top: 12px;">
              {selected['summary']}
            </p>
            """,
            unsafe_allow_html=True,
        )

        if st.sidebar.button("Resolve Dispute", type="primary", use_container_width=True):
            from pathlib import Path
            from config.settings import SAMPLES_DIR
            case_file = SAMPLES_DIR / selected["file"]
            case_data = load_case_by_file(case_file)

    else:
        # Custom dispute form
        st.sidebar.markdown(
            "<p style='font-size: 13px; font-weight: 600; color: #202735; margin-bottom: 8px;'>"
            "File a new dispute</p>",
            unsafe_allow_html=True,
        )

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

    st.sidebar.markdown(
        """
        <div style="border-top: 1px solid #e8ebef; margin-top: 16px; padding-top: 12px;">
          <p style="font-size: 10px; color: #7c8390; line-height: 1.5;">
            <span style="color: #6653ca; margin-right: 4px;">&#128737;</span>
            Balanced by design.<br>
            <span style="padding-left: 16px;">Every side heard. Every decision explained.</span>
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return case_data, run_mode
