# In your voice_ws_router.py file
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64
import json
import traceback # Keep traceback import for detailed exception logging
# Optional: Gemini/GPT fallback logic here
# --- CORRECTION: Import the actual orchestrator function ---
# Assuming run_workflow_orchestrator is in autonomous_router.py
from app.api.autonomous_router import run_workflow_orchestrator # Import the specific function
from scripts import platform_data_api # Assume platform_data_api is available if needed

# Setup logger for this module
import logging # Import logging
logger = logging.getLogger(__name__)


# Initialize the router WITHOUT a prefix. The prefix is applied in main.py (or not, in this case).
# Since main.py includes this router without a prefix, paths here must be the full paths (e.g., /voice/ws).
router = APIRouter(tags=["Voice WebSocket"]) # Added tags


# --- CORRECTION HERE ---
# Remove the duplicate /voice/ping endpoint defined in voice.py
# If you need a ping for the WebSocket specifically, define a different path
# @router.get("/voice/ping")
# async def voice_ws_health_check():
#     """
#     Quick health check for DebugIQ Voice WebSocket Router.
#     """
#     logger.info("Voice WS health check endpoint called.") # Use logger
#     return {"status": "ok", "message": "Voice WS router is live."}


@router.websocket("/voice/ws") # Define the full path
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection accepted.") # Use logger
    await websocket.accept()
    try:
        while True:
            # --- Use specific exception handling for receiving data ---
            try:
                raw_msg = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during receive.") # Use logger
                break # Exit the loop on disconnect

            try:
                data = json.loads(raw_msg)
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON on WebSocket: {raw_msg[:100]}...") # Use logger
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                continue # Continue loop, ignore this message

            msg_type = data.get("type")
            logger.debug(f"Received WebSocket message type: {msg_type}") # Log received type

            if msg_type == "voice_input":
                audio_b64 = data.get("audio_base64")
                if not audio_b64:
                    logger.warning("Received voice_input message with missing audio_base64.") # Use logger
                    await websocket.send_text(json.dumps({"error": "Missing audio_base64 in voice_input"}))
                    continue

                # --- Implement actual transcription and AI logic ---
                try:
                    audio_data_bytes = base64.b64decode(audio_b64)
                    logger.info(f"Processing {len(audio_data_bytes)} bytes of audio for transcription.")

                    # Assume you have an async transcription function available
                    # from backend.app.api.voice import transcribe_audio_async # Example reuse from voice.py
                    # Or define/import it here:
                    async def transcribe_audio_ws(audio_bytes: bytes) -> str:
                         logger.warning("Placeholder: transcribe_audio_ws called. Replace with actual STT API call.")
                         await asyncio.sleep(0.5)
                         return "run autonomous workflow for issue ISSUE-101" # Mock transcript

                    transcribed_text = await transcribe_audio_ws(audio_data_bytes) # Await transcription

                    await websocket.send_text(json.dumps({"type": "intermediate_transcript", "text": transcribed_text}))
                    logger.info(f"Sent intermediate transcript: '{transcribed_text[:100]}...'")


                    # Assume you have an async function for AI intent handling/chat
                    # This would take the transcribed text and potentially conversation history
                    async def process_voice_intent(text: str) -> dict:
                         logger.warning("Placeholder: process_voice_intent called. Replace with actual AI/intent logic.")
                         await asyncio.sleep(0.5)
                         # Mock intent handling
                         if "run autonomous workflow for issue" in text.lower():
                             # Simple regex or string splitting to extract ID
                             parts = text.lower().split("run autonomous workflow for issue")
                             if len(parts) > 1:
                                 issue_id = parts[1].strip().split()[0] # Get first word after phrase
                                 return {"action": "run_workflow", "issue_id": issue_id}
                             else:
                                 return {"action": "unknown_intent", "message": "Could not extract issue ID."}
                         else:
                              return {"action": "unknown_intent", "message": "No matching agent trigger."}


                    intent_result = await process_voice_intent(transcribed_text) # Await intent processing

                    await websocket.send_text(json.dumps({"type": "intent", **intent_result})) # Send intent details
                    logger.info(f"Sent intent result: {intent_result}")


                    # --- Handle specific intents ---
                    if intent_result.get("action") == "run_workflow" and intent_result.get("issue_id"):
                        issue_id_to_trigger = intent_result["issue_id"]
                        logger.info(f"Triggering autonomous workflow for issue: {issue_id_to_trigger}")

                        # --- CORRECTION HERE: Trigger workflow as a background task ---
                        # Use asyncio.create_task to run the orchestrator in the background
                        # This is crucial to prevent blocking the WebSocket loop.
                        import asyncio # Ensure asyncio is imported
                        # Assumes run_workflow_orchestrator is async and accepts issue_id
                        asyncio.create_task(run_workflow_orchestrator(issue_id_to_trigger))
                        logger.info(f"Autonomous workflow triggered in background for issue {issue_id_to_trigger}.")

                        # Send a message back confirming workflow is starting
                        await websocket.send_text(json.dumps({
                            "type": "workflow_trigger_status",
                            "status": "accepted",
                            "issue_id": issue_id_to_trigger,
                            "message": f"Autonomous workflow triggered for issue {issue_id_to_trigger}. Check status tab."
                        }))

                    # If the workflow orchestrator completes and you need to send a final result
                    # back over THIS WebSocket connection, the orchestrator would need a way
                    # to send messages back to this specific websocket. This is complex
                    # and typically involves storing the websocket connection or using a pub/sub system.
                    # A simpler approach is for the client to poll the /issues/{issue_id}/status endpoint.
                    # The "final_result" message might better be sent by the orchestrator if it has the websocket reference,
                    # but for now, just confirming trigger is sufficient for the client.

                elif intent_result.get("action") == "unknown_intent":
                    # Handle unknown intent - maybe call Gemini for a general chat response
                    logger.info("Handling unknown intent.")
                    async def get_general_ai_response(text: str) -> str:
                        logger.warning("Placeholder: get_general_ai_response called for unknown intent. Replace with actual Gemini chat.")
                        await asyncio.sleep(1.0)
                        return f"I didn't understand that. You said: '{text}'" # Mock response

                    ai_response = await get_general_ai_response(transcribed_text)
                    await websocket.send_text(json.dumps({
                        "type": "chat_response",
                        "text": ai_response,
                        "message": "Here's a general AI response based on your input."
                    }))
                    logger.info("Sent general AI response for unknown intent.")


            else:
                logger.warning(f"Received unhandled message type on WebSocket: {msg_type}") # Use logger
                await websocket.send_text(json.dumps({"error": f"Unhandled message type: {msg_type}"}))


        except Exception as e:
            # Catch any unexpected errors during processing a specific message
            logger.error(f"Error processing WebSocket message: {e}", exc_info=True) # Use logger and include traceback
            await websocket.send_text(json.dumps({"error": f"An internal error occurred: {e}"}))


    except WebSocketDisconnect:
        logger.info("🔌 WebSocket connection closed.") # Use logger

    except Exception as e:
        # Catch any unexpected errors outside the message processing loop
        logger.error(f"An unexpected error occurred in the WebSocket connection handler: {e}", exc_info=True) # Use logger
        # Attempt to send error before closing, but connection might be broken
        try:
            await websocket.send_text(json.dumps({"error": f"A critical error occurred: {e}"}))
        except:
            pass # Ignore errors during sending error message


# Note: This file defines the voice websocket router. It should be included in main.py
# using app.include_router(router, tags=["Voice WebSocket"]).
