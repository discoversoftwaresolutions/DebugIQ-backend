# backend/app/api/autonomous_router.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import traceback
import logging

# --- Import Assumed Modules/Functions for Workflow Steps ---
# These scripts contain the actual logic for each step.
# Ensure these files and functions exist and are implemented (even as placeholders initially).
# Ensure they are async if they perform I/O and are awaited in the orchestrator.

from scripts import platform_data_api # Imports the module containing async data functions
from scripts import autonomous_diagnose_issue # Assumed to contain async autonomous_diagnose function
from scripts.agent_suggest_patch import agent_suggest_patch # Assumed to contain async agent_suggest_patch function
from scripts.validate_proposed_patch import validate_patch # Assumed to contain async validate_patch function
from scripts.create_fix_pull_request import create_pull_request # Assumed to contain async create_pull_request function

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router WITHOUT a prefix. The prefix /workflow will be applied in main.py.
router = APIRouter(tags=["Autonomous Workflow"])


# --- Pydantic Models ---
class IssueInput(BaseModel):
    issue_id: str


class MockSeedInput(BaseModel):
    issue_id: str
    title: str
    description: str
    error_message: str | None = None # Error message can be optional
    logs: str
    relevant_files: list[str]
    repository: str
    # Optional fields you might want to include in seed data
    # repository_owner: str | None = None
    # base_branch: str | None = None


# --- Orchestrator Function (Runs in Background) ---
async def run_workflow_orchestrator(issue_id: str):
    """
    Orchestrates the entire autonomous debugging workflow for a given issue ID.
    Runs in a background task. Updates issue status throughout the process
    using functions from platform_data_api.
    """
    logger.info(f"[Orchestrator] Workflow started for issue: {issue_id}")

    # --- Step 1: Initializing/Fetching Details ---
    # Set initial status *within* the async orchestrator
    status = "Fetching Details"
    logger.info(f"[Orchestrator] {issue_id}: {status}")
    await platform_data_api.update_issue_status(issue_id, status)

    issue_details = await platform_data_api.get_issue_details(issue_id)
    if not issue_details:
         # If issue details cannot be fetched, the workflow cannot proceed
         error_msg = f"Could not fetch details for issue {issue_id}. Workflow aborted."
         logger.error(f"[Orchestrator] {issue_id}: {error_msg}")
         await platform_data_api.update_issue_status(issue_id, "Failed: Fetch Error", error_message=error_msg)
         return # Abort workflow

    try:
        # --- Step 2: Diagnosis ---
        status = "Diagnosis in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        # Assumes autonomous_diagnose takes issue_id and potentially issue_details as input
        diagnosis_details = await autonomous_diagnose_issue.autonomous_diagnose(issue_id, issue_details)

        if not diagnosis_details or not isinstance(diagnosis_details, dict):
            raise ValueError("Diagnosis failed or returned invalid details.")

        status = "Diagnosis Complete"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        await platform_data_api.save_diagnosis(issue_id, diagnosis_details)

        # --- Step 3: Patch Suggestion ---
        status = "Patch Suggestion in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        # Assumes agent_suggest_patch takes issue_id, diagnosis_details, and potentially language
        # We need to get language. Assume it's part of issue_details or diagnosis_details.
        language = issue_details.get("language", diagnosis_details.get("language", "unknown")) # Get language safely
        patch_suggestion_result = await agent_suggest_patch(issue_id, diagnosis_details, language)

        if not patch_suggestion_result or patch_suggestion_result.get("patch") is None: # Check for None explicitly
            # Check if an error was returned in the dict
            if patch_suggestion_result and patch_suggestion_result.get("error"):
                 raise ValueError(f"Patch suggestion failed with error: {patch_suggestion_result['error']}")
            else:
                raise ValueError("Patch suggestion failed or returned empty patch.")

        status = "Patch Suggestion Complete"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        await platform_data_api.save_patch_suggestion(issue_id, patch_suggestion_result)

        # --- Step 4: Patch Validation ---
        status = "Patch Validation in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        # Assumes validate_patch takes issue_id and patch_suggestion_result
        validation_results = await validate_patch(issue_id, patch_suggestion_result)

        if not validation_results or validation_results.get("status") == "Failed":
             # Include validation summary if available
             validation_summary = validation_results.get('summary', 'No summary provided') if validation_results else 'No results provided'
             raise ValueError(f"Patch validation failed with status: {validation_results.get('status', 'N/A')}. Summary: {validation_summary}")


        status = "Patch Validated"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        await platform_data_api.save_validation_results(issue_id, validation_results)

        # --- Step 5: PR Creation ---
        status = "PR Creation in Progress"
        logger.info(f"[Orchestrator] {issue_id}: {status}")
        await platform_data_api.update_issue_status(issue_id, status)
        # Assumes create_pull_request takes issue_id, patch_diff, diagnosis_details, validation_results
        pr_result = await create_pull_request(
            issue_id,
            patch_suggestion_result.get("patch", ""), # Pass the patch string
            diagnosis_details,
            validation_results
        )

        if not pr_result or pr_result.get("error"):
            # Include the error message from the PR result if available
            pr_error_msg = pr_result.get('error', 'Unknown error') if pr_result else 'No PR result'
            raise ValueError(f"PR creation failed: {pr_error_msg}")


        status = "PR Created - Awaiting Review/QA"
        logger.info(f"[Orchestrator] {issue_id}: {status}. PR: {pr_result.get('pr_url', 'N/A')}")
        await platform_data_api.update_issue_status(issue_id, status)
        await platform_data_api.save_pr_details(issue_id, pr_result)

        logger.info(f"[Orchestrator] Workflow completed successfully for issue: {issue_id}")

    except Exception as e:
        final_status = "Workflow Failed"
        # Log the full exception details
        logger.error(f"[Orchestrator] {issue_id}: {final_status} - {e}", exc_info=True)
        # Update issue status with the error message
        # Ensure error_message is a string
        error_message_str = str(e)
        await platform_data_api.update_issue_status(issue_id, final_status, error_message=error_message_str)


# --- API Endpoints for Workflow Trigger and Control ---
@router.post("/run_autonomous_workflow")
def trigger_autonomous_workflow(issue: IssueInput, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the autonomous debugging workflow.
    Starts the orchestrator function in a background task.
    Accepts an issue ID in the request body.
    """
    logger.info(f"[API] Received trigger for workflow for issue: {issue.issue_id}")
    # --- CORRECTION: Removed synchronous call to update_issue_status ---
    # The initial status update is handled by the orchestrator itself once it starts.
    # platform_data_api.update_issue_status(issue.issue_id, "Triggered") # REMOVE THIS LINE
    background_tasks.add_task(run_workflow_orchestrator, issue.issue_id)
    return {"message": f"Autonomous workflow triggered for issue {issue.issue_id}. Check status endpoint for updates.", "issue_id": issue.issue_id}


@router.post("/seed")
def seed_mock_issue(data: MockSeedInput):
    """
    Seeds a mock issue directly into the in-memory mock database.
    Useful for testing workflow runs without external issue tracking.
    """
    logger.info(f"[API] Seed endpoint called for issue: {data.issue_id}")
    # Import db here to keep the import local to the sync function if preferred,
    # or import at the top if mock_db is always available.
    from scripts.mock_db import db

    # Create the mock issue structure with initial status 'Seeded'
    db[data.issue_id] = {
        "id": data.issue_id,
        "title": data.title,
        "description": data.description,
        "error_message": data.error_message, # Keep the provided error message if any
        "logs": data.logs,
        "relevant_files": data.relevant_files,
        "repository": data.repository,
        "language": "python", # Add a mock language field for agent_suggest_patch
        "status": "Seeded", # Set initial status directly
        "details": {}, # Placeholder for other raw data
        "diagnosis": None,
        "patch_suggestion": None,
        "validation_results": None,
        "pr_details": None,
        # Include other optional fields if provided in MockSeedInput
        # "repository_owner": data.repository_owner,
        # "base_branch": data.base_branch,
    }

    # --- CORRECTION: Removed synchronous call to update_issue_status ---
    # The status is already set directly in the mock db above.
    # platform_data_api.update_issue_status(data.issue_id, "Seeded") # REMOVE THIS LINE

    logger.info(f"[API] Issue {data.issue_id} seeded successfully with status 'Seeded'.")
    return {"message": f"Issue {data.issue_id} seeded successfully."}


@router.get("/check")
def workflow_check():
    """
    Placeholder endpoint for workflow integrity check.
    """
    logger.info("[API] Workflow check endpoint called.")
    return {"status": "ok", "message": "Workflow check endpoint stub"}

# Note: This router is included in main.py with prefix="/workflow", e.g.,
# app.include_router(autonomous_router.router, prefix="/workflow", tags=["Autonomous Workflow"])
