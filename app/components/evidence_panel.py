"""Evidence panel component: shows evidence summary in a styled card container."""

import html as _html
import textwrap

import streamlit as st

from evidence.loaders import CaseData
from graph.tools import get_route_analysis, get_fare_breakdown, get_chat_log
from app.components.route_map import get_route_map_html


def _h(s: str) -> str:
    """Strip leading indentation from HTML strings."""
    return textwrap.dedent(s).strip()


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
    """Render a summary of the evidence inside a styled container card."""
    trip_id = case.trip.get("ride_id", case.dispute.get("ride_id", ""))
    route = get_route_analysis(trip_id)
    fare = get_fare_breakdown(trip_id)
    chat = get_chat_log(trip_id)

    est_dist = case.trip.get("estimated_distance_km", 0)
    act_dist = case.trip.get("actual_distance_km", 0)
    deviation = route.get("extra_distance_pct", 0) if "error" not in route else 0
    extra_time = route.get("time_difference_min", 0) if "error" not in route else 0
    opt_traffic = route.get("traffic_optimal_congestion", "N/A") if "error" not in route else "N/A"
    act_traffic = route.get("traffic_actual_congestion", "N/A") if "error" not in route else "N/A"

    parts = []

    # ─── Container with green-tinted border ────────────
    parts.append(_h("""
        <div style="border: 1px solid rgba(29,158,117,0.18); border-radius: 12px;
        background: white; overflow: hidden; margin-bottom: 20px;">
    """))

    # ─── Header bar ────────────────────────────────────
    parts.append(_h("""
        <div style="background: #eaf6f0; padding: 16px 20px;
        border-bottom: 1px solid rgba(29,158,117,0.12);">
          <div style="display: flex; justify-content: space-between;
          align-items: center;">
            <span style="font-size: 10px; font-weight: 700;
            color: #1D9E75; letter-spacing: 0.12em;">
              <span style="margin-right: 4px;">&#128269;</span>EVIDENCE ROOM
            </span>
            <span style="font-size: 9px; color: #1D9E75;
            border: 1px solid rgba(29,158,117,0.18);
            border-radius: 4px; padding: 2px 8px;">
              Trip verified
            </span>
          </div>
        </div>
    """))

    # ─── Body ──────────────────────────────────────────
    parts.append("<div style=\"padding: 20px;\">")

    # ─── Three-column grid ─────────────────────────────
    parts.append(_h("""
        <div style="display: grid; grid-template-columns: 1.05fr 1fr 0.86fr; gap: 20px;">
    """))

    # ── Column 1: Route Map ────────────────────────────
    map_html = get_route_map_html(case)
    if map_html:
        # Escape only quotes so srcdoc doesn't break; leave HTML tags intact
        map_quoted = map_html.replace('"', '&quot;')
        parts.append(_h(f"""
            <div>
              <iframe srcdoc="{map_quoted}" width="100%" height="420"
              style="border: 1px solid #e8ebef; border-radius: 8px;"></iframe>
            </div>
        """))
    else:
        parts.append(_h("""
            <div style="display: flex; align-items: center; justify-content: center;
            height: 420px; border: 1px solid #e8ebef; border-radius: 8px;
            background: #f5f6f8;">
              <span style="font-size: 11px; color: #7c8390;">No GPS route data</span>
            </div>
        """))

    # ── Column 2: Trip metrics + Fare breakdown ────────
    col2_parts = []

    # Trip & route analysis
    col2_parts.append(_h("""
        <p style="font-size: 10px; font-weight: 700; color: #7c8390;
        letter-spacing: 0.13em; text-transform: uppercase; margin: 0 0 10px 0;">
          Trip & route analysis
        </p>
    """))

    col2_parts.append(_h(f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 10px; padding-bottom: 14px; border-bottom: 1px solid #e8ebef;">
          <div>
            <p style="font-size: 10px; color: #7c8390; margin: 0;">Est. distance</p>
            <p style="font-size: 20px; font-weight: 800; color: #202735;
            margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
              {est_dist} <span style="font-size: 10px; font-weight: 400; color: #7c8390;">km</span>
            </p>
            <p style="font-size: 10px; color: #7c8390; margin: 8px 0 0 0;">Opt. route traffic</p>
            {_traffic_tag(opt_traffic)}
          </div>
          <div>
            <p style="font-size: 10px; color: #7c8390; margin: 0;">Actual distance</p>
            <p style="font-size: 20px; font-weight: 800; color: #202735;
            margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
              {act_dist} <span style="font-size: 10px; font-weight: 400; color: #7c8390;">km</span>
            </p>
            <p style="font-size: 10px; color: #7c8390; margin: 8px 0 0 0;">Act. route traffic</p>
            {_traffic_tag(act_traffic)}
          </div>
          <div>
            <p style="font-size: 10px; color: #7c8390; margin: 0;">Deviation</p>
            <p style="font-size: 20px; font-weight: 800; color: #D85A30;
            margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
              {deviation}<span style="font-size: 12px; font-weight: 600;">%</span>
            </p>
            <p style="font-size: 10px; color: #7c8390; margin: 8px 0 0 0;">Extra time</p>
            <p style="font-size: 20px; font-weight: 800; color: #202735;
            margin: 4px 0 0 0; font-family: 'Manrope', sans-serif;">
              {extra_time} <span style="font-size: 10px; font-weight: 400; color: #7c8390;">min</span>
            </p>
          </div>
        </div>
    """))

    # Alerts
    if route.get("traffic_exception_applies"):
        col2_parts.append(_h("""
            <div style="margin-top: 10px; padding: 8px 12px;
            background: rgba(29,158,117,0.08); border-radius: 6px;">
              <span style="font-size: 11px; color: #1D9E75;">
                &#9432; Traffic exception may apply (Section 1.4).
              </span>
            </div>
        """))
    if route.get("unexpected_stops"):
        stops = len(route["unexpected_stops"])
        col2_parts.append(_h(f"""
            <div style="margin-top: 8px; padding: 8px 12px;
            background: rgba(226,75,74,0.08); border-radius: 6px;">
              <span style="font-size: 11px; color: #c43d3c;">
                &#9888; {stops} unexpected stop(s) detected.
              </span>
            </div>
        """))

    # Fare breakdown
    if "error" not in fare:
        total = fare.get("total", 0)
        col2_parts.append(_h(f"""
            <div style="background: #f5f6f8; border-radius: 8px; padding: 12px 16px;
            margin-top: 12px;">
              <div style="display: flex; justify-content: space-between;
              align-items: center; margin-bottom: 10px;">
                <span style="font-size: 12px; font-weight: 600; color: #202735;">Fare breakdown</span>
                <span style="font-size: 12px; font-weight: 700; color: #202735;">${total:.2f}</span>
              </div>
              <div style="display: flex; justify-content: space-between;
              align-items: center; padding: 5px 0;">
                <span style="font-size: 11px; font-weight: 500; color: #202735;">Base fare</span>
                <span style="font-size: 11px; font-weight: 600; color: #202735;">${fare.get('base', 0):.2f}</span>
              </div>
              <div style="display: flex; justify-content: space-between;
              align-items: center; padding: 5px 0;">
                <span style="font-size: 11px; font-weight: 500; color: #202735;">Distance &middot; Time</span>
                <span style="font-size: 11px; font-weight: 600; color: #202735;">${fare.get('distance_charge', 0):.2f} &middot; ${fare.get('time_charge', 0):.2f}</span>
              </div>
        """))
        if fare.get("overcharge_amount", 0) > 0:
            col2_parts.append(_h(f"""
                <div style="display: flex; justify-content: space-between;
                align-items: center; padding: 5px 0;">
                  <span style="font-size: 11px; font-weight: 500; color: #D85A30;">Disputed overcharge</span>
                  <span style="font-size: 11px; font-weight: 600; color: #D85A30;">${fare['overcharge_amount']:.2f}</span>
                </div>
            """))
        elif fare.get("cancellation_fee", 0) > 0:
            col2_parts.append(_h(f"""
                <div style="display: flex; justify-content: space-between;
                align-items: center; padding: 5px 0;">
                  <span style="font-size: 11px; font-weight: 500; color: #D85A30;">Cancellation fee</span>
                  <span style="font-size: 11px; font-weight: 600; color: #D85A30;">${fare['cancellation_fee']:.2f}</span>
                </div>
            """))
        col2_parts.append("</div>")

    parts.append("<div>" + "".join(col2_parts) + "</div>")

    # ── Column 3: Chat highlights + Profiles ───────────
    col3_parts = []

    col3_parts.append(_h("""
        <p style="font-size: 10px; font-weight: 700; color: #7c8390;
        letter-spacing: 0.13em; text-transform: uppercase; margin: 0 0 10px 0;">
          Chat highlights
        </p>
    """))

    if "error" not in chat and chat.get("key_exchanges"):
        for exchange in chat.get("key_exchanges", [])[:5]:
            sender = exchange.get("sender", "?")
            sentiment = exchange.get("sentiment", "neutral")
            msg = _html.escape(exchange.get("message", ""))
            color = {"rider": "#378ADD", "driver": "#D85A30", "system": "#888780"}.get(sender, "#888")
            bg = {"rider": "rgba(55,138,221,0.05)", "driver": "rgba(216,90,48,0.05)", "system": "#f5f6f8"}.get(sender, "#f5f6f8")
            col3_parts.append(_h(f"""
                <div style="background: {bg}; border-left: 2px solid {color};
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
                </div>
            """))
    else:
        col3_parts.append(_h("""
            <div style="padding: 12px; background: #f5f6f8; border-radius: 6px;">
              <span style="font-size: 11px; color: #7c8390;">No chat highlights available.</span>
            </div>
        """))

    # Profiles
    rp = case.rider_profile
    dp = case.driver_profile
    r_initials = f"{rp.get('name', 'R')[0]}{rp.get('name', ' ').split(' ')[-1][0] if ' ' in rp.get('name', '') else ''}"
    d_initials = f"{dp.get('name', 'D')[0]}{dp.get('name', ' ').split(' ')[-1][0] if ' ' in dp.get('name', '') else ''}"

    col3_parts.append(_h(f"""
        <div style="border-top: 1px solid #e8ebef; margin-top: 12px; padding-top: 12px;
        display: flex; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 28px; height: 28px; border-radius: 8px;
            background: rgba(55,138,221,0.1); color: #378ADD;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; font-weight: 700;">
              {r_initials}
            </div>
            <div>
              <p style="font-size: 11px; font-weight: 600; color: #202735; margin: 0;">
                {_html.escape(rp.get('name', 'N/A'))}
              </p>
              <p style="font-size: 9px; color: #7c8390; margin: 1px 0 0 0;">
                Rider &middot; {rp.get('rating', 'N/A')}/5.0
              </p>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 28px; height: 28px; border-radius: 8px;
            background: rgba(216,90,48,0.1); color: #D85A30;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; font-weight: 700;">
              {d_initials}
            </div>
            <div>
              <p style="font-size: 11px; font-weight: 600; color: #202735; margin: 0;">
                {_html.escape(dp.get('name', 'N/A'))}
              </p>
              <p style="font-size: 9px; color: #7c8390; margin: 1px 0 0 0;">
                Driver &middot; {dp.get('rating', 'N/A')}/5.0
              </p>
            </div>
          </div>
        </div>
    """))

    parts.append("<div>" + "".join(col3_parts) + "</div>")

    # ─── Close grid + container ────────────────────────
    parts.append("</div></div></div>")

    # Render everything in one call
    st.markdown("".join(parts), unsafe_allow_html=True)
