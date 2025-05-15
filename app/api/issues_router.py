# backend/app/api/issues_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel # Included in case needed for future endpoints
import logging # Import logging

# Assuming platform_data_api has functions to query/get issue status
# Ensure these functions are implemented and are async if they do I/O
from scripts.platform_data_api import query_issues_by_status, get_issue_status

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router WITHOUT a prefix. The prefix is applied in main.py (or not, in this case).
# Since main.py includes this router without a prefix, paths here must be the full paths (e.g., /issues/...).
router = APIRouter(tags=["Issues"])

# --- ROUTES ---

@router.get("/issues/inbox") # Define the full path
# Make it async if query_issues_by_status is async (recommended if it hits a DB)
async def get_new_issues():
    """
    Retrieves issues with status "New".
    Note: Frontend's "Issues Inbox" tab currently maps to /issues/attention-needed.
    """
    logger.info("Received request for /issues/inbox (new issues).")
    try:
        # Assumes query_issues_by_status exists. Make it async if it does I/O.
        # If query_issues_by_status is async, add 'await' here:
        issues = await query_issues_by_status("New") # Assuming async
        logger.info(f"Found {len(issues)} new issues.")
        return {"issues": issues}
    except Exception as e:
        logger.error(f"Failed to fetch new issues: {e}", exc_info=True) # Use logger
        raise HTTPException(status_code=500, detail=f"Failed to fetch inbox issues: {e}") # Use HTTPException

@router.get("/issues/attention-needed") # Define the full path
# Make it async if query_issues_by_status is async (recommended if it hits a DB)
async def get_issues_needing_attention():
    """
    Retrieves issues requiring attention based on failure statuses.
    This endpoint is currently used by the frontend's "Issues Inbox" tab.
    """
    logger.info("Received request for /issues/attention-needed.")
    try:
        # Assumes query_issues_by_status exists. Make it async if it does I/O.
        # If query_issues_by_status is async, add 'await' here:
        issues = await query_issues_by_status([ # Assuming async
            "Diagnosis Failed - AI Analysis",
            "Validation Failed - Manual Review",
            "PR Creation Failed - Needs Review",
            "QA Failed - Needs Review",
            "Workflow Failed" # Added the new workflow failed status
        ])
        logger.info(f"Found {len(issues)} issues needing attention.")
        return {"issues": issues}
    except Exception as e:
        logger.error(f"Failed to fetch attention-needed issues: {e}", exc_info=True) # Use logger
        raise HTTPException(status_code=500, detail=f"Failed to fetch attention-needed list: {e}") # Use HTTPException


# This is the endpoint for fetching a single issue's status, used by frontend polling
@router.get("/issues/{issue_id}/status") # Define the full path with path parameter
# Keep it async as get_issue_status likely does async I/O
async def get_issue_status_endpoint(issue_id: str):
    """
    Retrieves the current status and details for a specific issue ID.
    Used by the frontend for workflow progress polling.
    """
    logger.info(f"Received status request for issue: {issue_id}")
    try:
        # Assumes get_issue_status exists in platform_data_api and is async
        issue_details = await get_issue_status(issue_id) # <--- CORRECTION HERE: Added await

        if not issue_details:
            logger.warning(f"Issue with ID {issue_id} not found during status request.")
            raise HTTPException(status_code=404, detail=f"Issue with ID {issue_id} not found.")

        # Return the relevant details needed by the frontend polling logic
        # Frontend expects {"status": "...", "error_message": "..."}
        status = issue_details.get("status", "Unknown")
        error_message = issue_details.get("error_message") # Can be None

        logger.info(f"Returning status for issue {issue_id}: {status}")

        return {
            "status": status,
            "error_message": error_message # Include error message if stored
            # Omit other details unless frontend polling needs them
        }
    except HTTPException as http_e:
        # Re-raise FastAPI HTTPExceptions (like the 404)
        raise http_e
    except Exception as e:
        logger.error(f"Failed to fetch status for issue {issue_id}: {e}", exc_info=True) # Use logger
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue status: {e}") # Catch other errors


# NOTE on Async: The endpoints calling query_issues_by_status and get_issue_status
# should ensure these underlying functions are correctly defined as async def
# and use appropriate async database drivers or clients if they perform I/O
# to avoid blocking the event loop in this async router.
