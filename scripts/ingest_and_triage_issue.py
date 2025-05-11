from scripts import platform_data_api
from utils.ai_api_client import call_ai_agent

TRIAGE_TASK_TYPE = "triage"

def ingest_and_triage(raw_data: dict) -> dict:
    """
    Parses raw error data and structures it into a DebugIQ issue schema using AI.
    """
    print(f"📥 Ingesting raw issue data...")
    prompt = f"""
Given the following raw error report, monitoring log, or crash message, structure it as a new issue.
Return the output as a JSON object with the keys:
- title
- description
- logs
- error_message
- relevant_files

Raw Data:
{raw_data}
"""
    try:
        ai_response = call_ai_agent(task_type=TRIAGE_TASK_TYPE, prompt=prompt)
        structured_issue = {
            "title": "Unknown",
            "description": "Raw error data could not be parsed.",
            "logs": str(raw_data),
            "error_message": "Unparsed",
            "relevant_files": []
        }

        # Simple JSON parsing fallback
        import json
        ai_json = json.loads(ai_response)
        structured_issue.update(ai_json)

        # Check for duplicate
        duplicate_found, existing_id = platform_data_api.find_duplicate_issue(structured_issue)
        if duplicate_found:
            print(f"⚠️ Duplicate issue detected: {existing_id}")
            return {"duplicate": True, "existing_issue_id": existing_id}

        new_issue_id = platform_data_api.create_new_issue(structured_issue)
        print(f"✅ New issue created: {new_issue_id}")
        return {"duplicate": False, "issue_id": new_issue_id, "issue": structured_issue}

    except Exception as e:
        print(f"❌ Error during triage: {e}")
        return {"error": str(e)}
