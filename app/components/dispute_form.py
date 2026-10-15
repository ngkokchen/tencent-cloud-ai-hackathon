"""Dispute form component: sample case selection or custom dispute filing.

Matches the ui-design-draft.html sidebar styling.
"""

import streamlit as st

from evidence.loaders import list_available_cases, load_case_by_file
from evidence.loaders import CaseData


# Sidebar width override so the timeline has room
_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] { min-width: 280px !important; max-width: 310px !important; }

/* Segmented control style for radio */
[data-testid="stSidebar"] div[role="radiogroup"] {
    flex-direction: row !important;
    gap: 4px !important;
    background: #f5f6f8;
    padding: 4px;
    border-radius: 8px;
    align-items: stretch;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    flex: 1;
    margin: 0 !important;
    padding: 0 !important;
    text-align: center;
    cursor: pointer;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label > div {
    justify-content: center;
    padding: 0;
    border-radius: 6px;
    transition: all 0.15s;
}
/* Hide the radio circle icon */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
/* Label text styling */
[data-testid="stSidebar"] div[role="radiogroup"] > label [data-testid="stMarkdownContainer"] {
    text-align: center;
    font-size: 11px;
    font-weight: 500;
    padding: 8px 0;
    border-radius: 6px;
    display: block;
}
/* Inactive label */
[data-testid="stSidebar"] div[role="radiogroup"] > label [data-testid="stMarkdownContainer"] p {
    color: #7c8390;
}
/* Active label (checked) */
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) [data-testid="stMarkdownContainer"] {
    background: white;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) [data-testid="stMarkdownContainer"] p {
    color: #202735;
    font-weight: 600;
}

/* Full-width toggle across the sidebar */
[data-testid="stSidebar"] div[data-testid="stRadio"] {
    width: 100% !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
    width: 100% !important;
}

/* Field styling to match the app design (rounded, soft canvas bg) */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div,
[data-testid="stSidebar"] .stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid #e8ebef !important;
    background: #f5f6f8 !important;
    font-size: 12px !important;
    color: #202735 !important;
    transition: border-color 0.15s;
}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
[data-testid="stSidebar"] .stTextInput > div > div:focus-within,
[data-testid="stSidebar"] .stTextArea textarea:focus {
    border-color: #6653ca !important;
    box-shadow: 0 0 0 1px rgba(102,83,202,0.15) !important;
}

/* Sidebar labels — smaller, muted, matching the draft */
[data-testid="stSidebar"] .stSelectbox label p,
[data-testid="stSidebar"] .stTextInput label p,
[data-testid="stSidebar"] .stTextArea label p {
    font-size: 11px !important;
    color: #7c8390 !important;
    margin-bottom: 4px !important;
}

/* Checkbox — subtle accent */
[data-testid="stSidebar"] .stCheckbox label p {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #202735 !important;
}

/* Resolve Dispute button — match app primary styling */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #6653ca !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 10px 0 !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(102,83,202,0.15) !important;
    transition: all 0.18s;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #5a48b8 !important;
    box-shadow: 0 6px 14px rgba(102,83,202,0.22) !important;
    filter: none !important;
}
</style>
"""


def _parse_route(route_str: str) -> tuple[str, str]:
    """Parse pickup and dropoff from a route string."""
    if not route_str:
        return "N/A", "N/A"
    for sep in (" -> ", " → ", " to ", " - "):
        if sep in route_str:
            parts = route_str.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return route_str.strip(), "N/A"


def render_dispute_form() -> tuple[CaseData | None, str]:
    """
    Render the dispute selection form in the sidebar.

    Returns:
        (case_data, run_mode) where run_mode is "demo" or "live",
        or (None, "demo") if nothing selected yet.
    """
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

    # ─── Header ──────────────────────────────────────────
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
          <div style="width: 36px; height: 36px; border-radius: 10px;
          background: #202735; color: white; display: flex;
          align-items: center; justify-content: center; font-size: 16px;">
            &#128739;
          </div>
          <div>
            <div style="font-size: 18px; font-weight: 800; color: #202735;
            letter-spacing: -0.5px; line-height: 1.1;">
              ryde<span style="color: #6653ca;">.</span>
            </div>
            <div style="font-size: 9px; color: #7c8390; letter-spacing: 0.1em; margin-top: 2px;">
              DISPUTE RESOLVER
            </div>
          </div>
          <span style="margin-left: auto; font-size: 9px; border: 1px solid #e8ebef;
          border-radius: 4px; padding: 1px 5px; color: #7c8390; font-weight: 600;">
            BETA
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Section label ───────────────────────────────────
    st.sidebar.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <span style="font-size: 10px; font-weight: 700; color: #7c8390;
          letter-spacing: 0.1em; text-transform: uppercase;">
            Resolution workspace
          </span>
          <span style="font-size: 11px; color: #7c8390;">&#9881;</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Method toggle (working horizontal radio) ────────
    _method_key = "_df_method"
    if _method_key not in st.session_state:
        st.session_state[_method_key] = "sample"

    method = st.session_state[_method_key]

    mode = st.sidebar.radio(
        "Choose input method",
        ["Pick sample case", "File custom dispute"],
        label_visibility="collapsed",
        horizontal=True,
        index=0 if method == "sample" else 1,
        key="_df_radio",
    )
    # Sync back to our state
    st.session_state[_method_key] = "sample" if mode == "Pick sample case" else "custom"

    # ─── Demo mode ───────────────────────────────────────
    demo_mode = st.sidebar.checkbox(
        "Demo mode",
        value=True,
        help="Uses simulated agent responses. No real charges or account changes.",
        key="_df_demo",
    )
    demo_note = (
        "Uses simulated agent responses. No real charges or account changes."
        if demo_mode
        else "Preview only. Live resolution is not connected."
    )
    st.sidebar.markdown(
        f"""
        <p style="font-size: 10px; color: #7c8390; line-height: 1.5; margin-top: 4px;">
          {demo_note}
        </p>
        """,
        unsafe_allow_html=True,
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
            "Sample case",
            range(len(labels)),
            format_func=lambda i: labels[i],
            label_visibility="visible",
            key="_df_case_select",
        )

        selected = cases[selected_idx]
        pickup, dropoff = _parse_route(selected.get("route", ""))

        st.sidebar.markdown(
            f"""
            <div style="border-left: 2px solid #e8ebef; margin-left: 4px;
            padding-left: 16px; margin-top: 16px; position: relative;">
              <div style="position: absolute; left: -5px; top: 3px;
              width: 8px; height: 8px; border-radius: 50%;
              background: white; border: 2px solid #6653ca;"></div>
              <p style="font-size: 10px; color: #7c8390; margin: 0 0 2px 0;">
                PICKUP
              </p>
              <p style="font-size: 12px; color: #202735; margin: 0 0 14px 0; font-weight: 500;">
                {pickup}
              </p>
              <div style="position: absolute; left: -5px; bottom: 3px;
              width: 8px; height: 8px; border-radius: 2px;
              background: #202735;"></div>
              <p style="font-size: 10px; color: #7c8390; margin: 0 0 2px 0;">
                DROPOFF
              </p>
              <p style="font-size: 12px; color: #202735; margin: 0; font-weight: 500;">
                {dropoff}
              </p>
            </div>
            <p style="font-size: 11px; color: #7c8390; line-height: 1.7; margin-top: 14px;">
              {selected.get('summary', '')}
            </p>
            """,
            unsafe_allow_html=True,
        )

        if st.sidebar.button("Resolve Dispute", type="primary", use_container_width=True, key="_df_resolve_sample"):
            from pathlib import Path
            from config.settings import SAMPLES_DIR
            case_file = SAMPLES_DIR / selected["file"]
            case_data = load_case_by_file(case_file)

    else:
        # Custom dispute form
        st.sidebar.markdown(
            """
            <p style="font-size: 11px; font-weight: 600; color: #202735; margin: 0 0 10px 0;">
              File a new dispute
            </p>
            """,
            unsafe_allow_html=True,
        )

        dispute_type = st.sidebar.selectbox(
            "Dispute type",
            ["route_deviation", "no_show"],
            format_func=lambda x: "Route deviation" if x == "route_deviation" else "No-show charge",
            key="_df_dispute_type",
        )

        trip_id = st.sidebar.text_input("Trip ID", value="RIDE-CUSTOM-001", key="_df_trip_id")
        complaint = st.sidebar.text_area(
            "Complaint description",
            value="Driver took a longer route than expected.",
            height=80,
            key="_df_complaint",
        )

        col_r, col_d = st.sidebar.columns(2)
        with col_r:
            rider_id = st.text_input("Rider ID", value="R-CUST-001", key="_df_rider_id")
        with col_d:
            driver_id = st.text_input("Driver ID", value="D-CUST-001", key="_df_driver_id")

        if st.sidebar.button("Resolve Dispute", type="primary", use_container_width=True, key="_df_resolve_custom"):
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

    # ─── Footer ──────────────────────────────────────────
    st.sidebar.markdown(
        """
        <div style="border-top: 1px solid #e8ebef; margin-top: 16px; padding-top: 12px;">
          <div style="padding: 10px 12px; background: #f5f6f8; border-radius: 8px;">
            <p style="font-size: 10px; color: #7c8390; line-height: 1.5; margin: 0;">
              <span style="color: #6653ca; margin-right: 4px;">&#128737;</span>
              Balanced by design.<br>
              <span style="padding-left: 16px;">Every side heard. Every decision explained.</span>
            </p>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; padding-top: 14px;">
            <div style="width: 28px; height: 28px; border-radius: 50%;
            background: #eeeaf8; color: #6653ca;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; font-weight: 700;">
              OP
            </div>
            <span style="font-size: 11px; font-weight: 500; color: #202735;">Operations workspace</span>
            <span style="margin-left: auto; font-size: 9px; color: #7c8390;">&#9660;</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return case_data, run_mode
