import json
import traceback
from scripts import platform_data_api
from utils.call_ai_agent import call_ai_agent

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"

def agent_suggest_patch(issue_id: str, diagnosis: dict) -> dict | None:
    print(f"🩹 Starting patch suggestion for issue: {issue_id}")

    # Fetch repository information
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

    try:
        # Call DebugIQ's GPT-4o-powered model
        response = call_ai_agent(PATCH_SUGGESTION_TASK_TYPE, patch_prompt)
        response_data = json.loads(response) if isinstance(response, str) else response

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
