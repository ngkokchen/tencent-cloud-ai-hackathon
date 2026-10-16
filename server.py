"""
FastAPI server: serves the dispute resolution UI and exposes the
agent pipeline as JSON API endpoints.

Run:  python server.py
Then: open http://localhost:8000
"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from evidence.loaders import load_case_by_file, list_available_cases
from graph.tools import (
    get_route_analysis,
    get_chat_log,
    get_fare_breakdown,
    get_user_history,
    get_policy,
)
from graph.orchestrator import run_demo_resolution
from models.message import ConversationLog

app = FastAPI(title="Ryde Dispute Resolver")

PROJECT_ROOT = Path(__file__).resolve().parent
HTML_FILE = PROJECT_ROOT / "ui-design-draft.html"
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"


class ResolveRequest(BaseModel):
    file: str


@app.get("/")
def serve_ui():
    return FileResponse(str(HTML_FILE))


@app.get("/api/cases")
def get_cases():
    cases = list_available_cases()
    return {"cases": cases}


@app.post("/api/resolve")
def resolve_dispute(req: ResolveRequest):
    file_path = SAMPLES_DIR / req.file
    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"Case file '{req.file}' not found"},
        )

    case_data = load_case_by_file(file_path)

    trip_id = case_data.trip.get("ride_id", case_data.dispute.get("ride_id", ""))
    rider_id = case_data.rider_profile.get("rider_id", "")
    driver_id = case_data.driver_profile.get("driver_id", "")
    dispute_type = case_data.dispute.get("dispute_type", "")

    route = get_route_analysis(trip_id)
    chat = get_chat_log(trip_id)
    fare = get_fare_breakdown(trip_id)
    rider_hist = get_user_history(rider_id)
    driver_hist = get_user_history(driver_id)
    policy = get_policy(dispute_type)

    log = ConversationLog()
    ruling, rider_arg, driver_arg, rider_reb, driver_reb = run_demo_resolution(
        case_data, log, delay=0
    )

    messages = [m.model_dump(mode="json") for m in log.messages]

    response = {
        "messages": messages,
        "ruling": ruling.model_dump(mode="json"),
        "rider_argument": rider_arg.model_dump(mode="json"),
        "driver_argument": driver_arg.model_dump(mode="json"),
        "rider_rebuttal": rider_reb.model_dump(mode="json"),
        "driver_rebuttal": driver_reb.model_dump(mode="json"),
        "evidence": {
            "route": route,
            "chat": chat,
            "fare": fare,
            "rider_history": rider_hist,
            "driver_history": driver_hist,
            "routes": {
                "optimal": case_data.trip.get("optimal_route", []),
                "actual": case_data.trip.get("actual_route", []),
                "driver_gps_at_pickup": case_data.raw.get("driver_gps_at_pickup", []),
                "rider_gps_at_pickup": case_data.raw.get("rider_gps_at_pickup", []),
            },
        },
        "case": {
            "dispute_id": case_data.dispute.get("dispute_id", ""),
            "dispute_type": dispute_type,
            "ride_id": trip_id,
            "pickup_address": case_data.trip.get("pickup", {}).get("address", ""),
            "dropoff_address": case_data.trip.get("dropoff", {}).get("address", ""),
            "filed_at": case_data.dispute.get("filed_at", ""),
            "claim": case_data.dispute.get("claim", ""),
            "rider_name": case_data.rider_profile.get("name", ""),
            "driver_name": case_data.driver_profile.get("name", ""),
            "rider_id": rider_id,
            "driver_id": driver_id,
            "estimated_distance_km": case_data.trip.get("estimated_distance_km", 0),
            "actual_distance_km": case_data.trip.get("actual_distance_km", 0),
            "estimated_duration_min": case_data.trip.get("estimated_duration_min", 0),
            "actual_duration_min": case_data.trip.get("actual_duration_min", 0),
            "driver_wait_time_min": case_data.trip.get("driver_wait_time_min", 0),
            "rider_distance_from_pickup_m": case_data.raw.get(
                "rider_distance_from_pickup_m", None
            ),
        },
    }

    return JSONResponse(content=jsonable_encoder(response))


if __name__ == "__main__":
    import os
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )
