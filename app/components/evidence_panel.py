"""Evidence panel component: shows evidence summary from the dispute."""

import streamlit as st

from evidence.loaders import CaseData
from graph.tools import get_route_analysis, get_fare_breakdown
from app.components.route_map import render_route_map


def _traffic_tag(traffic: str) -> str:
    """Return an HTML severity tag for traffic level."""
    level = traffic.lower().strip()
    if level in ("light", "low", "clear"):
        return (
            f'<span style="display: inline-block; background: rgba(29,158,117,0.12); '
            f'color: #1D9E75; font-size: 10px; font-weight: 600; padding: 2px 8px; '
            f'border-radius: 4px; margin-top: 4px;">{traffic}</span>'
        )
    elif level in ("moderate", "medium"):
        return (
            f'<span style="display: inline-block; background: rgba(239,159,39,0.12); '
            f'color: #c78a1c; font-size: 10px; font-weight: 600; padding: 2px 8px; '
            f'border-radius: 4px; margin-top: 4px;">{traffic}</span>'
        )
    elif level in ("heavy", "high", "severe"):
        return (
            f'<span style="display: inline-block; background: rgba(226,75,74,0.12); '
            f'color: #c43d3c; font-size: 10px; font-weight: 600; padding: 2px 8px; '
            f'border-radius: 4px; margin-top: 4px;">{traffic}</span>'
        )
    return (
        f'<span style="display: inline-block; background: #f5f6f8; '
        f'color: #7c8390; font-size: 10px; font-weight: 600; padding: 2px 8px; '
        f'border-radius: 4px; margin-top: 4px;">{traffic}</span>'
    )


def render_evidence_panel(case: CaseData) -> None:
    """Render a summary of the evidence for the dispute in a card container."""
    trip_id = case.trip.get("ride_id", case.dispute.get("ride_id", ""))

    # ─── Evidence Room container ─────────────────────────
    st.markdown(
        """
        <div style="border: 1px solid #e8ebef; border-radius: 12px;
        background: white; margin-bottom: 20px; overflow: hidden;">
          <div style="padding: 14px 20px; border-bottom: 1px solid #e8ebef;
          display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 13px; font-weight: 700; color: #202735;
            font-family: 'Manrope', sans-serif;">
              <span style="margin-right: 8px;">&#128451;</span>Evidence room
            </span>
            <span style="font-size: 10px; color: #7c8390;">
              Trip #{}</span>
          </div>
          <div style="padding: 16px 20px;">
        """.format(trip_id),
        unsafe_allow_html=True,
    )

    # ─── Three-column grid: Map | Metrics | Chat ─────────
    col_map, col_metrics, col_chat = st.columns([1.05, 1, 0.86])

    # ── Column 1: Route Map ─────────────────────────────
    with col_map:
        if case.trip.get("optimal_route") or case.trip.get("actual_route"):
            render_route_map(case)

        # Map legend (optimal vs actual)
        st.markdown(
            """
            <div style="display: flex; gap: 16px; margin-top: 10px;
            font-size: 10px; color: #7c8390;">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span style="width: 14px; height: 3px; background: #6653ca;
                border-radius: 2px;"></span>
                <span>Optimal route</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px;">
                <span style="width: 14px; height: 3px; background: #b0a3d9;
                border-radius: 2px;"></span>
                <span>Actual route</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Column 2: Trip & route analysis + Fare breakdown ─
    with col_metrics:
        route = get_route_analysis(trip_id)
        fare = get_fare_breakdown(trip_id)

        est_dist = case.trip.get("estimated_distance_km", 0)
        act_dist = case.trip.get("actual_distance_km", 0)
        deviation = route.get("extra_distance_pct", 0) if "error" not in route else 0
        extra_time = route.get("time_difference_min", 0) if "error" not in route else 0
        opt_traffic = route.get("traffic_optimal_congestion", "N/A") if "error" not in route else "N/A"
        act_traffic = route.get("traffic_actual_congestion", "N/A") if "error" not in route else "N/A"

        st.markdown(
            """
            <p style="font-size: 10px; font-weight: 700; color: #7c8390;
            letter-spacing: 0.13em; text-transform: uppercase; margin: 0 0 10px 0;">
              Trip & route analysis
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 10px; padding-bottom: 14px; border-bottom: 1px solid #e8ebef;">
              <div>
                <p style="font-size: 10px; color: #7c8390; margin: 0;">Est. distance</p>
                <p style="font-size: 20px; font-weight: 800; color: #202735;
                margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
                  {est_dist} <span style="font-size: 10px; font-weight: 400; color: #7c8390;">km</span>
                </p>
                <p style="font-size: 10px; color: #7c8390; margin: 8px 0 0 0;">
                  Opt. route traffic
                </p>
                {_traffic_tag(opt_traffic)}
              </div>
              <div>
                <p style="font-size: 10px; color: #7c8390; margin: 0;">Actual distance</p>
                <p style="font-size: 20px; font-weight: 800; color: #202735;
                margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
                  {act_dist} <span style="font-size: 10px; font-weight: 400; color: #7c8390;">km</span>
                </p>
                <p style="font-size: 10px; color: #7c8390; margin: 8px 0 0 0;">
                  Act. route traffic
                </p>
                {_traffic_tag(act_traffic)}
              </div>
              <div>
                <p style="font-size: 10px; color: #7c8390; margin: 0;">Deviation</p>
                <p style="font-size: 20px; font-weight: 800; color: #D85A30;
                margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
                  {deviation}<span style="font-size: 12px; font-weight: 600;">%</span>
                </p>
                <p style="font-size: 10px; color: #7c8390; margin: 8px 0 0 0;">
                  Extra time
                </p>
                <p style="font-size: 20px; font-weight: 800; color: #202735;
                margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
                  {extra_time} <span style="font-size: 10px; font-weight: 400; color: #7c8390;">min</span>
                </p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if route.get("traffic_exception_applies"):
            st.info("Traffic exception may apply (Section 1.4).")
        if route.get("unexpected_stops"):
            st.warning(f"{len(route['unexpected_stops'])} unexpected stop(s) detected.")

        # ─── Fare breakdown ──────────────────────────────
        if "error" not in fare:
            st.markdown(
                """
                <div style="background: #f5f6f8; border-radius: 8px; padding: 12px 16px;
                margin-top: 12px;">
                  <div style="display: flex; justify-content: space-between;
                  align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 12px; font-weight: 600; color: #202735;">
                      Fare breakdown
                    </span>
                    <span style="font-size: 12px; font-weight: 700; color: #202735;">
                      ${:.2f}
                    </span>
                  </div>
                  <div style="display: grid; grid-template-columns: 1fr auto;
                  gap: 6px 16px; font-size: 11px; color: #7c8390;">
                """.format(fare.get("total", 0)),
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <span>Base fare</span>
                <span style="text-align: right;">${fare.get('base', 0):.2f}</span>
                <span>Distance &middot; Time</span>
                <span style="text-align: right;">${fare.get('distance_charge', 0):.2f} &middot; ${fare.get('time_charge', 0):.2f}</span>
                """,
                unsafe_allow_html=True,
            )
            if fare.get("overcharge_amount", 0) > 0:
                st.markdown(
                    f"""
                    <span style="color: #D85A30; font-weight: 500;">Disputed overcharge</span>
                    <span style="text-align: right; color: #D85A30; font-weight: 600;">
                      ${fare['overcharge_amount']:.2f}
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
            elif fare.get("cancellation_fee", 0) > 0:
                st.markdown(
                    f"""
                    <span style="color: #D85A30; font-weight: 500;">Cancellation fee</span>
                    <span style="text-align: right; color: #D85A30; font-weight: 600;">
                      ${fare['cancellation_fee']:.2f}
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Column 3: Chat highlights + Profiles ────────────
    with col_chat:
        st.markdown(
            """
            <p style="font-size: 10px; font-weight: 700; color: #7c8390;
            letter-spacing: 0.13em; text-transform: uppercase; margin: 0 0 10px 0;">
              Chat highlights
            </p>
            """,
            unsafe_allow_html=True,
        )

        from graph.tools import get_chat_log
        chat = get_chat_log(trip_id)
        if "error" not in chat and chat.get("key_exchanges"):
            for exchange in chat.get("key_exchanges", [])[:5]:
                sender = exchange.get("sender", "?")
                sentiment = exchange.get("sentiment", "neutral")
                msg = exchange.get("message", "")
                color = {"rider": "#378ADD", "driver": "#D85A30", "system": "#888780"}.get(
                    sender, "#888"
                )
                bg = {"rider": "rgba(55,138,221,0.05)", "driver": "rgba(216,90,48,0.05)", "system": "#f5f6f8"}.get(
                    sender, "#f5f6f8"
                )
                st.markdown(
                    f"""<div style="background: {bg}; border-left: 2px solid {color};
                    padding: 6px 10px; margin: 6px 0; border-radius: 0 6px 6px 0;">
                    <div style="display: flex; justify-content: space-between;
                    align-items: center;">
                      <span style="font-size: 10px; color: {color}; font-weight: 600;">
                        {sender.title()}
                      </span>
                      <span style="font-size: 9px; color: #7c8390;">
                        {sentiment.title()} &middot; {exchange.get('time', '')}
                      </span>
                    </div>
                    <div style="font-size: 11px; color: #202735; margin-top: 3px; line-height: 1.4;">
                      {msg}
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # ─── Profiles ────────────────────────────────────
        st.markdown(
            """
            <div style="border-top: 1px solid #e8ebef; margin-top: 12px; padding-top: 12px;
            display: flex; gap: 16px;">
            """,
            unsafe_allow_html=True,
        )

        rp = case.rider_profile
        dp = case.driver_profile

        st.markdown(
            f"""<div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 28px; height: 28px; border-radius: 8px;
              background: rgba(55,138,221,0.1); color: #378ADD;
              display: flex; align-items: center; justify-content: center;
              font-size: 10px; font-weight: 700;">
                {rp.get('name', 'R')[0]}{rp.get('name', ' ').split(' ')[-1][0] if ' ' in rp.get('name', '') else ''}
              </div>
              <div>
                <p style="font-size: 11px; font-weight: 600; color: #202735; margin: 0;">
                  {rp.get('name', 'N/A')}
                </p>
                <p style="font-size: 9px; color: #7c8390; margin: 1px 0 0 0;">
                  Rider &middot; {rp.get('rating', 'N/A')}/5.0
                </p>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""<div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 28px; height: 28px; border-radius: 8px;
              background: rgba(216,90,48,0.1); color: #D85A30;
              display: flex; align-items: center; justify-content: center;
              font-size: 10px; font-weight: 700;">
                {dp.get('name', 'D')[0]}{dp.get('name', ' ').split(' ')[-1][0] if ' ' in dp.get('name', '') else ''}
              </div>
              <div>
                <p style="font-size: 11px; font-weight: 600; color: #202735; margin: 0;">
                  {dp.get('name', 'N/A')}
                </p>
                <p style="font-size: 9px; color: #7c8390; margin: 1px 0 0 0;">
                  Driver &middot; {dp.get('rating', 'N/A')}/5.0
                </p>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Close the Evidence Room container
    st.markdown("</div></div>", unsafe_allow_html=True)
