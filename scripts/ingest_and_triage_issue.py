# backend/scripts/ingest_and_triage.py

import json
import traceback # Keep traceback import for detailed exception logging if needed
from scripts import platform_data_api # Assumes platform_data_api is available
from utils.ai_api_client import call_ai_agent # Assumes call_ai_agent is available and async
import logging # Import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

TRIAGE_TASK_TYPE = "triage"

# --- CORRECTION HERE ---
# Define the function as asynchronous (async def)
async def ingest_and_triage(raw_data: dict) -> dict:
    """
    Parses raw error data and structures it into a DebugIQ issue schema using AI.
    Checks for duplicates and creates a new issue if unique.

    Args:
        raw_data (dict): The raw input data (e.g., error report, log snippet).

    Returns:
        dict: A dictionary indicating success (issue_id, issue) or failure (error),
              or if a duplicate was found (duplicate, existing_issue_id).
    """
    # --- CORRECTION HERE ---
    logger.info("📥 Ingesting raw issue data...")
    logger.debug(f"Raw data received: {raw_data}") # Log raw data for debugging

    prompt = f"""
Given the following raw error report, monitoring log, or crash message, structure it as a new issue.
Return the output as a JSON object with the keys:
- title (concise summary)
- description (detailed problem description based on raw data)
- logs (relevant log snippets)
- error_message (the primary error message if identifiable)
- relevant_files (list of file paths involved if mentioned)

Raw Data:
{raw_data}
"""

    try:
        logger.info("Calling AI agent for triage...")
        # --- CORRECTION HERE ---
        # Assume utils.ai_api_client.call_ai_agent is async and needs await
        ai_response = await call_ai_agent(task_type=TRIAGE_TASK_TYPE, prompt=prompt)

        # --- Add more robust handling for raw_response ---
        if not ai_response:
             logger.error("❌ AI agent returned empty response for triage.")
             return {"error": "ai_triage_empty_response", "reason": "AI agent returned empty response."}

        # --- CORRECTION HERE ---
        # Attempt to parse the AI response as JSON
        try:
            ai_json = json.loads(ai_response)
            logger.info("✅ Successfully parsed AI triage response JSON.")

            # Start with a base structure and update with AI results
            structured_issue = {
                "title": "AI Parsing Fallback Title", # Fallback values
                "description": "AI parsing fallback description.",
                "logs": str(raw_data), # Default to raw data if AI doesn't provide logs key
                "error_message": "AI Parsing Fallback Error",
                "relevant_files": []
            }
            # Update the structured issue with valid keys from AI response
            valid_keys = ["title", "description", "logs", "error_message", "relevant_files"]
            for key in valid_keys:
                if key in ai_json:
                    structured_issue[key] = ai_json[key]

        except json.JSONDecodeError as json_e:
            # Handle JSON parsing error, create a fallback issue structure
            logger.error(f"❌ Failed to parse AI triage response as JSON: {json_e}. Raw response: {ai_response[:500]}...", exc_info=True) # Use logger
            structured_issue = {
                "title": "AI Triage Parsing Error",
                "description": f"AI response was not valid JSON: {json_e}",
                "logs": str(raw_data), # Include original raw data in logs
                "error_message": "AI Triage JSON Error",
                "relevant_files": [],
                 "raw_ai_response": ai_response # Include raw AI response for debugging
            }
            # Decide if a parsing error should stop the process or create a "Needs Review" issue
            # For now, let's create the issue but mark it for attention.
            structured_issue["status"] = "Needs Manual Triage Review" # Example status
            structured_issue["triage_error"] = f"AI JSON parsing failed: {json_e}"


        # --- Check for duplicate ---
        # Assume platform_data_api.find_duplicate_issue is async and needs await
        duplicate_found, existing_id = await platform_data_api.find_duplicate_issue(structured_issue)
        if duplicate_found:
            logger.warning(f"⚠️ Duplicate issue detected: {existing_id}") # Use logger
            return {"duplicate": True, "existing_issue_id": existing_id}

        # --- Create new issue ---
        # Assume platform_data_api.create_new_issue is async and needs await
        # Ensure create_new_issue handles the status and triage_error fields if present in structured_issue
        new_issue_id = await platform_data_api.create_new_issue(structured_issue)
        logger.info(f"✅ New issue created: {new_issue_id}") # Use logger
        return {"duplicate": False, "issue_id": new_issue_id, "issue": structured_issue}

    except Exception as e:
        # Catch any other unexpected errors during the triage process
        logger.error(f"❌ Error during triage: {e}", exc_info=True) # Use logger and include traceback
        return {"error": str(e)}

# Note: This file defines the 'ingest_and_triage' function.
# It could be called by an API endpoint (like /workflow/triage)
# or by other internal processes that receive raw data.
