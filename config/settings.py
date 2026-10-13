"""Project configuration: paths, fare rates, policy thresholds."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
POLICY_FILE = DATA_DIR / "policies" / "ryde_policy.md"
SAMPLES_DIR = DATA_DIR / "samples"
SAMPLE_INDEX = SAMPLES_DIR / "index.json"

# Fare rates (must match sample data)
BASE_FARE = 3.50
DISTANCE_RATE_PER_KM = 0.75
TIME_RATE_PER_MIN = 0.15
NO_SHOW_FEE = 5.00

# Route deviation thresholds — policy Section 1.3
DEVIATION_TOLERANCE_PCT = 10.0       # 0-10%: no refund
DEVIATION_MINOR_PCT = 15.0            # 10-15%: minor (refund if no communication)
DEVIATION_SIGNIFICANT_PCT = 30.0      # 15-30%: significant (full refund)
                                       # >30%: major (refund + 50% goodwill)

# Traffic exception — policy Section 1.4
TRAFFIC_EXCEPTION_SPEED_KMH = 20.0     # optimal route avg speed below this = heavy
TRAFFIC_EXCEPTION_MAX_DEVIATION_PCT = 15.0

# No-show rules — policy Section 2.3, 2.5
NO_SHOW_MIN_WAIT_MIN = 5.0
NO_SHOW_PICKUP_RADIUS_M = 50.0

# Surge anomaly threshold
SURGE_ANOMALY_THRESHOLD = 1.5

# Unexpected stop detection
STOP_RADIUS_M = 10.0       # movement < 10m = stationary
STOP_MIN_DURATION_S = 30   # stationary for 30s+ = a stop
