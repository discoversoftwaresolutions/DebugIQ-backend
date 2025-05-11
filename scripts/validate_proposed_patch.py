import json
import traceback
from utils.call_ai_agent import call_ai_agent

def validate_patch(issue_id: str, patch_diff: str) -> dict:
    print(f"[🔍] Validating patch for issue {issue_id}...")

    # Simulate some checks — in real world, integrate test runners, linters, etc.
    checks = [
        {"check": "Patch Applies Cleanly", "status": "passed"},
        {"check": "Static Analysis", "status": "passed"},
        {"check": "Build Status", "status": "passed"},
        {"check": "Bug Reproduction", "status": "passed"}
    ]

    is_valid = all(step["status"] == "passed" for step in checks)

    prompt = f"""
Given the following patch and validation results, summarize whether it is safe to proceed.

Patch:
```diff
{patch_diff}
