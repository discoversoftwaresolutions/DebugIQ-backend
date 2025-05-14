# analyze.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai  # OpenAI API client for GPT-4o integration
import os

# --- CORRECTION HERE ---
# Initialize the router with the /debugiq prefix
router = APIRouter(prefix="/debugiq", tags=["Analysis"]) # Added prefix and optional tags

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Use logging.error instead of raising Runtime Error immediately,
    # as the app might run but the endpoint would fail.
    # Raising HTTPException in the endpoint is better for API errors.
    # Or, depending on your app structure, raise it during app startup.
    # For a simple file like this, logging is a good indicator.
    print("ERROR: OPENAI_API_KEY environment variable is not set.")
    # Or, raise an exception during application startup if this file is imported there
    # raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize OpenAI client - using the newer client style
# The older openai.api_key might work but the client is preferred.
try:
    # Ensure API key is available before initializing client
    if OPENAI_API_KEY:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None # Client will be None if key is missing
        print("WARNING: OpenAI client not initialized because API key is missing.")
except Exception as e:
     print(f"ERROR: Failed to initialize OpenAI client: {e}")
     openai_client = None


class AnalyzeRequest(BaseModel):
    code: str
    language: str  # Specify the programming language (e.g., Python, JavaScript)
    context: dict = {}  # Optional context, e.g., imports, dependencies

@router.post("/suggest_patch") # This path is now relative to the router prefix /debugiq
async def suggest_patch(request: AnalyzeRequest):
    """
    Uses the DebugIQ model powered by GPT-4o to generate a patch for the provided code.
    """
    # Check if the OpenAI client was initialized successfully
    if openai_client is None:
         raise HTTPException(status_code=500, detail="OpenAI API key is not configured.")

    try:
        # Prepare the prompt for GPT-4o
        # Used f-string continuation for better readability of long strings
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

        # Call GPT-4o via OpenAI API using the initialized client
        response = openai_client.chat.completions.create( # Use client.chat.completions.create
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000  # Increased token limit slightly, adjust as needed
        )

        # Extract the response content - Adjusting for the new client's response object structure
        # The response is an object, access attributes with dot notation
        if not response.choices or not response.choices[0].message:
             raise ValueError("GPT-4o response did not contain expected message.")

        gpt_reply = response.choices[0].message.content

        # Parse the response based on markers - still using find, consider more robust parsing if needed
        diff_marker = "### Diff:"
        explanation_marker = "### Explanation:"

        diff_index = gpt_reply.find(diff_marker)
        explanation_index = gpt_reply.find(explanation_marker)

        if diff_index == -1 or explanation_index == -1:
             # Include the raw reply in the error for debugging
             raise ValueError(f"GPT-4o response is not in the expected format. Raw reply: {gpt_reply[:500]}...") # Limit raw reply length


        # Extract diff and explanation based on marker positions
        # Handle cases where markers might be at the very start/end
        diff_start = diff_index + len(diff_marker)
        explanation_start = explanation_index + len(explanation_marker)

        # If explanation comes after diff
        if diff_index < explanation_index:
            diff = gpt_reply[diff_start:explanation_index].strip()
            explanation = gpt_reply[explanation_start:].strip()
        else:
            # Handle unexpected marker order (e.g., if explanation comes before diff)
            # Or if only one marker is found (already handled by the -1 check)
            # For simplicity here, we assume the expected order. If order is variable,
            # you'd need more complex parsing logic (e.g., regex or splitting)
            logger.error(f"Unexpected marker order in GPT-4o reply: Diff at {diff_index}, Explanation at {explanation_index}. Raw reply: {gpt_reply[:500]}...")
            raise ValueError("GPT-4o response markers found in unexpected order.")


        # Return the response to the client - match frontend's expected keys
        return {
            "diff": diff,
            # "patched_code": f"# This is a placeholder for the patched code.\n{request.code}", # Not strictly needed by frontend, can remove
            "explanation": explanation,
            # "patched_file_name": "patched_file.py", # Not strictly needed by frontend, can remove
            # "original_content": request.code # Not strictly needed by frontend, can remove
        }

    # Catch specific OpenAI API errors
    except openai.APIError as e: # Use openai.APIError for general API errors
         logger.error(f"OpenAI API Error: {e}")
         raise HTTPException(status_code=500, detail=f"Error from OpenAI API: {e.message}") # Access error message
    except openai.AuthenticationError: # Catch specific authentication errors
         logger.error("OpenAI Authentication Error: Invalid API key.")
         raise HTTPException(status_code=500, detail="OpenAI Authentication Error: Invalid API key.")
    except openai.RateLimitError: # Catch specific rate limit errors
         logger.error("OpenAI Rate Limit Error.")
         raise HTTPException(status_code=429, detail="OpenAI Rate Limit Exceeded. Please try again later.") # Use 429 status code
    except openai.APIConnectionError as e: # Catch connection errors
         logger.error(f"OpenAI API Connection Error: {e}")
         raise HTTPException(status_code=503, detail=f"OpenAI API Connection Error: {e}") # Use 503 status code
    except ValueError as e:
         # Catch ValueErrors, specifically the response parsing error
         logger.error(f"Response Parsing Error: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to parse GPT-4o response: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors during the process
        logger.exception("Unexpected error in suggest_patch endpoint:") # Log exception details
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Remember to include this router in your main FastAPI application instance (e.g., in main.py or app.py)
# Example: app.include_router(router)
