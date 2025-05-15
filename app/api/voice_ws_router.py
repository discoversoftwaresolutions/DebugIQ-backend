# backend/app/api/voice_ws_router.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import base64
import json
import traceback
import logging
import asyncio
import os # Import os for environment variables
import google.generativeai as genai # Import Gemini library
from google.cloud import speech # Import Google Cloud STT
from google.cloud import texttospeech # Import Google Cloud TTS

# Note: If your Google Cloud credentials are set up via GOOGLE_APPLICATION_CREDENTIALS
# environment variable in Railway, the clients should authenticate automatically.

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router
router = APIRouter(tags=["Voice WebSocket"])

# --- Google Cloud/Gemini Configuration ---
# Ensure these environment variables are set in Railway
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GOOGLE_APPLICATION_CREDENTIALS should be set for Google Cloud STT/TTS (path to service account key file)

# Configure Gemini API client (needed for conversational turns)
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini API configured for Voice WebSocket.")
        # Initialize Gemini model (you might need a model that supports chat turns)
        # gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or your preferred model
    except Exception as e:
        logger.error(f"Error configuring Gemini API for Voice WS: {e}", exc_info=True)
        GEMINI_API_KEY = None # Disable Gemini if configuration fails
else:
    logger.warning("GEMINI_API_KEY environment variable is not set. Gemini interaction will not work in Voice WS.")

# Initialize Google Cloud STT client
# Ensure GOOGLE_APPLICATION_CREDENTIALS env var is set in Railway
try:
    stt_client = speech.SpeechClient()
    logger.info("Google Cloud Speech-to-Text client initialized.")
except Exception as e:
    logger.error(f"Error initializing Google Cloud STT client: {e}", exc_info=True)
    stt_client = None # Disable STT if initialization fails

# Initialize Google Cloud TTS client
# Ensure GOOGLE_APPLICATION_CREDENTIALS env var is set in Railway
try:
    tts_client = texttospeech.TextToSpeechClient()
    logger.info("Google Cloud Text-to-Speech client initialized.")
except Exception as e:
    logger.error(f"Error initializing Google Cloud TTS client: {e}", exc_info=True)
    tts_client = None # Disable TTS if initialization fails


# --- Helper Function for Speech-to-Text ---
async def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Converts audio bytes to text using Google Cloud Speech-to-Text."""
    if not stt_client:
        logger.error("STT client not initialized. Cannot perform transcription.")
        return None

    # Configure the STT request
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, # Or the encoding of your incoming audio
        sample_rate_hertz=16000, # Or the sample rate of your incoming audio
        language_code="en-US", # Or the language code you expect
        # Add other configuration as needed, e.g., enable_automatic_punctuation=True
    )

    logger.debug("Sending audio to Google Cloud STT...")
    try:
        # Perform the transcription (synchronous call)
        # Note: For long audio or real-time streams, you'd use streaming recognition
        # This example assumes short audio chunks sent via WebSocket
        response = await asyncio.to_thread(stt_client.recognize, config=config, audio=audio)

        if response.results:
            # Get the first result and first alternative (most likely transcription)
            transcript = response.results[0].alternatives[0].transcript
            logger.info(f"Transcription successful: {transcript}")
            return transcript
        else:
            logger.info("Transcription successful, but no results returned.")
            return ""

    except Exception as e:
        logger.error(f"Error during Google Cloud STT transcription: {e}", exc_info=True)
        return None

# --- Helper Function for Gemini Conversational Response ---
# You might want to maintain conversation history per WebSocket connection
async def get_gemini_response(text: str, conversation_history: list) -> str | None:
    """Sends text to Gemini and gets a conversational text response."""
    if not GEMINI_API_KEY or not genai: # Check if Gemini was configured
         logger.error("Gemini not configured. Cannot get AI response.")
         return "AI service not available."

    try:
        # Initialize or get the chat session (example: creating a new one each time - inefficient)
        # A better approach is to store and reuse the chat_session per WebSocket connection
        # For simplicity in this example, let's simulate a single turn
        # If you need multi-turn chat, you'll need to manage 'conversation_history'
        # model = genai.GenerativeModel('gemini-1.5-flash-latest') # Initialize here or globally if safe
        # chat_session = model.start_chat(history=conversation_history) # Start chat with history

        # For a simple response generation (without history, like the old placeholder intent)
        # You could just use generate_content directly
        if not hasattr(router.state, 'gemini_model') or not router.state.gemini_model:
            logger.info("Initializing Gemini model in router state.")
            router.state.gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') # Cache model instance

        # Send the user's text to the Gemini model
        logger.debug(f"Sending text to Gemini: {text}")
        # Note: For streaming responses, use generate_content(..., stream=True)
        response = await router.state.gemini_model.generate_content(text)

        if hasattr(response, 'text') and response.text:
            logger.info("Received text response from Gemini.")
            return response.text.strip()
        else:
             # Handle cases where Gemini returns no text (e.g., blocked by safety)
             if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                  block_reason = response.prompt_feedback.block_reason
                  logger.warning(f"Gemini response blocked: {block_reason}. Raw response: {response}")
                  return f"AI response blocked by safety policy: {block_reason}"
             else:
                 logger.warning(f"Gemini generated no text response. Raw response: {response}")
                 return "AI generated no response."


    except Exception as e:
        logger.error(f"Error getting Gemini response: {e}", exc_info=True)
        return f"Error contacting AI: {e}"


# --- Helper Function for Text-to-Speech ---
async def synthesize_text_to_audio(text: str) -> bytes | None:
    """Converts text to audio bytes using Google Cloud Text-to-Speech."""
    if not tts_client:
        logger.error("TTS client not initialized. Cannot perform synthesis.")
        return None

    # Configure the TTS request
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Select the voice parameters (example: a standard US English voice)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL, # Or MALE/FEMALE
        # name="en-US-Standard-C" # Optional: specify a specific voice name
    )

    # Select the audio file type
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16, # Or MP3, OGG_OPUS, etc.
        sample_rate_hertz=16000 # Match expected client audio format
    )

    logger.debug(f"Synthesizing text to audio: {text[:100]}...")
    try:
        # Perform the text-to-speech conversion (synchronous call)
        response = await asyncio.to_thread(tts_client.synthesize_speech,
                                         input=synthesis_input,
                                         voice=voice,
                                         audio_config=audio_config)

        logger.info("TTS synthesis successful.")
        # The response's audio_content is binary audio data
        return response.audio_content

    except Exception as e:
        logger.error(f"Error during Google Cloud TTS synthesis: {e}", exc_info=True)
        return None


@router.websocket("/voice/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection accepted.")
    await websocket.accept()

    # You might want to initialize or retrieve conversation history here per connection
    # For simplicity in this example, we'll treat each voice input as a new turn
    # without explicit multi-turn history management in this function scope.

    try:
        while True:
            try:
                # Receive incoming messages (expecting text with JSON payload)
                raw_msg = await websocket.receive_text()
                logger.debug(f"Received raw WebSocket message: {raw_msg[:200]}...")
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during receive.")
                break # Exit the loop on disconnect

            try:
                # Parse the JSON payload
                data = json.loads(raw_msg)
                logger.debug(f"Parsed WebSocket data: {data}")
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON on WebSocket: {raw_msg[:100]}...")
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON format"}))
                continue # Skip to the next message

            msg_type = data.get("type")
            logger.debug(f"Received WebSocket message type: {msg_type}")

            # --- Handle different message types ---
            if msg_type == "voice_input":
                # --- Step 1: Receive and Transcribe Audio ---
                audio_b64 = data.get("audio_base64")
                if not audio_b64:
                    logger.warning("Received voice_input message with missing audio_base64.")
                    await websocket.send_text(json.dumps({"type": "error", "message": "Missing audio_base64 in voice_input"}))
                    continue

                try:
                    audio_data_bytes = base64.b64decode(audio_b64)
                    logger.info(f"Received {len(audio_data_bytes)} bytes of audio.")

                    # Perform STT
                    transcribed_text = await transcribe_audio(audio_data_bytes)

                    if transcribed_text is None: # Handle STT failure
                        await websocket.send_text(json.dumps({"type": "error", "message": "Speech-to-Text failed."}))
                        continue
                    elif transcribed_text == "": # Handle no speech detected
                         await websocket.send_text(json.dumps({"type": "info", "message": "No speech detected."}))
                         logger.info("No speech detected by STT.")
                         continue


                    # Send back the transcription as an intermediate result
                    await websocket.send_text(json.dumps({"type": "transcription", "text": transcribed_text}))
                    logger.info(f"Sent transcription: '{transcribed_text[:100]}...'")

                    # --- Step 2: Process Transcription with Gemini ---
                    # Here you would send the transcribed_text to Gemini
                    # You might need logic to determine intent vs. conversational chat
                    # For a simple conversation, just pass the text to Gemini
                    # If you need to trigger the autonomous workflow, you'd add intent detection logic here
                    # based on the 'transcribed_text'. The old process_voice_intent did this.
                    # Let's assume for now we send the text to Gemini for a response.

                    # Example: Simple check for workflow trigger phrase (like the old placeholder)
                    # Or send the text to Gemini for general conversation
                    if "run autonomous workflow for issue" in transcribed_text.lower():
                         logger.info("Detected potential workflow trigger phrase.")
                         # You might still want Gemini to confirm or respond conversationally
                         # For now, let's prioritize Gemini response first, then potentially trigger workflow

                         # Process the text for a conversational response using Gemini
                         gemini_text_response = await get_gemini_response(transcribed_text, []) # Pass empty history for now
                         if gemini_text_response is None: # Handle Gemini failure
                              await websocket.send_text(json.dumps({"type": "error", "message": "AI response generation failed."}))
                              continue

                         # Send the text response back before sending audio
                         await websocket.send_text(json.dumps({"type": "ai_response_text", "text": gemini_text_response}))
                         logger.info(f"Sent AI text response: '{gemini_text_response[:100]}...'")

                         # --- Step 3: Synthesize Gemini's Response to Audio ---
                         audio_response_bytes = await synthesize_text_to_audio(gemini_text_response)

                         if audio_response_bytes is None: # Handle TTS failure
                              await websocket.send_text(json.dumps({"type": "error", "message": "Text-to-Speech failed."}))
                              continue

                         # --- Step 4: Send Audio Response Back ---
                         audio_response_b64 = base64.b64encode(audio_response_bytes).decode("utf-8")
                         await websocket.send_text(json.dumps({
                             "type": "ai_response_audio",
                             "format": "linear16", # Or the encoding used by TTS
                             "audio_base64": audio_response_b64
                         }))
                         logger.info(f"Sent {len(audio_response_bytes)} bytes of audio response.")


                         # --- Optional: Trigger Workflow After AI Response (if intent detected) ---
                         # If you still want to trigger the autonomous workflow based on transcription,
                         # you would add that logic here AFTER the AI response, or branch earlier
                         # For example, check 'transcribed_text' for the trigger phrase again here
                         if "run autonomous workflow for issue" in transcribed_text.lower():
                             try:
                                 from app.api.autonomous_router import run_workflow_orchestrator
                                 # Extract issue ID (you'll need robust parsing here)
                                 parts = transcribed_text.lower().split("run autonomous workflow for issue")
                                 if len(parts) > 1:
                                     issue_id = parts[1].strip().split()[0] # Basic split
                                     logger.info(f"Triggering autonomous workflow in background for issue: {issue_id}")
                                     # Trigger the workflow in a background task
                                     asyncio.create_task(run_workflow_orchestrator(issue_id))
                                     await websocket.send_text(json.dumps({
                                         "type": "workflow_trigger_status",
                                         "status": "accepted",
                                         "issue_id": issue_id,
                                         "message": f"Autonomous workflow triggered for issue {issue_id}. Check status tab."
                                     }))
                                 else:
                                     logger.warning("Workflow trigger phrase detected but could not extract issue ID.")
                                     await websocket.send_text(json.dumps({"type": "info", "message": "Detected workflow trigger phrase but could not extract issue ID."}))
                             except ImportError:
                                 logger.error("Could not import run_workflow_orchestrator.")
                                 await websocket.send_text(json.dumps({"type": "error", "message": "Internal error: Workflow orchestrator not available."}))
                             except Exception as wf_e:
                                 logger.error(f"Error triggering workflow: {wf_e}", exc_info=True)
                                 await websocket.send_text(json.dumps({"type": "error", "message": f"Error triggering workflow: {wf_e}"}))


                    else:
                         # If no specific workflow trigger phrase, just get Gemini conversational response and speak it back
                         gemini_text_response = await get_gemini_response(transcribed_text, []) # Pass empty history for now
                         if gemini_text_response is None: # Handle Gemini failure
                              await websocket.send_text(json.dumps({"type": "error", "message": "AI response generation failed."}))
                              continue

                         # Send the text response back before sending audio
                         await websocket.send_text(json.dumps({"type": "ai_response_text", "text": gemini_text_response}))
                         logger.info(f"Sent AI text response: '{gemini_text_response[:100]}...'")

                         # --- Step 3: Synthesize Gemini's Response to Audio ---
                         audio_response_bytes = await synthesize_text_to_audio(gemini_text_response)

                         if audio_response_bytes is None: # Handle TTS failure
                              await websocket.send_text(json.dumps({"type": "error", "message": "Text-to-Speech failed."}))
                              continue

                         # --- Step 4: Send Audio Response Back ---
                         audio_response_b64 = base64.b64encode(audio_response_bytes).decode("utf-8")
                         await websocket.send_text(json.dumps({
                             "type": "ai_response_audio",
                             "format": "linear16", # Or the encoding used by TTS
                             "audio_base64": audio_response_b64
                         }))
                         logger.info(f"Sent {len(audio_response_bytes)} bytes of audio response.")


                except Exception as e:
                    logger.error(f"Error processing voice input message: {e}", exc_info=True)
                    await websocket.send_text(json.dumps({"type": "error", "message": f"An internal error occurred: {e}"}))

            # Handle other message types if necessary
            elif msg_type:
                logger.warning(f"Received unhandled message type on WebSocket: {msg_type}")
                await websocket.send_text(json.dumps({"type": "error", "message": f"Unhandled message type: {msg_type}"}))
            else:
                 logger.warning("Received WebSocket message with no 'type' field.")
                 await websocket.send_text(json.dumps({"type": "error", "message": "Message missing 'type' field."}))


    except WebSocketDisconnect:
        # This block handles disconnections that occur outside the inner receive loop
        logger.info("WebSocket connection closed.")

    except Exception as e:
        # Catch any unexpected errors in the main WebSocket processing
        logger.error(f"Unexpected error in WebSocket connection: {e}", exc_info=True)
        try:
            # Attempt to send an error message before closing the connection
            await websocket.send_text(json.dumps({"type": "error", "message": f"A critical error occurred: {e}"}))
        except:
            # Ignore errors if sending the error message fails (connection might be closed)
            pass

# Note: You will need to install the necessary Google Cloud client libraries:
# pip install google-cloud-speech google-cloud-texttospeech
# Also ensure you have Google Cloud authentication set up in your Railway environment,
# typically by setting the GOOGLE_APPLICATION_CREDENTIALS environment variable
# to the path of your service account key file.
# Ensure GEMINI_API_KEY is also set for Gemini interaction.
