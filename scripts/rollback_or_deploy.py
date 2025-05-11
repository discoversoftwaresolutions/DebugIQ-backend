# DebugIQ-backend/scripts/rollback_or_deploy.py

import subprocess
import traceback
from scripts import platform_data_api

def deploy_patch(issue_id: str, validated_patch: dict) -> dict:
    """
    Deploys a patch to production or rolls back if errors are detected.

    Args:
        issue_id (str): The issue being resolved.
        validated_patch (dict): Contains keys like 'patch', 'is_valid', etc.

    Returns:
        dict: Deployment result or rollback reason.
    """
    try:
        print(f"🚀 Starting deployment for issue {issue_id}...")

        if not validated_patch.get("is_valid", False):
            raise Exception("Patch validation failed. Deployment aborted.")

        patch_diff = validated_patch.get("patch") or validated_patch.get("suggested_patch_diff")
        if not patch_diff:
            raise Exception("No patch diff provided for deployment.")

        branch_name = f"debugiq/deploy-{issue_id.lower()}"

        print(f"🔧 Applying patch and creating branch: {branch_name}")
        platform_data_api.apply_patch_and_create_branch(
            repository_url=platform_data_api.get_repository_info_for_issue(issue_id)["repository_url"],
            base_branch="main",
            new_branch_name=branch_name,
            patch_diff=patch_diff,
            issue_id=issue_id
        )

        pr_details = platform_data_api.create_pull_request_on_platform(
            issue_id=issue_id,
            branch_name=branch_name,
            base_branch="main",
            pr_title=f"Deploy: Auto-fix for issue {issue_id}",
            pr_body="Deploying auto-patch via DebugIQ agent."
        )

        return {
            "status": "success",
            "pr_url": pr_details.get("url", "unknown"),
            "message": f"Patch deployed successfully to branch: {branch_name}"
        }

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        traceback.print_exc()
        return {
            "status": "rollback",
            "reason": str(e),
            "message": f"Deployment aborted. Reason: {e}"
        }
