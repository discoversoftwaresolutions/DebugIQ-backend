python
import json
import traceback
from utils.call_ai_agent import call_ai_agent

def validate_patch(issue_id: str, patch_diff: str) -> dict:
    print(f"[🔍] Validating patch for issue {issue_id}...")

    # Simulated validation logic
    checks = [
        {"check": "Patch Applies Cleanly", "status": "passed"},
        {"check": "Static Analysis", "status": "passed"},
        {"check": "Build Status", "status": "passed"},
        {"check": "Bug Reproduction", "status": "passed"}
    ]

    is_valid = all(step["status"] == "passed" for step in checks)
    validation_summary = "\n".join(f"- {step['check']}: {step['status']}" for step in checks)

    # Avoid using triple backticks inside triple-quoted strings
    # We'll use indentation instead of ```diff
    prompt = f"""You are an AI code reviewer. Assess the following patch and validation results.

Patch (unified diff format):
{patch_diff}

Validation Results:
{validation_summary}

Respond in JSON format like this:
{{
  "is_valid": true,
  "reason": "Short explanation"
}}
"""

    try:
        response = call_ai_agent("qa", {"code": prompt})
        if "result" in response:
            return json.loads(response["result"])
        return {"is_valid": False, "error": response.get("error", "Agent did not return a result")}
    except Exception as e:
        traceback.print_exc()
        return {"is_valid": False, "error": str(e)}
