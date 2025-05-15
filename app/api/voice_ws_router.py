from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64
import json
import traceback
import logging
import asyncio
from app.api.autonomous_router import run_workflow_orchestrator

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router
router = APIRouter(tags=["Voice WebSocket"])

@router.websocket("/voice/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection accepted.")
    await websocket.accept()
    try:
        while True:
            try:
                raw_msg = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during receive.")
                break

            try:
                data = json.loads(raw_msg)
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON on WebSocket: {raw_msg[:100]}...")
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                continue

            msg_type = data.get("type")
            logger.debug(f"Received WebSocket message type: {msg_type}")

            if msg_type == "voice_input":
                audio_b64 = data.get("audio_base64")
                if not audio_b64:
                    logger.warning("Received voice_input message with missing audio_base64.")
                    await websocket.send_text(json.dumps({"error": "Missing audio_base64 in voice_input"}))
                    continue

                try:
                    audio_data_bytes = base64.b64decode(audio_b64)
                    logger.info(f"Processing {len(audio_data_bytes)} bytes of audio for transcription.")

                    # Placeholder transcription function
                    async def transcribe_audio_ws(audio_bytes: bytes) -> str:
                        logger.warning("Placeholder: transcribe_audio_ws called. Replace with actual STT API call.")
                        await asyncio.sleep(0.5)
                        return "run autonomous workflow for issue ISSUE-101"

                    transcribed_text = await transcribe_audio_ws(audio_data_bytes)

                    await websocket.send_text(json.dumps({"type": "intermediate_transcript", "text": transcribed_text}))
                    logger.info(f"Sent intermediate transcript: '{transcribed_text[:100]}...'")

                    # Placeholder intent processing function
                    async def process_voice_intent(text: str) -> dict:
                        logger.warning("Placeholder: process_voice_intent called. Replace with actual AI/intent logic.")
                        await asyncio.sleep(0.5)
                        if "run autonomous workflow for issue" in text.lower():
                            parts = text.lower().split("run autonomous workflow for issue")
                            if len(parts) > 1:
                                issue_id = parts[1].strip().split()[0]
                                return {"action": "run_workflow", "issue_id": issue_id}
                            else:
                                return {"action": "unknown_intent", "message": "Could not extract issue ID."}
                        else:
                            return {"action": "unknown_intent", "message": "No matching agent trigger."}

                    intent_result = await process_voice_intent(transcribed_text)
                    await websocket.send_text(json.dumps({"type": "intent", **intent_result}))
                    logger.info(f"Sent intent result: {intent_result}")

                    if intent_result.get("action") == "run_workflow" and intent_result.get("issue_id"):
                        issue_id_to_trigger = intent_result["issue_id"]
                        logger.info(f"Triggering autonomous workflow for issue: {issue_id_to_trigger}")
                        asyncio.create_task(run_workflow_orchestrator(issue_id_to_trigger))
                        logger.info(f"Autonomous workflow triggered in background for issue {issue_id_to_trigger}.")
                        await websocket.send_text(json.dumps({
                            "type": "workflow_trigger_status",
                            "status": "accepted",
                            "issue_id": issue_id_to_trigger,
                            "message": f"Autonomous workflow triggered for issue {issue_id_to_trigger}. Check status tab."
                        }))

                except Exception as e:
                    logger.error(f"Error during processing voice input: {e}", exc_info=True)
                    await websocket.send_text(json.dumps({"error": f"An internal error occurred: {e}"}))

            elif msg_type:
                logger.warning(f"Received unhandled message type on WebSocket: {msg_type}")
                await websocket.send_text(json.dumps({"error": f"Unhandled message type: {msg_type}"}))

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}", exc_info=True)
        try:
            await websocket.send_text(json.dumps({"error": f"A critical error occurred: {e}"}))
        except:
            pass
