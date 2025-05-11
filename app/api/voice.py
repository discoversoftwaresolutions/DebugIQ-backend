from fastapi import APIRouter

router = APIRouter()

@router.get("/voice/ping")
def voice_health_check():
    return {"status": "ok", "message": "DebugIQ voice router is live."}
