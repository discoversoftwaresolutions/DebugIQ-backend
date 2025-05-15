# backend/utils/call_ai_agent.py

import os
# --- IMPORTANT --- Replace 'requests' with an async HTTP client like 'httpx'
# import requests # REMOVE or comment out the synchronous requests library
import httpx # Import the asynchronous HTTP client
import logging # Import logging
import json # Import json for parsing responses
# import traceback # Keep traceback if needed for detailed logging within complex handlers

# Setup logger for this module
logger = logging.getLogger(__name__)

# --- Configuration ---
# These should be securely managed in production via environment variables.
# Raise an error if critical keys are missing instead of providing insecure defaults.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check for required API keys at startup
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable not set. OpenAI API calls will fail.")
    # Consider raising a ValueError here if OpenAI is critical for startup
    # raise ValueError("OPENAI_API_KEY environment variable is missing")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. Gemini API calls will fail.")
    # Gemini might be less critical depending on features used, so maybe just a warning is okay.

# Define base URLs (adjust if using self-hosted or different endpoints)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
# Construct Gemini URL securely
if GEMINI_API_KEY:
    # Using f-string for cleaner URL construction
    GEMINI_GENERATE_CONTENT_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
else:
    GEMINI_GENERATE_CONTENT_URL = None # Set to None if key is missing

GPT_MODEL = "gpt-4o" # Or your preferred GPT model

# --- Helper async functions for specific AI API calls ---

# --- CORRECTION HERE ---
# Convert to async def
# Accept prompt string directly as this is how workflow scripts prepare it
async def _call_openai_chat(prompt: str, model: str = GPT_MODEL, temperature: float = 0.2) -> str | None:
    """
    Calls OpenAI's Chat Completions API asynchronously.

    Args:
        prompt (str): The text prompt to send to the model.
        model (str): The OpenAI model name (default: GPT_MODEL).
        temperature (float): The sampling temperature (default: 0.2).

    Returns:
        str | None: The text content of the AI response, or None on failure.
    """
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set. Cannot call OpenAI API.")
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": model,
        "messages": [
            # Consider adding a system message based on the task if not already in prompt
            # {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        # Add other parameters as needed (e.g., max_tokens, response_format)
    }

    try:
        logger.debug(f"Calling OpenAI chat API for prompt: {prompt[:100]}...") # Log prompt snippet
        # --- CORRECTION HERE ---
        # Replace requests.post with await httpx.post
        async with httpx.AsyncClient(timeout=25) as client: # Use async client with context manager
            res = await client.post(OPENAI_CHAT_COMPLETIONS_URL, headers=headers, json=body) # AWAIT the call
            res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the JSON response
        response_data = res.json()

        # Extract the content safely
        content = response_data.get("choices", [])[0].get("message", {}).get("content") if response_data.get("choices") else None

        if content is None:
             logger.warning(f"OpenAI chat response did not contain expected content structure. Raw response: {response_data}")

        logger.debug("OpenAI chat API call successful.")
        return content

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI API HTTP error: {e} - Response: {e.response.text}", exc_info=True)
        return None
    except httpx.RequestError as e:
        logger.error(f"OpenAI API request error: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred calling OpenAI API: {e}", exc_info=True)
        return None


# --- CORRECTION HERE ---
# Convert to async def
# Accept prompt string directly
async def _call_gemini_generate_content(prompt: str, model: str = "gemini-pro", temperature: float = 0.2) -> str | None:
    """
    Calls Gemini's generateContent API asynchronously.

    Args:
        prompt (str): The text prompt to send to the model.
        model (str): The Gemini model name (default: gemini-pro).
        temperature (float): The sampling temperature (default: 0.2).

    Returns:
        str | None: The text content of the AI response, or None on failure.
    """
    if not GEMINI_API_KEY or not GEMINI_GENERATE_CONTENT_URL:
        logger.error("GEMINI_API_KEY is not set. Cannot call Gemini API.")
        return None

    # Headers are often minimal for Google APIs using key in URL
    headers = {"Content-Type": "application/json"}

    body = {
        "contents": [
            # Consider adding a system instruction if appropriate for the model/task
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": { # Use generationConfig for temperature and other params
            "temperature": temperature,
            # Add other parameters as needed (e.g., maxOutputTokens, stopSequences)
        },
        # Add safetySettings if needed (refer to Gemini API docs)
        # "safetySettings": [...],
    }

    try:
        logger.debug(f"Calling Gemini generateContent API for prompt: {prompt[:100]}...") # Log prompt snippet
        # --- CORRECTION HERE ---
        # Replace requests.post with await httpx.post
        async with httpx.AsyncClient(timeout=20) as client: # Use async client with context manager
             # Use the pre-constructed URL with key
             res = await client.post(GEMINI_GENERATE_CONTENT_URL, headers=headers, json=body) # AWAIT the call
             res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the JSON response
        response_data = res.json()

        # Extract the content safely
        # Gemini response structure: {'candidates': [{'content': {'parts': [{'text': '...'}]}}]}
        content = response_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text") if response_data.get("candidates") else None

        if content is None:
             logger.warning(f"Gemini generateContent response did not contain expected content structure. Raw response: {response_data}")
             # Check for 'promptFeedback' or 'filters' in response_data for block reasons
             if response_data.get("promptFeedback"):
                 logger.warning(f"Gemini prompt feedback: {response_data['promptFeedback']}")


        logger.debug("Gemini generateContent API call successful.")
        return content

    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API HTTP error: {e} - Response: {e.response.text}", exc_info=True)
        return None
    except httpx.RequestError as e:
        logger.error(f"Gemini API request error: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred calling Gemini API: {e}", exc_info=True)
        return None

# --- Main routing async function ---
# --- CORRECTION HERE ---
# Convert to async def
# Simplify task routing to map task type to the appropriate async helper function
# The payload is now expected to be the prompt string itself.
async def call_ai_agent(task_type: str, prompt: str) -> str | None:
    """
    Routes prompt to the appropriate asynchronous AI helper function based on task_type.
    Returns the text content of the AI response or None on failure.

    Args:
        task_type (str): The type of task (e.g., "diagnosis", "patch_suggestion", "validation_review", "triage").
        prompt (str): The full prompt text prepared by the calling function.

    Returns:
        str | None: The text content of the AI response, or None on failure.
    """
    logger.info(f"[call_ai_agent] Routing task type: {task_type}")

    # Map task types to AI models/functions
    # This mapping assumes which model is best for each task.
    # You might need to adjust this or make it configurable.
    # Removed voice-related tasks from here as they are handled in voice.py/voice_ws_router.py
    # if they use dedicated transcription/chat endpoints.
    if task_type in {"diagnosis", "patch_suggestion", "validation_review", "triage", "generate_doc"}:
        # These tasks typically involve complex text understanding/generation
        # GPT-4o is often strong for these.
        logger.debug(f"Routing task '{task_type}' to OpenAI (_call_openai_chat).")
        return await _call_openai_chat(prompt) # AWAIT the helper call
    # elif task_type in {"intent", "chat_response"}:
    #     # If you need a general conversational model outside of voice.py/voice_ws_router.py
    #     # Gemini could be used here.
    #     logger.debug(f"Routing task '{task_type}' to Gemini (_call_gemini_generate_content).")
    #     return await _call_gemini_generate_content(prompt) # AWAIT the helper call
    else:
        logger.error(f"[call_ai_agent] Unknown or unhandled task type: {task_type}")
        # Consider returning an error structure or raising HTTPException if called from an endpoint
        return None

# Note: This file provides asynchronous functions for calling AI APIs.
# Other scripts should import and AWAIT the 'call_ai_agent' function or the specific
# helper functions if they need direct access.
# Install httpx: pip install httpx
