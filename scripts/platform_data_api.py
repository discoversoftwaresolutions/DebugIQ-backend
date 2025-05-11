from scripts.mock_db import db
import logging

logger = logging.getLogger(__name__)


def query_issues_by_status(status_filter):
    """
    Filters issues from the in-memory DB based on status or list of statuses.
    """
    if isinstance(status_filter, str):
        status_filter = [status_filter]

    try:
        matching = [
            issue for issue in db.values()
            if issue.get("status") in status_filter
        ]
        logger.info(f"[platform_data_api] Found {len(matching)} issues matching {status_filter}")
        return matching
    except Exception as e:
        logger.error(f"[platform_data_api] Failed to query issues by status: {e}")
        return []
