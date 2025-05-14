from fastapi import APIRouter
from pydantic import BaseModel
from scripts import platform_data_api
from scripts import autonomous_diagnose_issue
# Removed: from scripts.agent_suggest_patch import agent_suggest_patch # Endpoint moved

router = APIRouter()

# --- Pydantic Models ---
# Keep all models
class IssueInput(BaseModel):
    issue_id: str

class PatchInput(BaseModel):
    issue_id: str
    patch_diff_content: str

class RawIssueData(BaseModel):
    raw_data: dict

class MockSeedInput(BaseModel):
    issue_id: str
    title: str
    description: str
    error_message: str
    logs: str
    relevant_files: list[str]
    repository: str


# --- ROUTES ---
# Removed /workflow prefix
@router.post("/triage") # Final path will be /workflow/triage
def triage_issue(payload: RawIssueData):
    return {"message": "Triage endpoint stub", "data": payload.raw_data}

# Renamed path to match frontend call and removed /workflow prefix
@router.post("/run_autonomous_workflow") # Final path will be /workflow/run_autonomous_workflow
def diagnose_issue(issue: IssueInput): # Function name can remain diagnose_issue if it performs diagnosis
    """
    Endpoint triggered by the frontend to start the autonomous workflow.
    Calls the diagnosis logic.
    """
    result = autonomous_diagnose_issue.autonomous_diagnose(issue.issue_id)
    return {"diagnosis": result}

# Removed: @router.post("/suggest-patch") and def suggest_patch function - MOVED TO agent_suggest_patch.py

# Removed /workflow prefix
@router.post("/seed") # Final path will be /workflow/seed
def seed_mock_issue(data: MockSeedInput):
    """
    Seeds a mock issue directly into the in-memory mock database.
    """
    from scripts.mock_db import db # Keep local import
    db[data.issue_id] = {
        "id": data.issue_id,
        "title": data.title,
        "description": data.description,
        "error_message": data.error_message,
        "logs": data.logs,
        "relevant_files": data.relevant_files,
        "repository": data.repository,
        "status": "Seeded"
    }
    return {"message": f"Issue {data.issue_id} seeded successfully."}

# Added /check endpoint based on frontend call GET /workflow/check
@router.get("/check") # Final path will be /workflow/check
def workflow_check():
    """
    Placeholder endpoint for workflow integrity check.
    """
    # Placeholder implementation - replace with actual logic
    return {"status": "ok", "message": "Workflow check endpoint stub"}

# NOTE: You might also need other endpoints like /status, /cancel, etc. in this router
# if they are part of the autonomous workflow and called by the frontend.
