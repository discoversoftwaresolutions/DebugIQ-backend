import os
import httpx  # Import the asynchronous HTTP client
import logging  # Import logging
import json  # Import json for parsing responses

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

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. Gemini API calls will fail.")

# Define base URLs (adjust if using self-hosted or different endpoints)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
if GEMINI_API_KEY:
    GEMINI_GENERATE_CONTENT_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
else:
    GEMINI_GENERATE_CONTENT_URL = None

GPT_MODEL = "gpt-4o"  # Or your preferred GPT model


# --- Helper async functions for specific AI API calls ---
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
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
    }

    try:
        logger.debug(f"Calling OpenAI chat API for prompt: {prompt[:100]}...")
        async with httpx.AsyncClient(timeout=25) as client:
            res = await client.post(OPENAI_CHAT_COMPLETIONS_URL, headers=headers, json=body)
            res.raise_for_status()

        response_data = res.json()
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

    headers = {"Content-Type": "application/json"}

    body = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }

    try:
        logger.debug(f"Calling Gemini generateContent API for prompt: {prompt[:100]}...")
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(GEMINI_GENERATE_CONTENT_URL, headers=headers, json=body)
            res.raise_for_status()

        response_data = res.json()
        content = response_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text") if response_data.get("candidates") else None

        if content is None:
            logger.warning(f"Gemini generateContent response did not contain expected content structure. Raw response: {response_data}")
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


async def call_ai_agent(task_type: str, prompt: str) -> str | None:
    """
    Routes the prompt to the appropriate asynchronous AI helper function based on task_type.

    Args:
        task_type (str): The type of task (e.g., "diagnosis", "patch_suggestion", "validation_review", "triage").
        prompt (str): The full prompt text prepared by the calling function.

    Returns:
        str | None: The text content of the AI response, or None on failure.
    """
    logger.info(f"[call_ai_agent] Routing task type: {task_type}")

    if task_type in {"diagnosis", "patch_suggestion", "validation_review", "triage", "generate_doc"}:
        logger.debug(f"Routing task '{task_type}' to OpenAI (_call_openai_chat).")
        return await _call_openai_chat(prompt)
    else:
        logger.error(f"[call_ai_agent] Unknown or unhandled task type: {task_type}")
        return None
