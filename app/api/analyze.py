from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai  # OpenAI API client for GPT-4o integration
import os

router = APIRouter()

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

openai.api_key = OPENAI_API_KEY

class AnalyzeRequest(BaseModel):
    code: str
    language: str  # Specify the programming language (e.g., Python, JavaScript)
    context: dict = {}  # Optional context, e.g., imports, dependencies

@router.post("/suggest_patch")
async def suggest_patch(request: AnalyzeRequest):
    """
    Uses the DebugIQ model powered by GPT-4o to generate a patch for the provided code.
    """
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

        # Call GPT-4o via OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Replace with the specific GPT-4o model if necessary
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500  # Adjust the token limit based on expected response size
        )

        # Extract the response content
        gpt_reply = response["choices"][0]["message"]["content"]
        diff_index = gpt_reply.find("### Diff:")
        explanation_index = gpt_reply.find("### Explanation:")

        if diff_index == -1 or explanation_index == -1:
            raise ValueError("GPT-4o response is not in the expected format.")

        # Split the response into diff and explanation
        diff = gpt_reply[diff_index + len("### Diff:"):explanation_index].strip()
        explanation = gpt_reply[explanation_index + len("### Explanation:"):].strip()

        # Return the response to the client
        return {
            "diff": diff,
            "patched_code": f"# This is a placeholder for the patched code.\n{request.code}",
            "explanation": explanation,
            "patched_file_name": "patched_file.py",  # Default file name for the patch
            "original_content": request.code
        }

    except openai.error.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with GPT-4o: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
