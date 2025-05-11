import traceback
from scripts.platform_data_api import create_new_issue, update_issue_status
from scripts.utils.ai_api_client import call_ai_agent

TRIAGE_TASK_TYPE = "issue_triage"

def ingest_and_triage(raw_data: dict) -> dict:
    """
    Ingests raw issue data (logs, messages) and uses AI to structure it.

    Returns:
        - issue_id
        - AI-generated title, description
        - status
    """
    try:
        print(f"📥 Ingesting raw issue: {raw_data}")

        triage_prompt = f"""
You are an intelligent triage agent.

Input:
{raw_data}

Tasks:
1. Generate a concise issue title.
2. Write a helpful issue description.
3. Estimate severity (low, medium, high).
4. Recommend one or two potentially relevant file names (best guess).

Respond in JSON:
"title": string,
"description": string,
"severity": string,
"relevant_files": list of strings
"""

        ai_response = call_ai_agent(TRIAGE_TASK_TYPE, triage_prompt)

        import json
        structured = json.loads(ai_response)

        issue_data = {
            "title": structured.get("title", "Untitled Issue"),
            "description": structured.get("description", "No description provided."),
            "severity": structured.get("severity", "medium"),
            "relevant_files": structured.get("relevant_files", []),
            "raw_data": raw_data,
        }

        issue_id = create_new_issue(issue_data)
        update_issue_status(issue_id, "Triage Complete")

        return {"issue_id": issue_id, "status": "triaged", **issue_data}

    except Exception as e:
        print(f"❌ Issue triage failed: {e}")
        traceback.print_exc()
        return {"error": str(e)}
