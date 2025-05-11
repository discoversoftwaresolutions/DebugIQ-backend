from fastapi import APIRouter
from scripts.platform_data_api import query_issues_by_status

router = APIRouter()

@router.get("/issues/inbox", tags=["Issues"])
def get_new_issues():
    try:
        issues = query_issues_by_status("New")
        return {"issues": issues}
    except Exception as e:
        return {"error": str(e), "status": "failed to fetch inbox"}


@router.get("/issues/attention-needed", tags=["Issues"])
def get_issues_needing_attention():
    try:
        issues = query_issues_by_status([
            "Diagnosis Failed - AI Analysis",
            "Validation Failed - Manual Review",
            "PR Creation Failed - Needs Review",
            "QA Failed - Needs Review"
        ])
        return {"issues": issues}
    except Exception as e:
        return {"error": str(e), "status": "failed to fetch attention-needed list"}
