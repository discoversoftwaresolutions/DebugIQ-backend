from fastapi import APIRouter
from pydantic import BaseModel
from scripts import agent_suggest_patch, platform_data_api

router = APIRouter()

# --- Models ---

class IssueInput(BaseModel):
    issue_id: str

class DiagnosisInput(BaseModel):
    issue_id: str
    diagnosis: dict

# --- Suggest Patch Endpoint ---

@router.post("/suggest-patch", tags=["Autonomous Agents"])
def suggest_patch(input_data: DiagnosisInput):
    """
    Uses AI to suggest a code patch for a diagnosed issue.
    """
    return agent_suggest_patch.agent_suggest_patch(
        issue_id=input_data.issue_id,
        diagnosis=input_data.diagnosis
    )
