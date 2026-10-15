"""Route map component: renders actual vs optimal GPS routes on an interactive map."""

import html as _html

import folium
import streamlit as st
from streamlit_folium import st_folium

from evidence.loaders import CaseData


# Colors for route lines
OPTIMAL_COLOR = "#1D9E75"   # green — the expected route
ACTUAL_COLOR = "#E24B4A"     # red — the actual (possibly deviated) route
PICKUP_COLOR = "#378ADD"     # blue — pickup marker
DROPOFF_COLOR = "#534AB7"    # purple — dropoff marker


def _build_map(case: CaseData) -> folium.Map | None:
    """Build a Folium map object from case data. Returns None if no GPS data."""
    trip = case.trip
    optimal_route = trip.get("optimal_route", [])
    actual_route = trip.get("actual_route", [])
    pickup = trip.get("pickup", {})
    dropoff = trip.get("dropoff", {})

    if not optimal_route and not actual_route:
        return None

    all_points = (
        [(p["lat"], p["lng"]) for p in optimal_route]
        + [(p["lat"], p["lng"]) for p in actual_route]
    )
    if not all_points:
        return None

    center_lat = sum(p[0] for p in all_points) / len(all_points)
    center_lng = sum(p[1] for p in all_points) / len(all_points)

    m = folium.Map(location=[center_lat, center_lng], zoom_start=13, tiles="OpenStreetMap")

    if optimal_route:
        folium.PolyLine(
            [(p["lat"], p["lng"]) for p in optimal_route],
            color=OPTIMAL_COLOR, weight=4, opacity=0.7,
            dashArray="10, 5", tooltip="Optimal route",
        ).add_to(m)

    if actual_route:
        folium.PolyLine(
            [(p["lat"], p["lng"]) for p in actual_route],
            color=ACTUAL_COLOR, weight=5, opacity=0.85,
            tooltip="Actual route",
        ).add_to(m)

    if pickup and "lat" in pickup:
        folium.CircleMarker(
            location=[pickup["lat"], pickup["lng"]],
            radius=8, color=PICKUP_COLOR, fill=True,
            fillColor=PICKUP_COLOR, fillOpacity=0.9,
            tooltip=f"Pickup: {pickup.get('address', 'N/A')}",
        ).add_to(m)

    if dropoff and "lat" in dropoff:
        folium.CircleMarker(
            location=[dropoff["lat"], dropoff["lng"]],
            radius=8, color=DROPOFF_COLOR, fill=True,
            fillColor=DROPOFF_COLOR, fillOpacity=0.9,
            tooltip=f"Dropoff: {dropoff.get('address', 'N/A')}",
        ).add_to(m)

    for p in actual_route:
        if p.get("note"):
            folium.CircleMarker(
                location=[p["lat"], p["lng"]],
                radius=3, color=ACTUAL_COLOR, fill=True,
                fillColor=ACTUAL_COLOR, fillOpacity=0.5,
                tooltip=f"Actual: {p['note']}",
            ).add_to(m)

    sw = [min(p[0] for p in all_points), min(p[1] for p in all_points)]
    ne = [max(p[0] for p in all_points), max(p[1] for p in all_points)]
    m.fit_bounds([sw, ne], padding=(30, 30))

    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 10px 14px; border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2); font-size: 13px;">
      <div style="margin-bottom: 4px;">
        <span style="color: #1D9E75; font-weight: 600;">--- green dashed ---</span>
        Optimal route
      </div>
      <div>
        <span style="color: #E24B4A; font-weight: 600;">&mdash; red solid &mdash;</span>
        Actual route
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


def get_route_map_html(case: CaseData) -> str | None:
    """Return the Folium map as an HTML string suitable for iframe srcdoc."""
    m = _build_map(case)
    if m is None:
        return None
    return m._repr_html_()


def render_route_map(case: CaseData) -> None:
    """Render an interactive folium map in Streamlit."""
    m = _build_map(case)
    if m is None:
        st.info("No GPS route data available for this case.")
        return
    st_folium(m, height=420, returned_objects=[])
