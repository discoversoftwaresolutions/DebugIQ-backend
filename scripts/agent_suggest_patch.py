import json
import traceback  # Keep traceback import for detailed exception logging
import logging  # Import logging
from scripts import platform_data_api  # Needed by agent_suggest_patch function
from utils.call_ai_agent import call_ai_agent  # Needed by agent_suggest_patch function

# Setup logger for this module
logger = logging.getLogger(__name__)

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"


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
    logger.info(f"🩹 Starting patch suggestion for issue: {issue_id}")

    try:
        # Fetch repository info for the issue
        repo_info = await platform_data_api.get_repository_info_for_issue(issue_id)
        if not repo_info:
            logger.error(f"❌ No repository info for issue {issue_id} during patch suggestion.")
            return None

        # Gather relevant files from diagnosis
        files_to_fetch = list(
            set(
                diagnosis.get("relevant_files", [])
                + [area.split("#")[0] for area in diagnosis.get("suggested_fix_areas", []) if "#" in area]
            )
        )
        # Filter out any empty strings or None values
        files_to_fetch = [f for f in files_to_fetch if f]

        if not files_to_fetch:
            logger.warning(f"No relevant files identified in diagnosis for issue {issue_id}.")
            return {"patch": "", "explanation": "No relevant files identified for patching."}

        # Fetch code context for these files
        code_context = await platform_data_api.fetch_code_context(
            repo_info.get("repository_url"),  # Ensure repository_url is in repo_info
            files_to_fetch
        )

        if not code_context:
            logger.warning(f"❌ No code context found for {issue_id} in files: {files_to_fetch}. Cannot suggest patch.")
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
{json.dumps(code_context, indent=2)}

### Programming Language:
{language}

Please generate a unified diff patch to fix the bug. Include detailed explanations of the changes made.
"""

        logger.info(f"Calling AI agent for patch suggestion with prompt snippet: {patch_prompt[:500]}...")

        # Call the AI agent for generating the patch
        ai_response = await call_ai_agent(PATCH_SUGGESTION_TASK_TYPE, patch_prompt)

        if not ai_response:
            logger.error(f"❌ AI agent returned an empty response for patch suggestion on issue {issue_id}.")
            return {"patch": "", "explanation": "AI agent failed to generate a patch."}

        try:
            # Parse the AI agent response as JSON
            response_data = json.loads(ai_response)
            logger.info("✅ Successfully parsed AI patch suggestion response JSON.")
            return response_data
        except json.JSONDecodeError as e:
            logger.error(
                f"❌ Failed to parse AI agent response as JSON for issue {issue_id}: {e}. Response: {ai_response[:500]}",
                exc_info=True
            )
            return {"patch": "", "explanation": "AI agent response was not valid JSON."}

    except Exception as e:
        logger.error(
            f"❌ An unexpected error occurred during patch suggestion for issue {issue_id}: {e}",
            exc_info=True
        )
        return {"patch": "", "explanation": "An unexpected error occurred during patch suggestion."}
