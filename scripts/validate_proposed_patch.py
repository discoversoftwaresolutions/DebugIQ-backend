import json
import traceback
from utils.call_ai_agent import call_ai_agent

def validate_patch(issue_id: str, patch_diff: str) -> dict:
    print(f"[🔍] Validating patch for issue {issue_id}...")

    # Simulate validation checks
    checks = [
        {"check": "Patch Applies Cleanly", "status": "passed"},
        {"check": "Static Analysis", "status": "passed"},
        {"check": "Build Status", "status": "passed"},
        {"check": "Bug Reproduction", "status": "passed"}
    ]

    is_valid = all(step["status"] == "passed" for step in checks)

    # Build readable validation summary
    validation_summary = "\n".join(f"- {c['check']}: {c['status']}" for c in checks)

    prompt = f"""
You are a code reviewer AI. Assess the following patch and validation results.
Determine whether this patch should be accepted and summarize the reasoning.

Patch:
```diff
{patch_diff}
