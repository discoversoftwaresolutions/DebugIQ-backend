import json
import traceback
from scripts import platform_data_api # Needed by agent_suggest_patch function
from utils.call_ai_agent import call_ai_agent # Needed by agent_suggest_patch function
from fastapi import APIRouter # Keep (router instance is still included in main.py)
# Removed: from fastapi import HTTPException # No longer needed if no endpoint is here
# Removed: from pydantic import BaseModel # No longer needed if no endpoint/model defined here

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"

# Define the API router for patch suggestion related endpoints
# This router instance is still included in main.py, potentially for future endpoints,
# but it no longer defines the /suggest_patch endpoint.
router = APIRouter() # Keep

# Removed: --- Pydantic Model for Frontend Payload for this Endpoint ---
# Removed: class CodeInput(BaseModel): code: str

# ===============================================================
# Removed: The API endpoint definition for suggest-patch (@router.post("/suggest_patch"))
# Removed: and the suggest_patch_endpoint function are REMOVED from this file
# because they should be defined ONLY in app/api/analyze.py to avoid routing conflicts.
# ===============================================================


# Your existing core function that does the work (likely used by the workflow where issue_id and diagnosis are available)
def agent_suggest_patch(issue_id: str, diagnosis: dict) -> dict | None:
    """
    Core function to orchestrate the patch suggestion process, typically
    called within the autonomous workflow using issue ID and diagnosis.
    This function is separate from any API endpoint definition.
    """
    print(f"🩹 Starting patch suggestion for issue: {issue_id}")

    # ... rest of your existing function code ...
    # This code relies on issue_id and diagnosis

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
3. Ensure the suggested patch is syntactically correct for {request.language}. # Note: This prompt assumes 'language' is available, which it isn't in the context of this function itself. This might need rethinking if called from a context without diagnosis/language.

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
             # response_data = json.loads(response) if isinstance(response, str) else response
             # Fix json load if response is already a dict
             response_data = json.loads(response) if isinstance(response, str) else response # <--- KEEP THIS LINE AS IS, IT HANDLES STRING OR DICT
        except json.JSONDecodeError:
             print(f"⚠️ AI agent response was not valid JSON: {response}")
             response_data = {} # Handle invalid JSON

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

# Note: The 'agent_suggest_patch' function is available to be called
# from other parts of your application, like the
# /workflow/run_autonomous_workflow endpoint in autonomous_router.py
# if it needs to include this step.
