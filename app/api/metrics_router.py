# backend/app/api/metrics_router.py

from fastapi import APIRouter, HTTPException # Import HTTPException for error handling
from datetime import datetime
from scripts.mock_db import db # Assuming mock_db has the in-memory 'db' dictionary
import logging # Import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router WITHOUT a prefix. The prefix is applied in main.py (or not, in this case).
# Since main.py includes this router without a prefix, paths here must be the full paths (e.g., /metrics/...).
router = APIRouter(tags=["Metrics"]) # Added tags for clarity


# Simulated in-memory agent usage metrics
# Use underscores for variable names based on Python conventions
METRIC_STATE = {
    "agent_calls": {
        "diagnose": 0,
        "patch": 0,
        "validate": 0,
    },
    "workflow_status_counts": { # Renamed for clarity
        "Seeded": 0, # Added Seeded status from autonomous_router seed endpoint
        "Fetching Details": 0,
        "Diagnosis in Progress": 0,
        "Diagnosis Complete": 0,
        "Patch Suggestion in Progress": 0,
        "Patch Suggestion Complete": 0,
        "Patch Validation in Progress": 0,
        "Patch Validated": 0,
        "PR Creation in Progress": 0,
        "PR Created - Awaiting Review/QA": 0, # Final success status
        "Workflow Failed": 0 # Final failed status
    },
    "last_updated_utc": datetime.utcnow().isoformat() # Renamed for clarity
}
# Align the keys with the exact status strings used in your autonomous_router and frontend


@router.get("/metrics/status") # Define the full path
# Keep it synchronous as the operations are non-blocking in-memory lookups
def get_system_metrics():
    """
    Retrieves current system and agent usage metrics.
    """
    logger.info("Received request for /metrics/status.")
    try:
        # Update timestamp
        METRIC_STATE["last_updated_utc"] = datetime.utcnow().isoformat()

        # Live count of open issues
        METRIC_STATE["issue_count"] = len(db) # Assuming 'db' is accessible here

        # Re-scan current statuses in mock DB (Assuming 'db' contains issue objects with a 'status' key)
        # Reset counts before recounting
        for status_key in METRIC_STATE["workflow_status_counts"]:
            METRIC_STATE["workflow_status_counts"][status_key] = 0

        # Count issues by their current status found in the mock DB
        for issue in db.values():
            status = issue.get("status") # Use .get for safety
            if status in METRIC_STATE["workflow_status_counts"]:
                METRIC_STATE["workflow_status_counts"][status] += 1
            else:
                 # Log if we encounter a status not expected/tracked
                 logger.warning(f"Encountered untracked issue status in DB: {status}")


        logger.info("Successfully gathered system metrics.")
        return METRIC_STATE

    except Exception as e:
        # Catch any unexpected errors during metrics gathering
        logger.error(f"Failed to get system metrics: {e}", exc_info=True) # Use logger
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system metrics: {e}") # Use HTTPException


# Optional: incrementor used by other modules (import & call this function)
# This function updates the in-memory metrics state.
# It should be thread-safe if called concurrently from multiple requests.
# Using a simple dictionary isn't thread-safe, consider using a lock or a thread-safe counter/queue.
def increment_agent_call(task: str):
    """
    Increments the count for a specific agent task call.
    NOTE: This in-memory update is NOT thread-safe if called concurrently.
    """
    if task in METRIC_STATE["agent_calls"]:
        METRIC_STATE["agent_calls"][task] += 1
        logger.debug(f"Incremented agent call metric for task: {task}. New count: {METRIC_STATE['agent_calls'][task]}")
    else:
        logger.warning(f"Attempted to increment unknown agent call task metric: {task}")

# Note: This file defines the metrics router. It should be included in main.py
# using app.include_router(router, tags=["Metrics"]).
