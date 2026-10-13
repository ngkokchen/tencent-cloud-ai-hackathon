"""Case loaders: find and load sample dispute JSON files by ride_id or user_id."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config.settings import SAMPLES_DIR


@dataclass
class CaseData:
    """Structured access to a loaded dispute case."""
    dispute: dict
    trip: dict
    chat_logs: list
    fare_breakdown: dict
    rider_profile: dict
    driver_profile: dict
    raw: dict
    file_path: str


def _load_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_case_by_file(file_path: str | Path) -> CaseData:
    """Load a case from a specific JSON file path."""
    data = _load_json(file_path)
    return CaseData(
        dispute=data.get("dispute", {}),
        trip=data.get("trip", {}),
        chat_logs=data.get("chat_logs", []),
        fare_breakdown=data.get("fare_breakdown", {}),
        rider_profile=data.get("rider_profile", {}),
        driver_profile=data.get("driver_profile", {}),
        raw=data,
        file_path=str(file_path),
    )


def _scan_samples() -> dict:
    """
    Build an index mapping ride_id, rider_id, and driver_id to file paths
    by scanning all sample JSON files.
    """
    index: dict[str, str] = {}
    if not SAMPLES_DIR.exists():
        return index
    for f in SAMPLES_DIR.glob("*.json"):
        if f.name == "index.json":
            continue
        try:
            data = _load_json(f)
        except (json.JSONDecodeError, OSError):
            continue
        # Index by ride_id
        ride_id = data.get("trip", {}).get("ride_id") or data.get("dispute", {}).get("ride_id")
        if ride_id:
            index[ride_id] = str(f)
        # Index by rider_id
        rider_id = data.get("rider_profile", {}).get("rider_id")
        if rider_id:
            index[rider_id] = str(f)
        # Index by driver_id
        driver_id = data.get("driver_profile", {}).get("driver_id")
        if driver_id:
            index[driver_id] = str(f)
    return index


_CASE_INDEX: dict | None = None


def _get_case_index() -> dict:
    global _CASE_INDEX
    if _CASE_INDEX is None:
        _CASE_INDEX = _scan_samples()
    return _CASE_INDEX


def load_case_by_ride_id(ride_id: str) -> Optional[CaseData]:
    """Find and load a case by its ride_id (e.g. 'RIDE-7821')."""
    idx = _get_case_index()
    file_path = idx.get(ride_id)
    if file_path is None:
        return None
    return load_case_by_file(file_path)


def load_case_by_user_id(user_id: str) -> Optional[CaseData]:
    """Find and load a case by rider_id or driver_id (e.g. 'R-8821', 'D-3401')."""
    idx = _get_case_index()
    file_path = idx.get(user_id)
    if file_path is None:
        return None
    return load_case_by_file(file_path)


def list_available_cases() -> list[dict]:
    """Load the sample index and return case summaries for UI display."""
    index_path = SAMPLES_DIR / "index.json"
    if index_path.exists():
        return _load_json(index_path).get("cases", [])
    return []
