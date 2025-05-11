from fastapi import APIRouter
from datetime import datetime
from scripts.mock_db import db

router = APIRouter()

# Simulated in-memory agent usage metrics
METRIC_STATE = {
    "agent_calls": {
        "diagnose": 0,
        "patch": 0,
        "validate": 0,
    },
    "workflow_status": {
        "Diagnosing": 0,
        "Patch Suggested": 0,
        "Patch Validated": 0,
        "PR Created": 0,
        "Failed": 0
    },
    "last_updated": datetime.utcnow().isoformat()
}

@router.get("/metrics/status")
def get_system_metrics():
    # Update timestamp
    METRIC_STATE["last_updated"] = datetime.utcnow().isoformat()

    # Live count of open issues
    METRIC_STATE["issue_count"] = len(db)

    # Re-scan current statuses in mock DB
    for status_key in METRIC_STATE["workflow_status"]:
        METRIC_STATE["workflow_status"][status_key] = 0

    for issue in db.values():
        status = issue.get("status")
        if status in METRIC_STATE["workflow_status"]:
            METRIC_STATE["workflow_status"][status] += 1

    return METRIC_STATE


# Optional: incrementor used by other modules (import & call this)
def increment_agent_call(task: str):
    if task in METRIC_STATE["agent_calls"]:
        METRIC_STATE["agent_calls"][task] += 1
