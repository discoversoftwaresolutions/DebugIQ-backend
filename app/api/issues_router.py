from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
# Assuming platform_data_api has functions to query/get issue status
from scripts.platform_data_api import query_issues_by_status, get_issue_status # <--- ADD get_issue_status

router = APIRouter()

# --- Pydantic Models (if needed for this router's specific endpoints) ---
# No specific models needed for the GET endpoints shown here

# --- ROUTES ---

@router.get("/issues/inbox", tags=["Issues"])
def get_new_issues():
    """
    Retrieves issues with status "New".
    """
    try:
        # Assumes query_issues_by_status exists and is synchronous
        issues = query_issues_by_status("New")
        return {"issues": issues}
    except Exception as e:
        print(f"[❌] Failed to fetch new issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch inbox: {e}") # Use HTTPException for API errors


@router.get("/issues/attention-needed", tags=["Issues"])
def get_issues_needing_attention():
    """
    Retrieves issues requiring attention based on failure statuses.
    """
    try:
        # Assumes query_issues_by_status exists and is synchronous
        issues = query_issues_by_status([
            "Diagnosis Failed - AI Analysis",
            "Validation Failed - Manual Review",
            "PR Creation Failed - Needs Review",
            "QA Failed - Needs Review",
            "Workflow Failed" # Added the new workflow failed status
        ])
        return {"issues": issues}
    except Exception as e:
        print(f"[❌] Failed to fetch attention-needed issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch attention-needed list: {e}") # Use HTTPException for API errors


# Add the missing endpoint for fetching a single issue's status
@router.get("/issues/{issue_id}/status", tags=["Issues"])
# Make it async if get_issue_status is async (recommended if it hits a DB)
async def get_issue_status_endpoint(issue_id: str): # <--- ADD THIS ENDPOINT
    """
    Retrieves the current status and details for a specific issue ID.
    Used by the frontend for workflow progress polling.
    """
    try:
        # Assumes get_issue_status exists in platform_data_api
        # Make get_issue_status async if it performs async operations (like DB calls)
        # Then add 'await' before the call: issue_details = await get_issue_status(issue_id)
        issue_details = get_issue_status(issue_id) # <--- CALL YOUR DATA FUNCTION

        if not issue_details:
            raise HTTPException(status_code=404, detail=f"Issue with ID {issue_id} not found.")

        # Return the relevant details needed by the frontend
        return {
            "issue_id": issue_details.get("id"),
            "status": issue_details.get("status"),
            "error_message": issue_details.get("error_message") # Include error message if stored with status
            # Include other details the frontend needs for progress display
        }
    except HTTPException as http_e:
        raise http_e # Re-raise FastAPI HTTPExceptions
    except Exception as e:
        print(f"[❌] Failed to fetch status for issue {issue_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue status: {e}") # Catch other errors


# NOTE on Async: The endpoints calling query_issues_by_status are currently synchronous.
# If query_issues_by_status or get_issue_status interact with a database or perform other I/O,
# they (and the endpoints calling them) should ideally be made async def and use an async DB driver/client
# to avoid blocking the event loop.
