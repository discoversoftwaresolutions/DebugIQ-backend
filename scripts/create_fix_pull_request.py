import traceback
from datetime import datetime
from scripts.platform_data_api import create_pull_request_on_platform

def create_pull_request(issue_id: str, branch_name: str, code_diff: str, diagnosis_details: dict, validation_results: dict) -> dict:
    try:
        print(f"📦 Creating PR for issue: {issue_id}")

        title = f"Fix: {diagnosis_details.get('root_cause', 'Unknown Issue')}"
        body = f"""
### 🧠 Diagnosis Summary
{diagnosis_details.get('detailed_analysis', 'N/A')}

### ✅ Validation Summary
{validation_results.get('ai_assessment', 'No AI assessment available.')}

### 🔧 Automated Patch
```diff
{code_diff[:500]}...
