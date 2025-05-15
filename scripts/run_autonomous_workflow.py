# This is the corrected generate_pr_body_with_gemini function code.
# It should be placed inside your create_fix_pull_request.py file.

# Ensure necessary imports are at the top of create_fix_pull_request.py:
# import google.generativeai as genai
# import logging
# import os # For GEMINI_API_KEY check

# Assume logger is configured at the module level in create_fix_pull_request.py
# logger = logging.getLogger(__name__)

# Assume GEMINI_API_KEY is read from environment variables at the top
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# --- Corrected Helper function to generate PR body using Gemini ---
# --- CORRECTION HERE ---
# Define the function as asynchronous (async def)
# The function signature and arguments match the expected input from the orchestrator
async def generate_pr_body_with_gemini(issue_id: str, code_diff: str, diagnosis_details: dict, validation_results: dict) -> str:
    """
    Generates a professional PR body using the Gemini API asynchronously.

    Args:
        issue_id (str): The ID of the issue.
        code_diff (str): The patch in diff format.
        diagnosis_details (dict): Details from the diagnosis step (e.g., summary).
        validation_results (dict): Results from the validation step (e.g., summary, status).

    Returns:
        str: The generated PR body text, or an informative error message if generation fails.
    """
    # --- CORRECTION HERE ---
    # Use logger instead of print for configuration check
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key missing, using fallback PR body template for PR body generation.")
        # Fallback template using available data
        diagnosis_summary = diagnosis_details.get('summary', 'N/A')
        validation_summary = validation_results.get('summary', 'N/A')
        code_changes = code_diff if code_diff else "No changes available."
        return f"""
## DebugIQ Automated Pull Request

**Issue ID:** {issue_id}

### Diagnosis Summary:
{diagnosis_summary}

### Validation Results:
{validation_summary}

### Code Changes:
```diff
{code_changes}
