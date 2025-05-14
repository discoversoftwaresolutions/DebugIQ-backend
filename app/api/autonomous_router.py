# autonomous_router.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import traceback # Import traceback for logging exceptions
import logging # Import logging

# Import assumed modules/functions for workflow steps
# Ensure these files and functions exist and match the signatures used in run_workflow_orchestrator
from scripts import platform_data_api          # Assumed for status updates and data fetching
from scripts import autonomous_diagnose_issue # Assumed for diagnosis logic
# Ensure agent_suggest_patch is a function or module with a callable agent_suggest_patch
from scripts.agent_suggest_patch import agent_suggest_patch # Assumed for patch suggestion function
# Ensure create_pull_request is a function
from scripts.create_pull_request import create_pull_request # Assuming create_pull_request is here
# Ensure validate_patch is a function - You need to implement scripts/validate_proposed_patch.py
from scripts.validate_proposed_patch import validate_patch


# Setup logger for this module
logger = logging.getLogger(__name__)


# --- CORRECTION HERE ---
# Initialize the router with the /workflow prefix
router = APIRouter(prefix="/workflow", tags=["Workflow"]) # Added prefix and optional tags


# --- Pydantic Models ---
# Keep all models as provided
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
    relevant_files: list[str] # Using list[str] for type hinting
    repository: str


# --- Orchestrator Function (Runs in Background) ---

async def run_workflow_orchestrator(issue_id: str):
    """
    Orchestrates the entire autonomous debugging workflow for a given issue ID.
    Updates issue status throughout the process.
    """
    logger.info(f"[Orchestrator] Workflow started for issue: {issue_id}") # Use logger

    try:
        # --- Step 1: Fetching Details ---
        status = "Fetching Details"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        # Assumed function in platform_data_api to update status
        platform_data_api.update_issue_status(issue_id, status)
        # Assume platform_data_api has get_issue_details or similar if needed

        # --- Step 2: Diagnosis ---
        status = "Diagnosis in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assume autonomous_diagnose_issue.autonomous_diagnose exists and is async/awaitable
        # and returns a dictionary with diagnosis details (including relevant_files, suggested_fix_areas, root_cause)
        diagnosis_details = await autonomous_diagnose_issue.autonomous_diagnose(issue_id)

        if not diagnosis_details:
            # Raise a specific error if diagnosis fails
            raise ValueError("Diagnosis failed to return details.")

        status = "Diagnosis Complete"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save diagnosis details - YOU NEED TO IMPLEMENT THIS
        platform_data_api.save_diagnosis(issue_id, diagnosis_details)


        # --- Step 3: Patch Suggestion ---
        status = "Patch Suggestion in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assume agent_suggest_patch function is async/awaitable
        # It takes issue_id and diagnosis_details, returns dict with 'patch' (diff string)
        patch_suggestion_result = await agent_suggest_patch(issue_id, diagnosis_details)

        if not patch_suggestion_result or not patch_suggestion_result.get("patch"):
             raise ValueError("Patch suggestion failed or returned empty patch.")

        status = "Patch Suggestion Complete"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save patch suggestion - YOU NEED TO IMPLEMENT THIS
        platform_data_api.save_patch_suggestion(issue_id, patch_suggestion_result)


        # --- Step 4: Patch Validation ---
        status = "Patch Validation in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assume validate_patch function exists, takes issue_id and patch details, returns validation results dict
        # YOU NEED TO IMPLEMENT THE LOGIC IN scripts/validate_proposed_patch.py and ensure it's awaitable
        validation_results = await validate_patch(issue_id, patch_suggestion_result) # <--- CALL YOUR VALIDATION LOGIC

        if not validation_results or validation_results.get("status") == "Failed": # Assume validation results have a status key
             # Handle validation failure - raise an error
             # You might want more detailed error messages based on validation_results
             raise ValueError("Patch validation failed.")

        status = "Patch Validated"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save validation results - YOU NEED TO IMPLEMENT THIS
        platform_data_api.save_validation_results(issue_id, validation_results)


        # --- Step 5: PR Creation ---
        status = "PR Creation in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Call the create_pull_request function
        # It needs the issue_id, diff, diagnosis, and validation results
        # YOU NEED TO IMPLEMENT scripts/create_pull_request.py and ensure it's awaitable
        pr_result = await create_pull_request(
            issue_id,
            patch_suggestion_result.get("patch"), # Pass the diff string
            diagnosis_details,
            validation_results
        )

        if not pr_result or pr_result.get("error"):
             # Handle PR creation failure - raise an error
             raise ValueError(f"PR creation failed: {pr_result.get('error', 'Unknown error')}")


        # Final success status matching the frontend's terminal_status_success
        status = "PR Created - Awaiting Review/QA"
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save PR details - YOU NEED TO IMPLEMENT THIS
        platform_data_api.save_pr_details(issue_id, pr_result)


        logger.info(f"[Orchestrator] Workflow completed successfully for issue: {issue_id}") # Use logger

    except Exception as e:
        # Catch any errors during the workflow execution
        final_status = "Workflow Failed" # Match frontend's terminal_status_failed
        error_message = f"Workflow failed: {e}" # Capture the exception message
        logger.error(f"[Orchestrator] {issue_id}: {final_status} - {e}", exc_info=True) # Log error with traceback
        # Update status with the final failed status and the error message
        platform_data_api.update_issue_status(issue_id, final_status, error_message=str(e))


    # Note: The orchestrator function itself does not return an HTTP response.
    # Its role is to run in the background and update the state of the issue.


# --- ROUTES ---

# The endpoint that triggers the workflow
# It's registered at /workflow/run_autonomous_workflow due to the router prefix
@router.post("/run_autonomous_workflow")
def trigger_autonomous_workflow(issue: IssueInput, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the autonomous debugging workflow.
    Starts the orchestrator function in a background task.
    """
    logger.info(f"[API] Received trigger for workflow for issue: {issue.issue_id}") # Use logger
    # Add the orchestrator task to be run in the background by FastAPI
    background_tasks.add_task(run_workflow_orchestrator, issue.issue_id)

    # Immediately return a successful response to the frontend
    return {"message": f"Autonomous workflow triggered for issue {issue.issue_id}", "issue_id": issue.issue_id}


@router.post("/triage") # This endpoint will be at /workflow/triage
def triage_issue(payload: RawIssueData):
    # ... existing triage logic ...
    logger.info(f"[API] Triage endpoint called with data: {payload.raw_data}") # Use logger
    # Placeholder implementation - replace with actual logic
    return {"message": "Triage endpoint stub", "data": payload.raw_data}


@router.post("/seed") # This endpoint will be at /workflow/seed
def seed_mock_issue(data: MockSeedInput):
    """
    Seeds a mock issue directly into the in-memory mock database.
    """
    logger.info(f"[API] Seed endpoint called for issue: {data.issue_id}") # Use logger
    from scripts.mock_db import db # Keep local import if only used here
    # Store the initial data in the mock database
    db[data.issue_id] = {
        "id": data.issue_id,
        "title": data.title,
        "description": data.description,
        "error_message": data.error_message,
        "logs": data.logs,
        "relevant_files": data.relevant_files,
        "repository": data.repository,
        "status": "Seeded", # Initial status
        "details": {}, # Initialize details or other fields your status endpoint might return
        "error_message": None # Initialize error message field
    }
    # Update status using the standard function as well to ensure consistency
    platform_data_api.update_issue_status(data.issue_id, "Seeded") # <--- Use status update function
    logger.info(f"[API] Issue {data.issue_id} seeded successfully with status 'Seeded'.") # Use logger
    return {"message": f"Issue {data.issue_id} seeded successfully."}


@router.get("/check") # This endpoint will be at /workflow/check
def workflow_check():
    """
    Placeholder endpoint for workflow integrity check.
    """
    logger.info("[API] Workflow check endpoint called.") # Use logger
    # Placeholder implementation - replace with actual logic
    return {"status": "ok", "message": "Workflow check endpoint stub"}


# --- IMPORTANT NOTE ---
# The frontend polls the backend for workflow status using an endpoint like:
# GET /issues/{issue_id}/status
# This endpoint is NOT defined in this autonomous_router.py file.
# It is typically defined in a separate router dedicated to issue management,
# for example, in a file like `backend/routers/issues_router.py`.
# Ensure you have an endpoint defined there that matches this path and method,
# and that it reads the status and error_message fields saved by the orchestrator
# (e.g., from your mock_db or persistent storage) and returns them in a JSON response
# that the frontend's polling logic expects (e.g., {"status": "...", "error_message": "..."}).

# Remember to include this router in your main FastAPI application instance (e.g., in main.py or app.py)
# Example:
# from .routers import autonomous_router, issues_router # Assuming structure
# app.include_router(autonomous_router.router)
# app.include_router(issues_router.router) # Make sure your issues router is included too!
