# backend/app/api/doc.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging # Import logging

logger = logging.getLogger(__name__)

# Initialize the router WITHOUT a prefix. The prefix /doc will be applied in main.py.
router = APIRouter(tags=["Documentation"])

# --- CORRECTION HERE ---
# Define the Pydantic Model for the Request Body
# This model MUST match the payload sent by the frontend for the Documentation tab.
class DocRequest(BaseModel):
    code: str # The code content
    language: str # <--- Corrected: Add the language field sent by the frontend

# --- Define the Endpoint ---
# This path is relative to the /doc prefix applied in main.py
@router.post("/generate")
# --- CORRECTION HERE ---
# Use the corrected Pydantic model for the request body
async def generate_doc(request: DocRequest):
    """
    Endpoint to generate documentation for provided code.
    """
    logger.info("Received documentation generation request.")
    code_content = request.code # Access the code content
    code_language = request.language # Access the language

    # --- Add your actual documentation generation logic here ---
    # This would involve using an LLM to generate documentation based on the code and language.
    logger.info(f"Generating documentation for {code_language} code (snippet): {code_content[:200]}...")

    # Placeholder for generated documentation
    generated_documentation = f"Placeholder: Documentation for {code_language} code." # Example using the language

    logger.info("Placeholder documentation generation complete.")

    # Return the generated documentation to the frontend
    # The frontend expects a JSON response, typically with a "documentation" key
    return {
        "documentation": generated_documentation
    }

# --- (Add other endpoints for the Doc router here if needed) ---
