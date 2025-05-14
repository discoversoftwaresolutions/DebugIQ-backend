# backend/analyze.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
# Import AsyncOpenAI for asynchronous operations
import openai  # Import the main library namespace
from openai import AsyncOpenAI # Import AsyncOpenAI specifically
import os
import logging # Import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router WITHOUT a prefix. The prefix /debugiq will be applied in main.py.
router = APIRouter(tags=["Analysis"])

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set. OpenAI calls will fail.")

# Initialize OpenAI client - Use AsyncOpenAI for asynchronous endpoints
openai_client = None # Initialize client to None
try:
    # Ensure API key is available before initializing client
    if OPENAI_API_KEY:
        # --- CORRECTION HERE: Use AsyncOpenAI ---
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized (Async).")
    else:
        logger.warning("OpenAI client not initialized because API key is missing.")
except Exception as e:
     logger.error(f"ERROR: Failed to initialize OpenAI client: {e}", exc_info=True)
     openai_client = None


class AnalyzeRequest(BaseModel):
    code: str
    language: str
    context: dict = {}

@router.post("/suggest_patch")
async def suggest_patch(request: AnalyzeRequest):
    """
    Uses the DebugIQ model powered by GPT-4o to generate a patch for the provided code.
    """
    if openai_client is None:
         logger.error("Attempted to call suggest_patch but OpenAI client is not configured.")
         raise HTTPException(status_code=500, detail="OpenAI API key is not configured in the backend.")

    try:
        prompt = f"""... (your prompt text) ...""" # Keep your existing prompt

        logger.info(f"Sending analysis request to OpenAI for {request.language} code...")

        # --- This call is now valid because openai_client is an AsyncOpenAI instance ---
        response = await openai_client.chat.completions.create(
             model="gpt-4o", # Use the appropriate model name
             messages=[{"role": "user", "content": prompt}],
             temperature=0.7,
             max_tokens=2000  # Adjust the token limit as needed
        )

        logger.info("Received response from OpenAI. Parsing...")

        # ... (keep the rest of your response parsing logic) ...
        diff_marker = "### Diff:"
        explanation_marker = "### Explanation:"

        diff_index = gpt_reply.find(diff_marker)
        explanation_index = gpt_reply.find(explanation_marker)

        if diff_index == -1 or explanation_index == -1 or diff_index >= explanation_index:
             logger.error(f"Markers not found or in incorrect order in GPT-4o reply. Raw reply: {gpt_reply[:500]}...")
             raise ValueError("GPT-4o response is not in the expected format (missing markers or wrong order).")

        diff_start = diff_index + len(diff_marker)
        explanation_start = explanation_index + len(explanation_marker)

        diff = gpt_reply[diff_start:explanation_index].strip()
        explanation = gpt_reply[explanation_start:].strip()

        logger.info("Successfully parsed diff and explanation from OpenAI response.")

        return {
            "diff": diff,
            "explanation": explanation,
        }

    except openai.APIError as e:
         logger.error(f"OpenAI API Error: {e.status_code} - {e.response.text}", exc_info=True)
         raise HTTPException(status_code=500, detail=f"Error from OpenAI API: {e.message}")
    except openai.AuthenticationError:
         logger.error("OpenAI Authentication Error: Invalid API key.")
         raise HTTPException(status_code=500, detail="OpenAI Authentication Error: Invalid API key.")
    except openai.RateLimitError:
         logger.error("OpenAI Rate Limit Error.")
         raise HTTPException(status_code=429, detail="OpenAI Rate Limit Exceeded. Please try again later.")
    except openai.APIConnectionError as e:
         logger.error(f"OpenAI API Connection Error: {e}", exc_info=True)
         raise HTTPException(status_code=503, detail=f"OpenAI API Connection Error: Could not connect to OpenAI.")
    except ValueError as e:
         logger.error(f"Response Parsing Error: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail=f"Failed to parse GPT-4o response: {str(e)}")
    except Exception as e:
        logger.exception("An unexpected error occurred in suggest_patch endpoint:")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred processing the request: {str(e)}")

# Note: This file defines the analyze router. It should be included in main.py
# using app.include_router(router, prefix="/debugiq", ...).
