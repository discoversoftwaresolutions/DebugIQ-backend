from fastapi import APIRouter
from pydantic import BaseModel
from scripts import platform_data_api
from scripts import autonomous_diagnose_issue
from scripts import agent_suggest_patch

router = APIRouter()

# --- Pydantic Models ---

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

@router.post("/workflow/triage")
def triage_issue(payload: RawIssueData):
    return {"message": "Triage endpoint stub", "data": payload.raw_data}


@router.post("/workflow/diagnose")
def diagnose_issue(issue: IssueInput):
    result = autonomous_diagnose_issue.autonomous_diagnose(issue.issue_id)
    return {"diagnosis": result}


@router.post("/suggest-patch")
def suggest_patch(issue: IssueInput):
    diagnosis = platform_data_api.get_diagnosis(issue.issue_id)
    if not diagnosis:
        return {"error": f"No diagnosis found for issue {issue.issue_id}"}
    patch_result = agent_suggest_patch.agent_suggest_patch(issue.issue_id, diagnosis)
    return {"patch": patch_result}


@router.post("/workflow/seed")
def seed_mock_issue(data: MockSeedInput):
    """
    Seeds a mock issue directly into the in-memory mock database.
    """
    from scripts.mock_db import db
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
