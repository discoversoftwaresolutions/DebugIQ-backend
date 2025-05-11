import json
import traceback
from scripts import platform_data_api
from utils.call_ai_agent import call_ai_agent  # ✅ Correct path
from typing import Optional

DIAGNOSIS_TASK_TYPE = "diagnosis"

def autonomous_diagnose(issue_id: str) -> Optional[dict]:
    print(f"🔬 Starting diagnosis for issue: {issue_id}")
    issue_details = platform_data_api.fetch_issue_details(issue_id)
    if not issue_details:
        print(f"❌ Issue not found: {issue_id}")
        return None

    logs = issue_details.get("logs", "")
    description = issue_details.get("description", "")
    error_msg = issue_details.get("error_message", "")

    prompt = f"""
You are an expert debugging agent. Analyze the following:

Issue: {issue_id}
Description: {description}
Error: {error_msg}
Logs:
{logs}

Return JSON with:
- "root_cause"
- "detailed_analysis"
- "relevant_files"
- "suggested_fix_areas"
- "confidence"
"""

    try:
        raw = call_ai_agent(DIAGNOSIS_TASK_TYPE, prompt)
        data = json.loads(raw)
        return data
    except Exception as e:
        traceback.print_exc()
        return {
            "error": "diagnosis_failed",
            "reason": str(e),
            "raw": raw if 'raw' in locals() else "no response"
        }
