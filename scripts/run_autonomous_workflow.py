import traceback
from scripts import (
    platform_data_api,
    autonomous_diagnose_issue,
    agent_suggest_patch,
    validate_proposed_patch,
    create_fix_pull_request
)

def run_workflow_for_issue(issue_id: str) -> dict:
    print(f"🔁 Starting autonomous workflow for issue: {issue_id}")
    result = {"issue_id": issue_id, "steps": []}

    try:
        platform_data_api.update_issue_status(issue_id, "Diagnosing")
        diagnosis = autonomous_diagnose_issue.autonomous_diagnose(issue_id)
        if not diagnosis:
            raise Exception("Diagnosis failed.")
        platform_data_api.store_diagnosis(issue_id, diagnosis)
        result["steps"].append("Diagnosis complete")

        platform_data_api.update_issue_status(issue_id, "Suggesting Patch")
        patch = agent_suggest_patch.agent_suggest_patch(issue_id, diagnosis)
        if not patch:
            raise Exception("Patch suggestion failed.")
        result["patch"] = patch
        platform_data_api.db[issue_id]["patch_suggestion"] = patch  # Mock store
        result["steps"].append("Patch suggested")

        platform_data_api.update_issue_status(issue_id, "Validating Patch")
        validation = validate_proposed_patch.validate_patch(issue_id, patch["patch"])
        if not validation.get("is_valid"):
            raise Exception("Patch validation failed.")
        platform_data_api.store_validation_results(issue_id, validation)
        result["steps"].append("Patch validated")

        platform_data_api.update_issue_status(issue_id, "Creating PR")
        pr = create_fix_pull_request.create_pull_request(
            issue_id=issue_id,
            branch_name=f"debugiq/fix-{issue_id.lower()}",
            code_diff=patch["patch"],
            diagnosis_details=diagnosis,
            validation_results=validation
        )
        result["pull_request"] = pr
        platform_data_api.update_issue_status(issue_id, "PR Created")
        result["steps"].append("Pull request created")

        print(f"✅ Workflow complete for issue: {issue_id}")
        return result

    except Exception as e:
        platform_data_api.update_issue_status(issue_id, "Workflow Failed")
        print(f"❌ Workflow error: {e}")
        traceback.print_exc()
        result["error"] = str(e)
        return result
