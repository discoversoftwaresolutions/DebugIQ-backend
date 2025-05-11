# app/api/autonomous_router.py
from fastapi import APIRouter
from pydantic import BaseModel
from scripts import agent_suggest_patch

class DiagnosisInput(BaseModel):
    issue_id: str
    diagnosis: dict

@router.post("/suggest-patch")
def suggest_patch(input: DiagnosisInput):
    return agent_suggest_patch.agent_suggest_patch(
        input.issue_id,
        input.diagnosis
    )
from scripts.run_autonomous_workflow import run_workflow_for_issue

router = APIRouter()

class IssueInput(BaseModel):
    issue_id: str

@router.post("/run")
def run_autonomous(issue: IssueInput):
    return run_workflow_for_issue(issue.issue_id)
