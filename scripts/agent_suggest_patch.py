import json
import traceback
from scripts import platform_data_api
from utils.call_ai_agent import call_ai_agent

PATCH_SUGGESTION_TASK_TYPE = "patch_suggestion"

def agent_suggest_patch(issue_id: str, diagnosis: dict) -> dict | None:
    print(f"🩹 Starting patch suggestion for issue: {issue_id}")

    repo_info = platform_data_api.get_repository_info_for_issue(issue_id)
    if not repo_info:
        print(f"❌ No repository info for issue {issue_id}")
        return None

    files_to_fetch = list(set(
        diagnosis.get("relevant_files", []) +
        [area.split("#")[0] for area in diagnosis.get("suggested_fix_areas", []) if "#" in area]
    ))

    code_context = platform_data_api.fetch_code_context(
        repo_info.get("repository_url"),
        files_to_fetch
    )

    if not code_context:
        print(f"❌ No code context found for {issue_id}")
        return None

    patch_prompt = f"""
Generate a unified diff patch to fix the following bug.

Diagnosis:
Root Cause: {diagnosis.get('root_cause')}
Suggested Areas: {', '.join(diagnosis.get('suggested_fix_areas', []))}

Code Context:
{code_context}

Output only the patch and a short explanation.
"""

    try:
        response = call_ai_agent(PATCH_SUGGESTION_TASK_TYPE, patch_prompt)
        response_data = json.loads(response) if isinstance(response, str) else response

        return {
            "patch": response_data.get("patch", ""),
            "explanation": response_data.get("explanation", "No explanation provided.")
        }

    except Exception as e:
        print(f"🔥 Failed to suggest patch: {e}")
        traceback.print_exc()
        return None
