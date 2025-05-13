import json
import traceback
from scripts import platform_data_api
from utils.call_ai_agent import call_ai_agent
# Add FastAPI import to define the router
from fastapi import APIRouter # <--- ADDED

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"

# Define the API router for patch suggestion related endpoints
# This is the 'router' object that other files will import
router = APIRouter() # <--- ADDED

# ===============================================================
# Define your API endpoints using the 'router' object here.
# Example:
# @router.post("/suggest")
# async def create_patch_suggestion(issue_id: str, diagnosis_data: dict):
#     # You would call your agent_suggest_patch function from here
#     patch_result = agent_suggest_patch(issue_id, diagnosis_data)
#     if patch_result:
#         return patch_result
#     # Add error handling here if agent_suggest_patch returns None
#     return {"error": "Failed to generate patch"}
# ===============================================================


def agent_suggest_patch(issue_id: str, diagnosis: dict) -> dict | None:
    """
    Core function to orchestrate the patch suggestion process.
    This function is likely called by an API endpoint defined on the router.
    """
    print(f"🩹 Starting patch suggestion for issue: {issue_id}")

    # Fetch repository information
    # Assuming platform_data_api has get_repository_info_for_issue and fetch_code_context
    try:
        repo_info = platform_data_api.get_repository_info_for_issue(issue_id)
        if not repo_info:
            print(f"❌ No repository info for issue {issue_id}")
            return None

        # Gather relevant files
        files_to_fetch = list(set(
            diagnosis.get("relevant_files", []) +
            [area.split("#")[0] for area in diagnosis.get("suggested_fix_areas", []) if "#" in area]
        ))

        # Fetch code context
        code_context = platform_data_api.fetch_code_context(
            repo_info.get("repository_url"),
            files_to_fetch
        )

        if not code_context:
            print(f"❌ No code context found for {issue_id}")
            return None

        # Prepare the patch suggestion prompt
        patch_prompt = f"""
You are a debugging assistant, part of the DebugIQ platform, powered by GPT-4o. Your task is to analyze the provided diagnosis and code context and generate a unified diff patch to fix the bug.

### Diagnosis:
Root Cause: {diagnosis.get('root_cause', 'Unknown')}
Suggested Fix Areas: {', '.join(diagnosis.get('suggested_fix_areas', []))}

### Code Context:
{code_context}

### Instructions:
1. Generate a unified diff patch that addresses the diagnosis.
2. Provide a clear and concise explanation of the changes.
3. Ensure the patch is syntactically valid.

Respond with the following format:
### Patch:
<patch>
### Explanation:
<explanation>
"""

        # Call DebugIQ's GPT-4o-powered model
        response = call_ai_agent(PATCH_SUGGESTION_TASK_TYPE, patch_prompt)
        # Attempt to parse JSON response
        try:
             response_data = json.loads(response) if isinstance(response, str) else response
        except json.JSONDecodeError:
             print(f"⚠️ AI agent response was not valid JSON: {response}")
             # Handle this case - maybe return a default structure or error
             response_data = {} # Or raise an exception

        # Parse and return the response
        return {
            "patch": response_data.get("patch", ""),
            "explanation": response_data.get("explanation", "No explanation provided."),
            "patched_file_name": response_data.get("patched_file_name", "patched_file.py")
        }

    except Exception as e:
        print(f"🔥 Failed to suggest patch: {e}")
        traceback.print_exc()
        return None

# Note: Your existing function 'agent_suggest_patch' is now available
# to be called from the API endpoints defined on the 'router' object above.
