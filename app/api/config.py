# backend/app/api/config.py

from fastapi import APIRouter
import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Initialize the router WITHOUT a prefix. The prefix /api will be applied in main.py.
config_router = APIRouter(tags=["Configuration"])

# Define the endpoint path as /config.
# When included in main.py with prefix="/api", the full path becomes /api/config.
@config_router.get("/config")
def get_frontend_config():
    """
    Endpoint to provide frontend configuration details.
    """
    logger.info("Frontend config endpoint called.")  # Use logger
    # Load configuration details (in a real app, consider loading from environment variables or a config file)
    return {
        "model": "gpt-4o",
        "backend": "FastAPI",
        "frontend": "Streamlit",
        "status": "Production Ready"  # Example status
    }

# Note: This file defines the config router. It should be included in main.py
# using app.include_router(config_router, prefix="/api", ...).
