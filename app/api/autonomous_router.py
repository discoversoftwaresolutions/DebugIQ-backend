from fastapi import APIRouter
from pydantic import BaseModel
from scripts import ingest_and_triage_issue

router = APIRouter()

class RawIssueData(BaseModel):
    raw_data: dict

@router.post("/triage")
def triage_issue(payload: RawIssueData):
    return ingest_and_triage_issue.ingest_and_triage(payload.raw_data)
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
@router.post("/diagnose", tags=["Autonomous Agents"])
def diagnose_issue(issue: IssueInput):
    """
    Diagnoses the root cause of the issue using logs and metadata.
    """
    return platform_data_api.get_diagnosis(issue.issue_id) or \
           autonomous_diagnose_issue.autonomous_diagnose(issue.issue_id)

@router.post("/run-workflow", tags=["Autonomous Agents"])
def run_full_workflow(issue: IssueInput):
    """
    Runs full autonomous debugging workflow for an issue.
    """
    return run_autonomous_workflow.run_workflow_for_issue(issue.issue_id)

@router.post("/create-pr", tags=["Autonomous Agents"])
def create_ai_pull_request(issue: IssueInput):
    """
    Create a Pull Request using AI-generated patch and validation results.
    """
    diagnosis = platform_data_api.get_diagnosis(issue.issue_id)
    patch = platform_data_api.get_proposed_patch(issue.issue_id)
    validation = platform_data_api.get_validation_results(issue.issue_id)

    return create_fix_pull_request.create_pull_request(
        issue_id=issue.issue_id,
        branch_name=f"debugiq/fix-{issue.issue_id.lower()}",
        code_diff=patch.get("patch", ""),
        diagnosis_details=diagnosis,
        validation_results=validation
    )
@router.post("/triage", tags=["Autonomous Agents"])
def triage_issue(payload: RawIssueData):
    """
    AI triages raw issue data (logs, traces, errors).
    """
    return ingest_and_triage_issue.ingest_and_triage(payload.raw_data)

@router.post("/run-workflow", tags=["Autonomous Agents"])
def run_full_workflow(issue: IssueInput):
    """
    Runs full autonomous debugging workflow for an issue.
    """
    return run_autonomous_workflow.run_workflow_for_issue(issue.issue_id)
