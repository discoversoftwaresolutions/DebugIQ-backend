# backend/app/api/autonomous_router.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import traceback # Import traceback for logging exceptions
import logging # Import logging

# --- Import Assumed Modules/Functions for Workflow Steps ---
# These scripts contain the actual logic for each step.
# Ensure these files and functions exist and are implemented (even as placeholders initially).
# Ensure they are async if they perform I/O and are awaited in the orchestrator.

# platform_data_api is assumed to handle interactions with your issue/status storage (mock_db or real DB)
# It needs functions like update_issue_status, save_diagnosis, save_patch_suggestion, save_validation_results, save_pr_details, get_issue_status (used by issues_router)
from scripts import platform_data_api

# autonomous_diagnose_issue is assumed to contain the diagnosis logic
# It needs a function like autonomous_diagnose(issue_id)
from scripts import autonomous_diagnose_issue

# agent_suggest_patch is assumed to contain patch suggestion logic
# It needs a function like agent_suggest_patch(issue_id, diagnosis_details)
from scripts.agent_suggest_patch import agent_suggest_patch

# validate_patch is assumed to contain patch validation logic
# It needs a function like validate_patch(issue_id, patch_suggestion_result)
from scripts.validate_proposed_patch import validate_patch

# create_pull_request is assumed to contain PR creation logic
# It needs a function like create_pull_request(issue_id, patch_diff, diagnosis_details, validation_results)
# CORRECTION: Import using the actual file name create_fix_pull_request
from scripts.create_fix_pull_request import create_pull_request


# Setup logger for this module
logger = logging.getLogger(__name__)


# Initialize the router WITHOUT a prefix. The prefix /workflow will be applied in main.py.
router = APIRouter(tags=["Autonomous Workflow"])


# --- Pydantic Models ---
# Models needed for this router's specific API endpoints (like trigger, seed, triage)
class IssueInput(BaseModel):
    issue_id: str

# PatchInput model example (might be used by a separate manual patch validation endpoint if you add one)
# class PatchInput(BaseModel):
#     issue_id: str
#     patch_diff_content: str

# RawIssueData model example (might be used for manual issue data submission)
# class RawIssueData(BaseModel):
#     raw_data: dict

class MockSeedInput(BaseModel):
    issue_id: str
    title: str
    description: str
    error_message: str
    logs: str
    relevant_files: list[str] # Using list[str] for type hinting
    repository: str


# --- Orchestrator Function (Runs in Background) ---
# This function contains the sequence of steps for the autonomous workflow.
# It calls functions defined in the scripts/ directory.
# It updates the issue status in your data storage via platform_data_api.

async def run_workflow_orchestrator(issue_id: str):
    """
    Orchestrates the entire autonomous debugging workflow for a given issue ID.
    Runs in a background task. Updates issue status throughout the process
    using functions from platform_data_api.
    """
    logger.info(f"[Orchestrator] Workflow started for issue: {issue_id}") # Use logger

    # Use a shared data structure (like a dictionary or database)
    # accessible via platform_data_api to store issue state that the
    # /issues/{issue_id}/status endpoint can read.

    try:
        # Fetch initial details if necessary - Assumes platform_data_api can fetch this.
        # Example: initial_data = await platform_data_api.get_initial_issue_data(issue_id)

        # --- Step 1: Initializing/Fetching Details ---
        status = "Fetching Details" # Corresponds to frontend progress label index 0
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        # Assume platform_data_api.update_issue_status updates the shared state
        await platform_data_api.update_issue_status(issue_id, status) # Assume async

        # --- Step 2: Diagnosis ---
        status = "Diagnosis in Progress" # Corresponds to frontend progress label index 1
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assume autonomous_diagnose_issue.autonomous_diagnose exists and is async/awaitable
        # and returns a dictionary with diagnosis details (including relevant_files, suggested_fix_areas, root_cause, summary)
        diagnosis_details = await autonomous_diagnose_issue.autonomous_diagnose(issue_id)

        if not diagnosis_details or not isinstance(diagnosis_details, dict):
            # Raise a specific error if diagnosis fails or returns unexpected format
            raise ValueError("Diagnosis failed or returned invalid details.")

        status = "Diagnosis Complete" # Corresponds to frontend progress label index 1
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assumed function to save diagnosis details - YOU NEED TO IMPLEMENT THIS in platform_data_api
        await platform_data_api.save_diagnosis(issue_id, diagnosis_details) # Assume async


        # --- Step 3: Patch Suggestion ---
        status = "Patch Suggestion in Progress" # Corresponds to frontend progress label index 2
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assume agent_suggest_patch function is async/awaitable
        # It takes issue_id and diagnosis_details, returns dict with 'patch' (diff string)
        patch_suggestion_result = await agent_suggest_patch(issue_id, diagnosis_details)

        if not patch_suggestion_result or not patch_suggestion_result.get("patch"):
             raise ValueError("Patch suggestion failed or returned empty patch.")

        status = "Patch Suggestion Complete" # Corresponds to frontend progress label index 2
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assumed function to save patch suggestion - YOU NEED TO IMPLEMENT THIS in platform_data_api
        await platform_data_api.save_patch_suggestion(issue_id, patch_suggestion_result) # Assume async


        # --- Step 4: Patch Validation ---
        status = "Patch Validation in Progress" # Corresponds to frontend progress label index 3
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assume validate_patch function exists, takes issue_id and patch details, returns validation results dict
        # YOU NEED TO IMPLEMENT THE LOGIC IN scripts/validate_proposed_patch.py and ensure it's awaitable
        validation_results = await validate_patch(issue_id, patch_suggestion_result) # <--- CALL YOUR VALIDATION LOGIC

        if not validation_results or validation_results.get("status") == "Failed": # Assume validation results have a status key
             # Handle validation failure - raise an error
             # You might want more detailed error messages based on validation_results
             raise ValueError(f"Patch validation failed with status: {validation_results.get('status', 'N/A')}")

        status = "Patch Validated" # Corresponds to frontend progress label index 4
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assumed function to save validation results - YOU NEED TO IMPLEMENT THIS in platform_data_api
        await platform_data_api.save_validation_results(issue_id, validation_results) # Assume async


        # --- Step 5: PR Creation ---
        status = "PR Creation in Progress" # Corresponds to frontend progress label index 5
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Call the create_pull_request function from scripts.create_fix_pull_request
        # It needs the issue_id, diff, diagnosis, and validation results
        # YOU NEED TO IMPLEMENT scripts/create_fix_pull_request.py and ensure it's awaitable
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
        status = "PR Created - Awaiting Review/QA" # Corresponds to frontend progress label index 5
        logger.info(f"[Orchestrator] {issue_id}: {status}") # Use logger
        await platform_data_api.update_issue_status(issue_id, status) # Assume async
        # Assumed function to save PR details - YOU NEED TO IMPLEMENT THIS in platform_data_api
        await platform_data_api.save_pr_details(issue_id, pr_result) # Assume async


        logger.info(f"[Orchestrator] Workflow completed successfully for issue: {issue_id}") # Use logger

    except Exception as e:
        # Catch any errors during the workflow execution
        final_status = "Workflow Failed" # Match frontend's terminal_status_failed
        # Capture the exception message or details for logging and status update
        error_message_detail = f"Workflow failed: {e}"
        logger.error(f"[Orchestrator] {issue_id}: {final_status} - {e}", exc_info=True) # Log error with traceback
        # Update status with the final failed status and the error message
        # Ensure update_issue_status can accept and store an error message
        await platform_data_api.update_issue_status(issue_id, final_status, error_message=str(e)) # Assume async


    # Note: The orchestrator function itself does not return an HTTP response.
    # Its role is to run in the background and update the state of the issue.


# --- API Endpoints for Workflow Trigger and Control ---
# These routes are registered under the /workflow prefix in main.py

# The endpoint that triggers the workflow
# It's registered at /workflow/run_autonomous_workflow due to the router prefix in main.py
@router.post("/run_autonomous_workflow")
def trigger_autonomous_workflow(issue: IssueInput, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the autonomous debugging workflow.
    Starts the orchestrator function in a background task.
    Accepts an issue ID in the request body.
    """
    logger.info(f"[API] Received trigger for workflow for issue: {issue.issue_id}") # Use logger

    # Optional: Check if issue exists and is in a state that can be triggered (e.g., "New", "Failed")
    # try:
    #     current_status = platform_data_api.get_issue_status(issue.issue_id).get("status")
    #     if current_status not in ["New", "Failed", "Seeded", None]:
    #         raise HTTPException(status_code=400, detail=f"Workflow cannot be triggered for issue {issue.issue_id} with status '{current_status}'.")
    # except HTTPException as http_e:
    #     raise http_e # Re-raise the HTTPException
    # except Exception as e:
    #      logger.error(f"Error checking issue status before triggering workflow: {e}", exc_info=True)
    #      raise HTTPException(status_code=500, detail=f"Error checking issue status: {e}")


    # Before starting, set the initial status to indicate it's about to begin
    # This is important for the frontend's initial status check
    try:
        # Assume update_issue_status can handle creating a new entry if issue_id doesn't exist
        platform_data_api.update_issue_status(issue.issue_id, "Triggered") # Assume synchronous update is ok here, or use BackgroundTasks
        logger.info(f"Issue {issue.issue_id} status set to 'Triggered' before starting workflow.")
    except Exception as e:
        logger.error(f"Failed to set initial status for issue {issue.issue_id}: {e}", exc_info=True)
        # Decide if this should block the trigger or just log a warning


    # Add the orchestrator task to be run in the background by FastAPI
    background_tasks.add_task(run_workflow_orchestrator, issue.issue_id)

    # Immediately return a successful response to the frontend
    return {"message": f"Autonomous workflow triggered for issue {issue.issue_id}", "issue_id": issue.issue_id}


# Placeholder endpoint for manually triggering triage (if not part of main flow)
@router.post("/triage") # This endpoint will be at /workflow/triage
def triage_issue(payload: RawIssueData):
    # ... existing triage logic ...
    logger.info(f"[API] Triage endpoint called with data: {payload.raw_data}") # Use logger
    # Placeholder implementation - replace with actual logic
    return {"message": "Triage endpoint stub", "data": payload.raw_data}


# Endpoint to seed a mock issue into the in-memory database for testing
@router.post("/seed") # This endpoint will be at /workflow/seed
def seed_mock_issue(data: MockSeedInput):
    """
    Seeds a mock issue directly into the in-memory mock database.
    Useful for testing workflow runs without external issue tracking.
    """
    logger.info(f"[API] Seed endpoint called for issue: {data.issue_id}") # Use logger
    # Keep local import if only used here
    from scripts.mock_db import db
    # Store the initial data in the mock database
    db[data.issue_id] = {
        "id": data.issue_id,
        "title": data.title,
        "description": data.description,
        "error_message": data.error_message, # Initial error message if any
        "logs": data.logs, # Relevant logs
        "relevant_files": data.relevant_files, # Files associated with the issue
        "repository": data.repository, # Repository information
        "status": "Seeded", # Initial status matching frontend progress map
        "details": {}, # Placeholder for storing diagnosis, validation, PR details
        "error_message": None # Field to store workflow failure message
    }
    # Update status using the standard function as well to ensure consistency
    # Assume update_issue_status saves to the same db structure that /issues/{issue_id}/status reads from
    # Assume update_issue_status can update an existing entry or create a new one
    try:
        # Assuming update_issue_status can be called synchronously if platform_data_api doesn't do async I/O here
        # If platform_data_api.update_issue_status needs async, add BackgroundTasks to this endpoint
        platform_data_api.update_issue_status(data.issue_id, "Seeded") # Assuming synchronous update is ok here
        logger.info(f"[API] Issue {data.issue_id} seeded successfully with status 'Seeded'.") # Use logger
        return {"message": f"Issue {data.issue_id} seeded successfully."}
    except Exception as e:
        logger.error(f"Failed to seed issue {data.issue_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to seed issue: {e}")


# Placeholder endpoint for workflow integrity check. Not part of the main flow.
@router.get("/check") # This endpoint will be at /workflow/check
def workflow_check():
    """
    Placeholder endpoint for workflow integrity check.
    """
    logger.info("[API] Workflow check endpoint called.") # Use logger
    # Placeholder implementation - replace with actual logic
    # Example: Check status of background task queue, check connectivity to dependencies, etc.
    return {"status": "ok", "message": "Workflow check endpoint stub"}


# --- IMPORTANT NOTE ---
# The frontend polls the backend for workflow status using an endpoint like:
# GET /issues/{issue_id}/status
# This endpoint is NOT defined in this autonomous_router.py file.
# It is typically defined in a separate router dedicated to issue management,
# for example, in a file like `backend/routers/issues_router.py`.
# Ensure you have an endpoint defined there that matches this path and method,
# and that it reads the status and error_message fields saved by the orchestrator
# (e.g., from your mock_db or persistent storage via platform_data_api.get_issue_status)
# and returns them in a JSON response that the frontend's polling logic expects
# (e.g., {"status": "...", "error_message": "..."}).

# Note: This file defines the autonomous workflow router. It should be included in main.py
# using app.include_router(router, prefix="/workflow", ...).
