# backend/scripts/agent_suggest_patch.py

import json
import traceback # Keep traceback import for detailed exception logging
from scripts import platform_data_api # Needed by agent_suggest_patch function
from utils.call_ai_agent import call_ai_agent # Needed by agent_suggest_patch function
# Removed: from fastapi import APIRouter # No longer needed if this file doesn't define a router
# Removed: from fastapi import HTTPException # No longer needed if no endpoint is here
# Removed: from pydantic import BaseModel # No longer needed if no endpoint/model defined here
import logging # Import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"

# Removed the router instance definition and any related endpoint code
# as this file is intended to contain the core function, not API endpoints.
# router = APIRouter() # REMOVED


# Your existing core function that does the work, corrected for async and logging
# --- CORRECTION HERE ---
# Define the function as asynchronous (async def)
# Add 'language' as an argument as it's used in the prompt
async def agent_suggest_patch(issue_id: str, diagnosis: dict, language: str) -> dict | None:
    """
    Core asynchronous function to orchestrate the patch suggestion process, typically
    called within the autonomous workflow using issue ID and diagnosis details.
    This function interacts with data storage/Git and an AI agent.

    Args:
        issue_id (str): The ID of the issue.
        diagnosis (dict): Diagnosis details for the issue.
        language (str): The programming language of the code being patched.

    Returns:
        dict | None: A dictionary containing the suggested patch, explanation, etc.,
                      or None on failure.
    """
    # --- CORRECTION HERE ---
    logger.info(f"🩹 Starting patch suggestion for issue: {issue_id}")

    try:
        # Assume platform_data_api functions are async and need await
        repo_info = await platform_data_api.get_repository_info_for_issue(issue_id) # await call
        if not repo_info:
            logger.error(f"❌ No repository info for issue {issue_id} during patch suggestion.") # Use logger
            return None

        # Gather relevant files from diagnosis
        files_to_fetch = list(set(
            diagnosis.get("relevant_files", []) +
            [area.split("#")[0] for area in diagnosis.get("suggested_fix_areas", []) if "#" in area]
        ))
        # Filter out any empty strings or None values that might result from splitting
        files_to_fetch = [f for f in files_to_fetch if f]

        if not files_to_fetch:
             logger.warning(f"No relevant files identified in diagnosis for issue {issue_id}.")
             # Decide how to handle this - maybe return None or proceed with less context
             return {"patch": "", "explanation": "No relevant files identified for patching."}


        # Fetch code context for these files
        code_context = await platform_data_api.fetch_code_context( # await call
            repo_info.get("repository_url"), # Ensure repository_url is in repo_info
            files_to_fetch,
            # You might need to pass commitish/branch info here too
            # branch = repo_info.get("branch", "main") # Example
        )

        if not code_context:
            logger.warning(f"❌ No code context found for {issue_id} in files: {files_to_fetch}. Cannot suggest patch.") # Use logger
            # Decide how to handle this - AI needs code to patch
            return {"patch": "", "explanation": "Could not fetch relevant code context for patching."}


        # Prepare the patch suggestion prompt
        patch_prompt = f"""
You are a debugging assistant, part of the DebugIQ platform. Your task is to analyze the provided diagnosis and code context and generate a unified diff patch to fix the bug.

### Issue ID:
{issue_id}

### Diagnosis:
Root Cause: {diagnosis.get('root_cause', 'Unknown')}
Detailed Analysis: {diagnosis.get('detailed_analysis', 'None provided')}
Suggested Fix Areas: {', '.join(diagnosis.get('suggested_fix_areas', []))}

### Code Context:
