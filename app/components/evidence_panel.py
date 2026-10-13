"""Evidence panel component: shows evidence summary from the dispute."""

import streamlit as st

from evidence.loaders import CaseData
from graph.tools import get_route_analysis, get_fare_breakdown
from app.components.route_map import render_route_map


def render_evidence_panel(case: CaseData) -> None:
    """Render a summary of the evidence for the dispute."""
    st.markdown("### Evidence summary")

    trip_id = case.trip.get("ride_id", case.dispute.get("ride_id", ""))

    # ─── Route map ──────────────────────────────────────
    if case.trip.get("optimal_route") or case.trip.get("actual_route"):
        st.markdown("#### Route visualization")
        render_route_map(case)

    # ─── Trip overview ───────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pickup = case.trip.get("pickup", {})
        st.metric("Pickup", pickup.get("address", "N/A")[:20])

    with col2:
        dropoff = case.trip.get("dropoff", {})
        st.metric("Dropoff", dropoff.get("address", "N/A")[:20])

    with col3:
        st.metric("Est. distance", f"{case.trip.get('estimated_distance_km', 0)} km")

    with col4:
        st.metric("Actual distance", f"{case.trip.get('actual_distance_km', 0)} km")

    st.markdown("---")

    # ─── Route analysis ──────────────────────────────────
    route = get_route_analysis(trip_id)
    if "error" not in route:
        st.markdown("#### Route analysis")
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            cat = route.get("deviation_category", "N/A")
            st.metric("Deviation", f"{route.get('extra_distance_pct', 0)}%", cat)
        with rc2:
            st.metric("Extra time", f"+{route.get('time_difference_min', 0)} min")
        with rc3:
            traffic = route.get("traffic_optimal_congestion", "N/A")
            st.metric("Optimal route traffic", traffic)

        if route.get("traffic_exception_applies"):
            st.info("Traffic exception may apply (Section 1.4).")
        if route.get("unexpected_stops"):
            st.warning(f"{len(route['unexpected_stops'])} unexpected stop(s) detected.")

    # ─── Fare breakdown ──────────────────────────────────
    fare = get_fare_breakdown(trip_id)
    if "error" not in fare:
        st.markdown("#### Fare breakdown")
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            st.metric("Total fare", f"${fare.get('total', 0):.2f}")
        with fc2:
            st.metric("Distance charge", f"${fare.get('distance_charge', 0):.2f}")
        with fc3:
            st.metric("Time charge", f"${fare.get('time_charge', 0):.2f}")
        with fc4:
            if fare.get("overcharge_amount", 0) > 0:
                st.metric("Overcharge", f"${fare['overcharge_amount']:.2f}")
            elif fare.get("cancellation_fee", 0) > 0:
                st.metric("Cancellation fee", f"${fare['cancellation_fee']:.2f}")
            else:
                st.metric("Surge", f"{fare.get('surge_multiplier', 1.0)}x")

    # ─── Chat highlights ─────────────────────────────────
    if case.chat_logs:
        st.markdown("#### Chat log highlights")
        from graph.tools import get_chat_log
        chat = get_chat_log(trip_id)
        if "error" not in chat:
            for exchange in chat.get("key_exchanges", [])[:5]:
                sender = exchange.get("sender", "?")
                sentiment = exchange.get("sentiment", "neutral")
                msg = exchange.get("message", "")
                color = {"rider": "#378ADD", "driver": "#D85A30", "system": "#888780"}.get(sender, "#888")
                st.markdown(
                    f'<div style="border-left: 2px solid {color}; padding-left: 10px; '
                    f'margin: 4px 0;"><span style="font-size:12px;color:{color};'
                    f'font-weight:500;">{sender}</span> '
                    f'<span style="font-size:11px;color:#888;">[{sentiment}]</span>'
                    f'<div style="font-size:13px;">{msg}</div></div>',
                    unsafe_allow_html=True,
                )

    # ─── Profiles ────────────────────────────────────────
    st.markdown("#### Profiles")
    pc1, pc2 = st.columns(2)

    with pc1:
        rp = case.rider_profile
        st.markdown(f"**Rider:** {rp.get('name', 'N/A')} ({rp.get('rider_id', 'N/A')})")
        st.markdown(f"Rating: {rp.get('rating', 'N/A')}/5.0 &middot; "
                    f"Rides: {rp.get('total_rides', 'N/A')} &middot; "
                    f"Disputes: {len(rp.get('past_disputes', []))}")

    with pc2:
        dp = case.driver_profile
        st.markdown(f"**Driver:** {dp.get('name', 'N/A')} ({dp.get('driver_id', 'N/A')})")
        st.markdown(f"Rating: {dp.get('rating', 'N/A')}/5.0 &middot; "
                    f"Rides: {dp.get('total_rides', 'N/A')} &middot; "
                    f"Completion: {dp.get('completion_rate', 0)*100:.0f}%")
