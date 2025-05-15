import json
import traceback  # Keep traceback import for detailed exception logging
import logging  # Import logging
from typing import Optional
from scripts import platform_data_api
from utils.call_ai_agent import call_ai_agent

# Setup logger for this module
logger = logging.getLogger(__name__)

DIAGNOSIS_TASK_TYPE = "diagnosis"


async def autonomous_diagnose(issue_id: str) -> Optional[dict]:
    """
    Performs autonomous diagnosis for a given issue ID using an AI agent.

    Args:
        issue_id (str): The ID of the issue to diagnose.

    Returns:
        Optional[dict]: A dictionary containing diagnosis details if successful,
                        or None or a dictionary with an "error" key on failure.
    """
    logger.info(f"🔬 Starting diagnosis for issue: {issue_id}")

    try:
        # Assume platform_data_api.fetch_issue_details is async and needs await
        issue_details = await platform_data_api.fetch_issue_details(issue_id)
        if not issue_details:
            logger.error(f"❌ Issue not found during diagnosis: {issue_id}")
            # Return a specific error structure or None as per signature
            return {"error": "issue_not_found", "issue_id": issue_id}

        logs = issue_details.get("logs", "")
        description = issue_details.get("description", "")
        error_msg = issue_details.get("error_message", "")
        relevant_files = issue_details.get("relevant_files", [])  # Get relevant files if available

        prompt = f"""
You are an expert debugging agent. Analyze the following:

Issue: {issue_id}
Description: {description}
Error: {error_msg}
Logs:
{logs}

Relevant Files (for context, do not assume you have access to content):
{', '.join(relevant_files) if relevant_files else 'None specified'}

Your task is to perform root cause analysis and identify potential fix areas.

Return JSON with the following keys:
- "summary": A brief summary of the root cause and suggested fix areas.
- "root_cause": Detailed description of the identified root cause.
- "detailed_analysis": Step-by-step analysis performed.
- "relevant_files": List of files identified as most relevant to the issue (confirm or refine from input if possible).
- "suggested_fix_areas": Specific code areas or modules to focus on for fixing.
- "confidence": Your confidence score in the diagnosis (e.g., High, Medium, Low).
"""

        logger.info(f"Calling AI agent for diagnosis with prompt snippet: {prompt[:500]}...")

        # Assume utils.call_ai_agent is async and needs await
        raw_response = await call_ai_agent(DIAGNOSIS_TASK_TYPE, prompt)

        # Add more robust handling for raw_response
        if not raw_response:
            logger.error("❌ AI agent returned empty response for diagnosis.")
            return {"error": "ai_diagnosis_empty_response", "reason": "AI agent returned empty response."}

        try:
            # Attempt to parse the raw response as JSON
            data = json.loads(raw_response)
            logger.info("✅ Successfully parsed AI diagnosis response JSON.")
            return data  # Return the parsed dictionary
        except json.JSONDecodeError as json_e:
            # If JSON parsing fails, return an error including the raw response
            logger.error(
                f"❌ Failed to parse AI diagnosis response as JSON: {json_e}. Raw response: {raw_response[:500]}...",
                exc_info=True
            )
            return {
                "error": "diagnosis_json_parse_failed",
                "reason": f"AI agent response was not valid JSON: {json_e}",
                "raw_response": raw_response  # Include the raw response for debugging
            }

    except Exception as e:
        # Catch any other exceptions during the diagnosis process (e.g., API call errors)
        logger.error(
            f"❌ An unexpected error occurred during diagnosis for issue {issue_id}: {e}",
            exc_info=True
        )
        return {
            "error": "diagnosis_unexpected_error",
            "reason": str(e),
            "raw_response": raw_response if 'raw_response' in locals() else "Error before AI call"
        }
