from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import traceback  # Import traceback for logging exceptions
import logging  # Import logging

# Import assumed modules/functions for workflow steps
# Ensure these files and functions exist and match the signatures used in run_workflow_orchestrator
from scripts import platform_data_api  # Assumed for status updates and data fetching
from scripts import autonomous_diagnose_issue  # Assumed for diagnosis logic
from scripts.agent_suggest_patch import agent_suggest_patch  # Assumed for patch suggestion function
from scripts.create_fix_pull_request import create_pull_request # Assuming create_pull_request function is inside create_fix_pull_request.py
from scripts.validate_proposed_patch import validate_patch  # Ensure validate_patch is implemented

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router with the /workflow prefix
router = APIRouter(prefix="/workflow", tags=["Workflow"])

# Pydantic Models
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
    relevant_files: list[str]  # Using list[str] for type hinting
    repository: str


# Orchestrator Function (Runs in Background)
async def run_workflow_orchestrator(issue_id: str):
    """
    Orchestrates the entire autonomous debugging workflow for a given issue ID.
    Updates issue status throughout the process.
    """
    logger.info(f"[Orchestrator] Workflow started for issue: {issue_id}")

    try:
        # Step 1: Fetching Details
        status = "Fetching Details"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)

        # Step 2: Diagnosis
        status = "Diagnosis in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        diagnosis_details = await autonomous_diagnose_issue.autonomous_diagnose(issue_id)

        if not diagnosis_details:
            raise ValueError("Diagnosis failed to return details.")

        status = "Diagnosis Complete"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        platform_data_api.save_diagnosis(issue_id, diagnosis_details)

        # Step 3: Patch Suggestion
        status = "Patch Suggestion in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        patch_suggestion_result = await agent_suggest_patch(issue_id, diagnosis_details)

        if not patch_suggestion_result or not patch_suggestion_result.get("patch"):
            raise ValueError("Patch suggestion failed or returned empty patch.")

        status = "Patch Suggestion Complete"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        platform_data_api.save_patch_suggestion(issue_id, patch_suggestion_result)

        # Step 4: Patch Validation
        status = "Patch Validation in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        validation_results = await validate_patch(issue_id, patch_suggestion_result)

        if not validation_results or validation_results.get("status") == "Failed":
            raise ValueError("Patch validation failed.")

        status = "Patch Validated"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        platform_data_api.save_validation_results(issue_id, validation_results)

        # Step 5: PR Creation
        status = "PR Creation in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        pr_result = await create_pull_request(
            issue_id,
            patch_suggestion_result.get("patch"),
            diagnosis_details,
            validation_results
        )

        if not pr_result or pr_result.get("error"):
            raise ValueError(f"PR creation failed: {pr_result.get('error', 'Unknown error')}")

        status = "PR Created - Awaiting Review/QA"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        platform_data_api.save_pr_details(issue_id, pr_result)

        logger.info(f"[Orchestrator] Workflow completed successfully for issue: {issue_id}")

    except Exception as e:
        final_status = "Workflow Failed"
        error_message = f"Workflow failed: {e}"
        logger.error(f"[Orchestrator] {issue_id}: {final_status} - {e}", exc_info=True)
        platform_data_api.update_issue_status(issue_id, final_status, error_message=str(e))


# Routes
@router.post("/run_autonomous_workflow")
def trigger_autonomous_workflow(issue: IssueInput, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the autonomous debugging workflow.
    Starts the orchestrator function in a background task.
    """
    logger.info(f"[API] Received trigger for workflow for issue: {issue.issue_id}")
    background_tasks.add_task(run_workflow_orchestrator, issue.issue_id)
    return {"message": f"Autonomous workflow triggered for issue {issue.issue_id}", "issue_id": issue.issue_id}


@router.post("/triage")
def triage_issue(payload: RawIssueData):
    """
    Placeholder endpoint for triage logic.
    """
    logger.info(f"[API] Triage endpoint called with data: {payload.raw_data}")
    return {"message": "Triage endpoint stub", "data": payload.raw_data}


@router.post("/seed")
def seed_mock_issue(data: MockSeedInput):
    """
    Seeds a mock issue directly into the in-memory mock database.
    """
    logger.info(f"[API] Seed endpoint called for issue: {data.issue_id}")
    from scripts.mock_db import db
    db[data.issue_id] = {
        "id": data.issue_id,
        "title": data.title,
        "description": data.description,
        "error_message": data.error_message,
        "logs": data.logs,
        "relevant_files": data.relevant_files,
        "repository": data.repository,
        "status": "Seeded",
        "details": {},
        "error_message": None
    }
    platform_data_api.update_issue_status(data.issue_id, "Seeded")
    return {"message": f"Issue {data.issue_id} seeded successfully."}


@router.get("/check")
def workflow_check():
    """
    Placeholder endpoint for workflow integrity check.
    """
    logger.info("[API] Workflow check endpoint called.")
    return {"status": "ok", "message": "Workflow check endpoint stub"}
