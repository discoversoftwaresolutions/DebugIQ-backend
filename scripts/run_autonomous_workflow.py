import traceback
from scripts import (
    autonomous_diagnose_issue,
    agent_suggest_patch,
    validate_proposed_patch,
    create_fix_pull_request,
    platform_data_api
)

def run_workflow_for_issue(issue_id: str) -> dict:
    print(f"🔁 Starting autonomous workflow for issue: {issue_id}")
    try:
        platform_data_api.update_issue_status(issue_id, "Diagnosing")
        diagnosis = autonomous_diagnose_issue.autonomous_diagnose(issue_id)
        if not diagnosis:
            return {"error": "Diagnosis failed."}
        platform_data_api.store_diagnosis(issue_id, diagnosis)

        platform_data_api.update_issue_status(issue_id, "Suggesting Patch")
        patch = agent_suggest_patch.agent_suggest_patch(issue_id, diagnosis)
        if not patch:
            return {"error": "Patch suggestion failed."}
        platform_data_api.store_patch_suggestion(issue_id, patch)

        platform_data_api.update_issue_status(issue_id, "Validating Patch")
        validation = validate_proposed_patch.validate_patch(issue_id, patch["patch"])
        if not validation["is_valid"]:
            return {"error": "Validation failed.", "details": validation}
        platform_data_api.store_validation_results(issue_id, validation)

        platform_data_api.update_issue_status(issue_id, "Creating Pull Request")
        pr = create_fix_pull_request.create_pull_request(
            issue_id=issue_id,
            branch_name=f"debugiq/fix-{issue_id.lower()}",
            code_diff=patch["patch"],
            diagnosis_details=diagnosis,
            validation_results=validation
        )

        platform_data_api.update_issue_status(issue_id, "Complete")
        return {
            "status": "Workflow Complete",
            "diagnosis": diagnosis,
            "patch": patch,
            "validation": validation,
            "pull_request": pr
        }

    except Exception as e:
        platform_data_api.update_issue_status(issue_id, "Workflow Error")
        traceback.print_exc()
        return {"error": f"Workflow failed: {str(e)}"}
