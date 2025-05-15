import json
import traceback  # Keep traceback import for detailed exception logging
from utils.call_ai_agent import call_ai_agent
import logging  # Import logging

# Setup logger for this module
logger = logging.getLogger(__name__)


async def validate_patch(issue_id: str, patch_diff: str) -> dict:
    """
    Validates a proposed patch using automated checks and potentially an AI code reviewer.

    Args:
        issue_id (str): The ID of the issue the patch is for.
        patch_diff (str): The patch content in unified diff format.

    Returns:
        dict: A dictionary containing validation results (status, summary, details).
              Includes "status": "Passed" or "Failed".
    """
    logger.info(f"[🔍] Starting patch validation for issue {issue_id}...")

    # Simulated validation logic (Replace with actual checks)
    # These are placeholders. In a real scenario, you'd run static analysis tools,
    # try applying the patch, potentially run tests, etc.
    checks = [
        {"check": "Patch Applies Cleanly", "status": "passed", "details": "Simulated clean application."},
        {"check": "Static Analysis", "status": "passed", "details": "Simulated no critical issues detected."},
        {"check": "Build Status", "status": "passed", "details": "Simulated successful build."},
        {"check": "Bug Reproduction", "status": "passed", "details": "Simulated bug no longer reproduces with patch."}
    ]

    # Determine overall status based on simulated checks
    is_valid = all(step["status"] == "passed" for step in checks)
    validation_status = "Passed" if is_valid else "Failed"

    # Create a summary of automated checks
    validation_summary = "\n".join(f"- {step['check']}: {step['status']}" for step in checks)

    # Prepare the AI code review prompt
    prompt = f"""
You are an AI code reviewer. Assess the following patch and its simulated validation results.

### Issue ID:
{issue_id}

### Patch Diff:
{patch_diff}

### Simulated Validation Results:
{validation_summary}

Provide a detailed review of the patch, focusing on:
- Potential issues or improvements in the patch.
- Suggestions for better implementation (if applicable).
- Final review status: "Approved" or "Changes Requested".
"""

    try:
        logger.info(f"Calling AI agent for patch validation with prompt snippet: {prompt[:500]}...")
        ai_response = await call_ai_agent("patch_validation", prompt)

        if not ai_response:
            logger.error(f"❌ AI agent returned an empty response for patch validation on issue {issue_id}.")
            return {
                "status": "Failed",
                "summary": "AI validation failed",
                "details": "AI agent returned an empty response."
            }

        try:
            # Parse the AI agent response as JSON
            ai_result = json.loads(ai_response)
            logger.info("✅ Successfully parsed AI validation response JSON.")
            return {
                "status": validation_status,
                "summary": validation_summary,
                "details": ai_result
            }
        except json.JSONDecodeError as e:
            logger.error(
                f"❌ Failed to parse AI agent response as JSON for issue {issue_id}: {e}. Response: {ai_response[:500]}",
                exc_info=True
            )
            return {
                "status": "Failed",
                "summary": "AI validation failed",
                "details": "AI response was not valid JSON."
            }

    except Exception as e:
        logger.error(
            f"❌ An unexpected error occurred during patch validation for issue {issue_id}: {e}",
            exc_info=True
        )
        return {
            "status": "Failed",
            "summary": "Validation process encountered an unexpected error.",
            "details": str(e)
        }
