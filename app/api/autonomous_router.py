from fastapi import APIRouter, HTTPException, BackgroundTasks # Import BackgroundTasks
from pydantic import BaseModel
# Import modules/functions for workflow steps
from scripts import platform_data_api          # Assumed for status updates and data fetching
from scripts import autonomous_diagnose_issue # Assumed for diagnosis logic
from scripts.agent_suggest_patch import agent_suggest_patch # Assumed for patch suggestion function
# Import create_pull_request - Assumed to be in a separate module now
from scripts.validate_proposed_patch import validate_patch 
# Assumed import for validation logic - You need to implement validate_patch
# from scripts.validate_patch import validate_patch # <--- YOU NEED TO CREATE THIS FILE/FUNCTION

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


# --- Orchestrator Function (Runs in Background) ---

async def run_workflow_orchestrator(issue_id: str):
    """
    Orchestrates the entire autonomous debugging workflow for a given issue ID.
    Updates issue status throughout the process.
    """
    print(f"[Orchestrator] Workflow started for issue: {issue_id}")

    try:
        # --- Step 1: Fetching Details ---
        status = "Fetching Details"
        print(f"[Orchestrator] {issue_id}: {status}")
        # Assumed function in platform_data_api to update status
        platform_data_api.update_issue_status(issue_id, status)
        # Assume platform_data_api has get_issue_details or similar if needed

        # --- Step 2: Diagnosis ---
        status = "Diagnosis in Progress"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assume autonomous_diagnose_issue.autonomous_diagnose exists and is async/awaitable
        # and returns a dictionary with diagnosis details (including relevant_files, suggested_fix_areas, root_cause)
        diagnosis_details = await autonomous_diagnose_issue.autonomous_diagnose(issue_id)

        if not diagnosis_details:
            raise ValueError("Diagnosis failed to return details.")

        status = "Diagnosis Complete"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save diagnosis details
        platform_data_api.save_diagnosis(issue_id, diagnosis_details) # <--- YOU NEED TO IMPLEMENT THIS IN platform_data_api


        # --- Step 3: Patch Suggestion ---
        status = "Patch Suggestion in Progress"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assume agent_suggest_patch function is async/awaitable
        # It takes issue_id and diagnosis_details, returns dict with 'patch' (diff string)
        patch_suggestion_result = await agent_suggest_patch(issue_id, diagnosis_details)

        if not patch_suggestion_result or not patch_suggestion_result.get("patch"):
             raise ValueError("Patch suggestion failed or returned empty patch.")

        status = "Patch Suggestion Complete"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save patch suggestion
        platform_data_api.save_patch_suggestion(issue_id, patch_suggestion_result) # <--- YOU NEED TO IMPLEMENT THIS


        # --- Step 4: Patch Validation ---
        status = "Patch Validation in Progress"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assume validate_patch function exists, takes issue_id and patch details, returns validation results dict
        # YOU NEED TO IMPLEMENT THE LOGIC IN scripts/validate_patch.py
        # validation_results = await validate_patch.validate_patch(issue_id, patch_suggestion_result) # <--- CALL YOUR VALIDATION LOGIC
        # Placeholder call until validate_patch is implemented
        validation_results = {"summary": "Placeholder validation results."}
        print(f"[Orchestrator] Placeholder Validation for {issue_id}: {validation_results['summary']}")


        if not validation_results or validation_results.get("status") == "Failed": # Assume validation results have a status key
             # Handle validation failure - maybe a different status or rollback
             raise ValueError("Patch validation failed.")

        status = "Patch Validated"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save validation results
        platform_data_api.save_validation_results(issue_id, validation_results) # <--- YOU NEED TO IMPLEMENT THIS


        # --- Step 5: PR Creation ---
        status = "PR Creation in Progress"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Call the create_pull_request function
        # It needs the diff, diagnosis, and validation results
        pr_result = await create_pull_request( # <--- CALL YOUR PR CREATION LOGIC
            issue_id,
            patch_suggestion_result.get("patch"), # Pass the diff string
            diagnosis_details,
            validation_results
        )

        if not pr_result or pr_result.get("error"):
             raise ValueError(f"PR creation failed: {pr_result.get('error', 'Unknown error')}")


        status = "PR Created - Awaiting Review/QA"
        print(f"[Orchestrator] {issue_id}: {status}")
        platform_data_api.update_issue_status(issue_id, status)
        # Assumed function to save PR details
        platform_data_api.save_pr_details(issue_id, pr_result) # <--- YOU NEED TO IMPLEMENT THIS


        print(f"[Orchestrator] Workflow completed successfully for issue: {issue_id}")

    except Exception as e:
        # Catch any errors during the workflow
        status = "Workflow Failed"
        error_message = f"Workflow failed at step '{status}': {e}"
        print(f"[Orchestrator] {issue_id}: {status} - {e}")
        traceback.print_exc() # Log the full traceback for debugging
        platform_data_api.update_issue_status(issue_id, status, error_message=str(e)) # <--- Update status with error

    # Note: The orchestrator doesn't return an HTTP response,
    # it just updates the internal state/DB.


# --- ROUTES ---

# The endpoint that triggers the workflow
@router.post("/run_autonomous_workflow")
def trigger_autonomous_workflow(issue: IssueInput, background_tasks: BackgroundTasks): # <--- ADD BackgroundTasks dependency
    """
    Endpoint to trigger the autonomous debugging workflow.
    Starts the orchestrator in the background.
    """
    print(f"[API] Received trigger for workflow for issue: {issue.issue_id}")
    # Add the orchestrator task to the background
    background_tasks.add_task(run_workflow_orchestrator, issue.issue_id)

    # Immediately return a response to the frontend
    return {"message": f"Autonomous workflow triggered for issue {issue.issue_id}", "issue_id": issue.issue_id}


@router.post("/triage") # Final path will be /workflow/triage
def triage_issue(payload: RawIssueData):
    # ... existing triage logic ...
    return {"message": "Triage endpoint stub", "data": payload.raw_data}


# Removed: @router.post("/workflow/diagnose") as it's now the orchestrator trigger

# Removed: @router.post("/suggest-patch") as it was moved to analyze.py

@router.post("/seed") # Final path will be /workflow/seed
def seed_mock_issue(data: MockSeedInput):
    # ... existing seed logic ...
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
        "status": "Seeded" # Initial status
    }
    # Update status using the standard function as well
    platform_data_api.update_issue_status(data.issue_id, "Seeded") # <--- Use status update function
    return {"message": f"Issue {data.issue_id} seeded successfully."}


@router.get("/check") # Final path will be /workflow/check
def workflow_check():
    # ... existing workflow check logic ...
    """
    Placeholder endpoint for workflow integrity check.
    """
    # Placeholder implementation - replace with actual logic
    return {"status": "ok", "message": "Workflow check endpoint stub"}


# NOTE: You need endpoints to get issue status and details for the frontend polling.
# These likely reside in your issues_router.py, e.g., GET /issues/{issue_id}/status
# The frontend calls GET /issues/{st.session_state.active_issue_id}/status
# which implies issues_router is included without a prefix and has an endpoint
# @router.get("/issues/{issue_id}/status") or similar.
