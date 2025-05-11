from fastapi import APIRouter
from pydantic import BaseModel
from scripts.utils.ai_api_client import call_ai_agent

router = APIRouter()

class VoiceCommand(BaseModel):
    command: str

@router.post("/voice/command")
def handle_voice_command(cmd: VoiceCommand):
    response = call_ai_agent("voice_command", cmd.command)
    return {"response": response}
