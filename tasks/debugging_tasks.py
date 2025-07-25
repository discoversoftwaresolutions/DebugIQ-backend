# File: backend/tasks/debugging_tasks.py (DebugIQ Service)

import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException # For raising structured errors from tasks

# === DebugIQ Celery App and Utilities ===
from debugiq_celery import celery_app # DebugIQ's own Celery app
from debugiq_utils import update_debugiq_task_state_and_notify # DebugIQ's own state update utility

# === OpenAI Client and Retry Strategy ===
import openai # Main library namespace
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError, APIConnectionError, AuthenticationError as OpenAIAuthError, BadRequestError

from tenacity import ( # For retries
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception, # <--- IMPORTED FOR CUSTOM PREDICATE
    before_sleep_log
)

import os # Ensure os is imported

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- OpenAI Client Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client_instance = None # Singleton instance

async def get_openai_client() -> Optional[AsyncOpenAI]:
    global openai_client_instance
    if openai_client_instance is None:
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not set. OpenAI client cannot be initialized.")
            return None
        try:
            openai_client_instance = AsyncOpenAI(api_key=OPENAI_API_KEY)
            logger.info("DebugIQ: AsyncOpenAI client initialized.")
        except Exception as e:
            logger.error(f"DebugIQ: Failed to initialize AsyncOpenAI client: {e}", exc_info=True)
            openai_client_instance = None
    return openai_client_instance

# --- Helper function for conditional APIError retry (NEW) ---
def is_retryable_openai_api_error(exception: Exception) -> bool:
    """
    Predicate for tenacity: Returns True if the OpenAI APIError
    is a transient server error (5xx) that should be retried.
    """
    return isinstance(exception, APIError) and \
           hasattr(exception, 'status_code') and \
           exception.status_code and \
           exception.status_code >= 500

# --- LLM Retry Strategy (UPDATED) ---
LLM_RETRY_STRATEGY = retry(
    stop=stop_after_attempt(7), # More attempts for LLMs due to higher transient failure rates
    wait=wait_exponential(multiplier=1, min=2, max=60), # Longer delays, up to 60s
    retry=(
        retry_if_exception_type(APITimeoutError) |
        retry_if_exception_type(APIConnectionError) |
        retry_if_exception_type(RateLimitError) |
        retry_if_exception(is_retryable_openai_api_error) # <--- UPDATED TO USE CUSTOM PREDICATE
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True # Re-raise the last exception after all retries are exhausted
)

# --- Custom Exception for LLM Integration Errors ---
class LLMIntegrationError(Exception):
    """Custom exception for errors during LLM interaction."""
    pass

# === Celery Task to Run Patch Suggestion ===
@celery_app.task(bind=True)
async def run_patch_suggestion_task(self, request_payload_dict: Dict[str, Any], debugiq_task_id: str):
    # request_payload_dict will contain 'code', 'language', 'context'
    request = request_payload_dict # For now, use dict directly for simplicity, or define Pydantic model

    await update_debugiq_task_state_and_notify(
        debugiq_task_id, status="running", logs="Starting patch suggestion process...",
        current_stage="LLM Prompting", progress=10
    )
    logger.info(f"DebugIQ Task {debugiq_task_id}: Processing patch suggestion for project '{request.get('project_id', 'N/A')}' (code language: {request.get('language')}).")

    try:
        client = await get_openai_client()
        if not client:
            raise LLMIntegrationError("OpenAI client not initialized, API key might be missing.")

        # Prepare the prompt for GPT-4o
        prompt = f"""
You are a debugging assistant, part of the DebugIQ platform, powered by GPT-4o. Your task is to analyze the following {request.get('language', 'programming')} code and suggest improvements or fixes.

### Code:
{request.get('code', 'No code provided.')}

### Context:
{request.get('context', 'No specific context.')}

### Instructions:
1. Provide a diff-style patch to improve the code.
2. Explain the changes you made in clear and concise terms.
3. Ensure the suggested patch is syntactically correct for {request.get('language', 'the specified language')}.

Respond with the following format:
### Diff:
<diff>
### Explanation:
<explanation>
"""
        await update_debugiq_task_state_and_notify(
            debugiq_task_id, logs="Sending analysis request to OpenAI...",
            current_stage="LLM Call", progress=30
        )
        logger.info(f"DebugIQ Task {debugiq_task_id}: Sending analysis request to OpenAI.")

        # Call GPT-4o via OpenAI API with tenacity retries
        @LLM_RETRY_STRATEGY
        async def call_openai_api(prompt_text: str):
            response = await client.chat.completions.create(
                model="gpt-4o", # Use the appropriate model name
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.7,
                max_tokens=2000
            )
            # Ensure choices and message exist and content is not None/empty
            if not (response.choices and response.choices[0].message and response.choices[0].message.content):
                raise ValueError("OpenAI response did not contain expected message content.")
            return response.choices[0].message.content

        response_content = await call_openai_api(prompt)
        
        await update_debugiq_task_state_and_notify(
            debugiq_task_id, logs="Received response from OpenAI. Parsing...",
            current_stage="Parsing Response", progress=70
        )
        logger.info(f"DebugIQ Task {debugiq_task_id}: Received response from OpenAI. Parsing content.")

        # --- Parsing Logic (from original analyze.py) ---
        diff_marker = "### Diff:"
        explanation_marker = "### Explanation:"

        diff_index = response_content.find(diff_marker)
        explanation_index = response_content.find(explanation_marker)

        if diff_index == -1 or explanation_index == -1 or diff_index >= explanation_index:
            error_msg = "GPT-4o response is not in the expected format (missing markers or wrong order)."
            logger.error(f"DebugIQ Task {debugiq_task_id}: {error_msg}. Raw reply: {response_content[:500]}...")
            raise ValueError(error_msg)

        diff_start = diff_index + len(diff_marker)
        explanation_start = explanation_index + len(explanation_marker)

        diff = response_content[diff_start:explanation_index].strip()
        explanation = response_content[explanation_start:].strip()

        final_output = {
            "diff": diff,
            "explanation": explanation,
            "raw_llm_response_snippet": response_content[:1000] # For auditing
        }

        await update_debugiq_task_state_and_notify(
            debugiq_task_id, status="completed", logs="Patch suggestion completed.",
            current_stage="Completed", progress=100, output_data=final_output
        )
        logger.info(f"DebugIQ Task {debugiq_task_id}: Patch suggestion completed successfully.")
        return {"status": "success", "result": final_output}

    except LLMIntegrationError as e:
        error_detail = f"LLM client error: {str(e)}"
        logger.error(f"DebugIQ Task {debugiq_task_id}: {error_detail}")
        await update_debugiq_task_state_and_notify(
            debugiq_task_id, status="failed", logs=error_detail,
            current_stage="LLM Client Error", progress=0, details={"error_type": "LLMClientError", "detail": error_detail}
        )
        raise # Re-raise for Celery to mark as failed
    except ValueError as e: # Catch parsing errors
        error_detail = f"Response parsing failed: {str(e)}"
        logger.error(f"DebugIQ Task {debugiq_task_id}: {error_detail}")
        await update_debugiq_task_state_and_notify(
            debugiq_task_id, status="failed", logs=error_detail,
            current_stage="Parsing Error", progress=0, details={"error_type": "ParsingError", "detail": error_detail}
        )
        raise # Re-raise for Celery
    except Exception as e:
        error_detail = f"An unexpected error occurred during patch suggestion: {str(e)}"
        logger.exception(f"DebugIQ Task {debugiq_task_id}: {error_detail}")
        await update_debugiq_task_state_and_notify(
            debugiq_task_id, status="failed", logs=error_detail,
            current_stage="Unhandled Error", progress=0, details={"error_type": "UnhandledError", "detail": error_detail}
        )
        raise # Re-raise for Celery to mark as failed
