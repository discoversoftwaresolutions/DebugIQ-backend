import json
import traceback
from scripts import platform_data_api # Needed by agent_suggest_patch function
from utils.call_ai_agent import call_ai_agent # Needed by agent_suggest_patch function
from fastapi import APIRouter # Keep
from fastapi import HTTPException # Added for proper error handling
from pydantic import BaseModel # Added for input model

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"

# Define the API router for patch suggestion related endpoints
# Main.py includes this router with prefix /debugiq
router = APIRouter() # Keep

# --- Pydantic Model for Frontend Payload for this Endpoint ---
class CodeInput(BaseModel):
    code: str

# ===============================================================
# Define the API endpoint for suggest-patch here, MOVED from autonomous_router.py
# Path is /suggest_patch within this router.
# Main.py includes this router with prefix /debugiq, resulting in /debugiq/suggest_patch
@router.post("/suggest_patch") # <--- ADDED/MOVED ENDPOINT
def suggest_patch_endpoint(payload: CodeInput): # <--- ACCEPTING CODE PAYLOAD FROM FRONTEND
    """
    Receives code directly and attempts to suggest a patch.
    This endpoint needs to be implemented to work based on
    raw code, or the frontend payload/workflow needs adjustment.
    """
    print(f"Received request to suggest patch based on code.")
    provided_code = payload.code

    # --- LOGIC MISMATCH / IMPLEMENTATION NEEDED ---
    # The 'agent_suggest_patch' function defined below requires 'issue_id' and 'diagnosis'.
    # This endpoint receives 'code'.
    # You need to decide how to bridge this:
    # Option A: Implement logic here to process 'provided_code' and call an AI agent directly based on code.
    # Option B: If this endpoint *should* be part of the workflow, change frontend to send issue_id
    #           and call agent_suggest_patch(issue_id, get_diagnosis(issue_id)).
    # Option C: Call a *different* agent function designed to work from raw code.

    # Placeholder implementation - replace with your actual logic
    # For now, it will raise an error indicating it needs implementation.
    # You could also return a simple placeholder response while testing routing.

    # Example of a placeholder response:
    # return {
    #      "patch": "```diff\n--- a/example.py\n+++ b/example.py\n@@ -1,1 +1,1 @@\n-old line\n+new line\n```",
    #      "explanation": "Placeholder patch based on provided code.",
    #      "patched_file_name": "example.py"
    # }

    # Raising an error to clearly show this endpoint needs implementation
    raise HTTPException(
        status_code=501, # 501 Not Implemented
        detail="Suggest patch from code endpoint not fully implemented yet based on this payload structure. Review logic mismatch notes."
    )

# ===============================================================

# Your existing core function that does the work (likely used by the workflow where issue_id and diagnosis are available)
def agent_suggest_patch(issue_id: str, diagnosis: dict) -> dict | None:
    """
    Core function to orchestrate the patch suggestion process, typically
    called within the autonomous workflow using issue ID and diagnosis.
    This function is separate from the /suggest_patch API endpoint above,
    unless the endpoint is specifically implemented to call this function
    after somehow obtaining issue_id and diagnosis.
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

# Note: Your existing function 'agent_suggest_patch' is available
# to be called from other parts of your application (like potentially
# the /workflow/run_autonomous_workflow endpoint) or from the
# /debugiq/suggest_patch endpoint *if* you implement the logic there
# to provide the necessary issue_id and diagnosis.
