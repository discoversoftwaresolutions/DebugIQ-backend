# File: DebugIQ-backend/app/api/voice_ws_router.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64
import json
import traceback

# Optional: Gemini/GPT fallback logic here
from scripts import run_autonomous_workflow, platform_data_api

router = APIRouter()

@router.get("/voice/ping")
async def voice_ws_health_check():
    """
    Quick health check for DebugIQ Voice WebSocket Router.
    """
    return {"status": "ok", "message": "Voice WS router is live."}

@router.websocket("/voice/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)

            if data.get("type") != "voice_input":
                await websocket.send_text(json.dumps({"error": "Unsupported message type"}))
                continue

            audio_b64 = data.get("audio_base64")
            if not audio_b64:
                await websocket.send_text(json.dumps({"error": "Missing audio_base64"}))
                continue

            # Simulate Gemini processing here (replace with actual API call)
            simulated_text = "run autonomous workflow for issue ISSUE-101"
            await websocket.send_text(json.dumps({"type": "intermediate_transcript", "text": simulated_text}))

            # Intent handling (mocked for now)
            if "run autonomous" in simulated_text:
                issue_id = "ISSUE-101"  # extract from intent in future
                await websocket.send_text(json.dumps({"type": "intent", "action": "run_workflow", "issue_id": issue_id}))

                # Trigger agent workflow
                result = run_autonomous_workflow.run_workflow_for_issue(issue_id)
                await websocket.send_text(json.dumps({
                    "type": "final_result",
                    "message": "Autonomous workflow complete",
                    "result": result
                }))
            else:
                await websocket.send_text(json.dumps({"type": "unknown_intent", "message": "No matching agent trigger"}))

    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
    except Exception as e:
        traceback.print_exc()
        await websocket.send_text(json.dumps({"error": str(e)}))
