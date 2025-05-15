# backend/app/api/voice.py

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import base64

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router
router = APIRouter(tags=["Voice Agent"])

# Placeholder async functions for AI Service Calls (to be replaced with actual implementations)
async def transcribe_audio_async(audio_data_bytes: bytes) -> str:
    await asyncio.sleep(0.5)
    return "This is a simulated transcription response."

async def get_gemini_chat_response_async(prompt: str) -> str:
    await asyncio.sleep(1.0)
    return "This is a simulated Gemini chat response."

async def text_to_speech_async(text: str) -> bytes:
    await asyncio.sleep(0.5)
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00\x00\x00\x00\x00'

# Pydantic Models for Request Bodies
class TranscribeRequest(BaseModel):
    audio_base64: str
    format: str = "wav"

class ChatRequest(BaseModel):
    text: str

class TextToSpeechRequest(BaseModel):
    text: str

# Endpoints
@router.get("/voice/ping")
def voice_health_check():
    logger.info("Voice health check endpoint called.")
    return {"status": "ok", "message": "DebugIQ voice router is live."}

@router.post("/transcribe")
async def transcribe_audio(request: TranscribeRequest):
    logger.info("Received transcription request.")
    try:
        audio_data_bytes = base64.b64decode(request.audio_base64)
        transcribed_text = await transcribe_audio_async(audio_data_bytes)
        if not transcribed_text:
            transcribed_text = "[No speech detected]"
        return {"text": transcribed_text}
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Transcription failed.")

@router.post("/gemini/chat")
async def get_chat_response(request: ChatRequest):
    logger.info("Received chat request.")
    try:
        gemini_response_text = await get_gemini_chat_response_async(request.text)
        if not gemini_response_text:
            gemini_response_text = "I'm sorry, I didn't get a response."
        return {"text": gemini_response_text}
    except Exception as e:
        logger.error(f"Error during Gemini chat interaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gemini chat failed.")

@router.post("/tts")
async def text_to_speech(request: TextToSpeechRequest):
    logger.info("Received text-to-speech request.")
    try:
        audio_bytes = await text_to_speech_async(request.text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS service returned empty audio.")
        return audio_bytes
    except Exception as e:
        logger.error(f"Error during Text-to-Speech: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Text-to-Speech failed.")
