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

# --- CORRECTION HERE ---
# Initialize the router WITHOUT a prefix. The prefix /debugiq will be applied in main.py.
router = APIRouter(tags=["Analysis"]) # Removed prefix="/debugiq"

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Log an error/warning if the key is missing
    logger.error("OPENAI_API_KEY environment variable is not set. OpenAI calls will fail.")
    # Consider raising a more critical error here if this is essential for the app to start
    # raise ValueError("OPENAI_API_KEY environment variable is not set.")

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
     # Log errors during client initialization
     logger.error(f"ERROR: Failed to initialize OpenAI client: {e}", exc_info=True)
     openai_client = None


class AnalyzeRequest(BaseModel):
    code: str
    language: str  # Specify the programming language (e.g., Python, JavaScript)
    context: dict = {}  # Optional context, e.g., imports, dependencies

# This path is relative to the router's prefix, which is /debugiq in main.py
# So, this becomes POST /debugiq/suggest_patch
@router.post("/suggest_patch")
async def suggest_patch(request: AnalyzeRequest):
    """
    Uses the DebugIQ model powered by GPT-4o to generate a patch for the provided code.
    """
    # Check if the OpenAI client was initialized successfully due to missing key
    if openai_client is None:
         logger.error("Attempted to call suggest_patch but OpenAI client is not configured.")
         raise HTTPException(status_code=500, detail="OpenAI API key is not configured in the backend.")

    try:
        # Prepare the prompt for GPT-4o
        prompt = f"""
You are a debugging assistant, part of the DebugIQ platform, powered by GPT-4o. Your task is to analyze the following {request.language} code and suggest improvements or fixes.

### Code:
{request.code}

### Context:
{request.context}

### Instructions:
1. Provide a diff-style patch to improve the code.
2. Explain the changes you made in clear and concise terms.
3. Ensure the suggested patch is syntactically correct for {request.language}.

Respond with the following format:
### Diff:
<diff>
### Explanation:
<explanation>
"""
        logger.info(f"Sending analysis request to OpenAI for {request.language} code...")

        # Call GPT-4o via OpenAI API using the initialized client
        response = await openai_client.chat.completions.create( # Use await with the new client method
             model="gpt-4o", # Use the appropriate model name
             messages=[{"role": "user", "content": prompt}],
             temperature=0.7,
             max_tokens=2000  # Adjust the token limit as needed
        )

        logger.info("Received response from OpenAI. Checking response structure...")

        # --- CORRECTION HERE: More robust response content extraction and check ---
        # Ensure choices and message exist and content is not None/empty
        response_content = None
        if response.choices and len(response.choices) > 0 and \
           hasattr(response.choices[0], 'message') and response.choices[0].message and \
           hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
            response_content = response.choices[0].message.content
            logger.info("Successfully extracted content from OpenAI response.")
        else:
            logger.warning(f"OpenAI response did not contain expected message content or structure. Raw response: {response}")
            # Raise a specific error if content is missing or structure is wrong
            raise ValueError("OpenAI response did not contain expected message content.")

        # Assign the content to gpt_reply AFTER confirming it exists
        gpt_reply = response_content # gpt_reply is now guaranteed to be assigned if no ValueError was raised

        # --- Rest of the parsing logic using gpt_reply ---
        # These lines are now safe to execute as gpt_reply is defined
        diff_marker = "### Diff:"
        explanation_marker = "### Explanation:"

        diff_index = gpt_reply.find(diff_marker)
        explanation_index = gpt_reply.find(explanation_marker)

        # Ensure both markers are found and in the correct order
        if diff_index == -1 or explanation_index == -1 or diff_index >= explanation_index:
             logger.error(f"Markers not found or in incorrect order in GPT-4o reply. Diff at {diff_index}, Explanation at {explanation_index}. Raw reply: {gpt_reply[:500]}...") # Log problematic reply snippet
             raise ValueError("GPT-4o response is not in the expected format (missing markers or wrong order).")

        diff_start = diff_index + len(diff_marker)
        explanation_start = explanation_index + len(explanation_marker)

        diff = gpt_reply[diff_start:explanation_index].strip()
        explanation = gpt_reply[explanation_start:].strip()

        logger.info("Successfully parsed diff and explanation from OpenAI response.")

        return {
            "diff": diff,
            "explanation": explanation,
            # Omitted other keys like patched_code, patched_file_name as frontend doesn't strictly need them based on previous code
        }

    # Catch specific exceptions during the OpenAI call or parsing
    except openai.APIError as e:
         logger.error(f"OpenAI API Error: Status {e.status_code} - {e.response.text}", exc_info=True) # Log API specific error details including status
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
    except ValueError as e: # This will now catch the ValueError raised if content is missing or markers are wrong
         logger.error(f"Response Parsing Error: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail=f"Failed to parse GPT-4o response: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors
        logger.exception("An unexpected error occurred in suggest_patch endpoint:") # Log with full traceback
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred processing the request: {str(e)}")

# Note: This file defines the analyze router. It should be included in main.py
# using app.include_router(router, prefix="/debugiq", ...).
