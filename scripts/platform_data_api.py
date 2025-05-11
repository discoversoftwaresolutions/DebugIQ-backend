import logging
from scripts.mock_db import db

logger = logging.getLogger(__name__)


def get_repository_info_for_issue(issue_id: str) -> dict:
    """
    Returns repository metadata for a given issue ID.
    """
    issue = db.get(issue_id)
    if not issue:
        logger.warning(f"[platform_data_api] No issue found for ID: {issue_id}")
        return {"error": "Issue not found"}

    repository_url = issue.get("repository")
    if not repository_url:
        logger.warning(f"[platform_data_api] No repository linked to issue {issue_id}")
        return {"error": "No repository linked"}

    return {
        "issue_id": issue_id,
        "repository_url": repository_url,
        "linked_files": issue.get("relevant_files", []),
    }


def fetch_code_context(repository_url: str, file_paths: list[str], commit_hash: str = None) -> str:
    """
    Simulates fetching source code from given repository and files.
    Replace with actual Git fetch or GitHub API integration later.
    """
    if not repository_url or not file_paths:
        logger.warning("[platform_data_api] Missing repo URL or file paths.")
        return "# Error: Missing repository URL or file paths."

    # TODO: Integrate Git fetcher or GitHub API
    content = [
        f"# --- Simulated content from: {file} ---\nprint('This is a stub from {file}')"
        for file in file_paths
    ]
    return "\n\n".join(content)
