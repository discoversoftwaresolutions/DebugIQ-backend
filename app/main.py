# backend/main.py

import sys
import os
import datetime
import logging # Ensure logging is imported
import traceback # Import traceback for exception logging
import requests # Import requests for optional health check

# Ensure project root is in sys.path
# This is often needed for importing modules like 'app.api' or 'scripts'
# Adjust this path manipulation based on your actual project structure
# If main.py is in 'backend/app/', then '../../' goes up to the backend root
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Import your API Routers ---
# Ensure these import paths correctly point to your router files.
# Assume routers are defined in files named after their purpose (e.g., analyze.py defines analyze.router)
# Assume routers are located in an 'app/api' directory relative to the project root added above.
from app.api import analyze, qa, doc, config, voice
# Assuming voice_ws_router is in app/api/voice_ws_router.py and defines 'router'
from app.api.voice_ws_router import router as voice_ws_router
# Assuming autonomous_router is in app/api/autonomous_router.py and defines 'router'
from app.api.autonomous_router import router as autonomous_router
# Assuming issues_router is in app/api/issues_router.py and defines 'router'
from app.api.issues_router import router as issues_router
# Assuming metrics_router is in app/api/metrics_router.py and defines 'router'
from app.api.metrics_router import router as metrics_router

# Import the agent_suggest_patch router - Ensure this file and router exist
# This path might need adjustment based on your project structure (e.g., scripts/agent_suggest_patch.py)
# Assuming this router also defines endpoints potentially under /debugiq
try:
    from scripts.agent_suggest_patch import router as agent_suggest_patch_router
    logger = logging.getLogger(__name__) # Get logger here for the try/except scope
    logger.info("Successfully imported agent_suggest_patch router.")
except ImportError:
    logging.error("Could not import agent_suggest_patch router. Check the path 'scripts.agent_suggest_patch' and ensure the file defines 'router'.")
    agent_suggest_patch_router = None # Set to None if import fails
except Exception as e:
    logging.error(f"An unexpected error occurred during import of agent_suggest_patch router: {e}", exc_info=True)
    agent_suggest_patch_router = None


# Setup main application logger
logger = logging.getLogger(__name__)


# --- FastAPI App Initialization ---
app = FastAPI(
    title="DebugIQ API",
    description="Autonomous debugging pipeline powered by GPT-4o and agents.",
    version="1.0.0"
)

# --- CORS Configuration ---
# Allows cross-origin requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # !!! In production, replace "*" with your actual frontend URL(s) for security !!!
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- Register Routers ---
# This section includes your different API modules into the main application,
# applying prefixes and tags. The prefix here is added *before* any paths defined
# within the router itself.
# IMPORTANT: Routers being included here should NOT have prefixes defined in their
# own files, unless they are sub-routers mounted within another router.

# Include the analyze router under the /debugiq prefix
# Frontend POST to /debugiq/suggest_patch maps to @router.post("/suggest_patch") in analyze.py
# The analyze.router file should be initialized WITHOUT a prefix.
app.include_router(analyze.router, prefix="/debugiq", tags=["Analysis"])
logger.info("Included analyze router with prefix /debugiq.")

# Include the QA router under the /qa prefix
# Frontend POST to /qa/run maps to @router.post("/run") in qa.py
# The qa.router file should be initialized WITHOUT a prefix.
# !!! This inclusion is correct for the path, but the 422 error indicates that
# the endpoint definition *inside* qa.py expects a 'code' field instead of 'patch_diff'.
# The fix for the 422 is in qa.py, not here in main.py.
app.include_router(qa.router, prefix="/qa", tags=["Quality Assurance"])
logger.info("Included QA router with prefix /qa.")

# Include the documentation router under the /doc prefix
# Frontend POST to /doc/generate maps to @router.post("/generate") in doc.py
# The doc.router file should be initialized WITHOUT a prefix.
app.include_router(doc.router, prefix="/doc", tags=["Documentation"])
logger.info("Included doc router with prefix /doc.")

# Include the config router under the /api prefix (example prefix)
# Endpoints like GET /api/settings map to @router.get("/settings") in config.py
# The config.config_router file should be initialized WITHOUT a prefix.
app.include_router(config.config_router, prefix="/api", tags=["Configuration"])
logger.info("Included config router with prefix /api.")

# Include the voice websocket router - often mounted without a prefix
# Endpoints like @router.websocket("/ws/voice") in voice_ws_router.py will be at /ws/voice
# The voice_ws_router file should be initialized WITHOUT a prefix and use full paths.
app.include_router(voice_ws_router, tags=["Voice WebSocket"])
logger.info("Included voice websocket router (no prefix).")


# Include the autonomous workflow router under the /workflow prefix
# Frontend POST to /workflow/run_autonomous_workflow maps to @router.post("/run_autonomous_workflow") in autonomous_router.py
# The autonomous_router file should be initialized WITHOUT a prefix.
app.include_router(autonomous_router, prefix="/workflow", tags=["Autonomous Workflow"])
logger.info("Included autonomous workflow router with prefix /workflow.")


# Include the issues router - mounted without a prefix means its internal paths are the full paths
# Frontend GET to /issues/attention-needed maps to @router.get("/issues/attention-needed") in issues_router.py
# Frontend GET to /issues/{issue_id}/status maps to @router.get("/issues/{issue_id}/status") in issues_router.py
# The issues_router file should be initialized WITHOUT a prefix and use full paths starting with /issues.
app.include_router(issues_router, tags=["Issues"]) # No prefix here!
logger.info("Included issues router (no prefix). Internal paths must start with /issues.")


# Include the metrics router - mounted without a prefix means its internal paths are the full paths
# Frontend GET to /metrics/status maps to @router.get("/metrics/status") in metrics_router.py
# The metrics_router file should be initialized WITHOUT a prefix and use full path /metrics/status.
app.include_router(metrics_router, tags=["Metrics"]) # No prefix here!
logger.info("Included metrics router (no prefix). Internal paths must start with /metrics.")


# Include the agent_suggest_patch router
# !!! Potential Conflict/Redundancy !!!
# Including this router *again* under the /debugiq prefix is suspicious if analyze.router
# is already handling endpoints like /debugiq/suggest_patch.
# If analyze.router is the intended place for /debugiq endpoints like /suggest_patch,
# you should probably comment out or remove this second inclusion line:
if agent_suggest_patch_router: # Only include if import was successful
     app.include_router(agent_suggest_patch_router, prefix="/debugiq", tags=["Agent Patch Suggestions - Potential Conflict"])
     logger.warning("Included agent_suggest_patch router with prefix /debugiq. Review for potential conflicts with analyze router.")


# --- Root Endpoint ---
# A simple endpoint to verify the API is running
@app.get("/")
def read_root():
    """Root endpoint returning a welcome message."""
    logger.info("Root endpoint called.")
    return {"message": "Welcome to the DebugIQ API"}

# --- Health Check Endpoint ---
@app.get("/health")
def health_check():
    """Endpoint to check if the API is live and responsive."""
    logger.info("Health check endpoint called.")
    return {"status": "ok", "message": "API is running"}


# --- Startup and Shutdown Events ---
# These functions run once when the FastAPI application starts or stops.
@app.on_event("startup")
async def startup_event():
    """
    Runs once when the API server starts.
    Initializes application state and logs launch.
    """
    # Configure basic logging if not already configured (usually done earlier)
    # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__) # Get logger again within the event function

    now = datetime.datetime.now().isoformat()
    logger.info(f"🚀 DebugIQ API starting up at {now}")

    # Example: Initialize in-memory application state variables
    app.state.active_agents = {} # Example: Track active agent instances
    app.state.launch_time = now # Example: Store startup time
    logger.info("Application state initialized.")

    # Optional: Add logic to warm up external services or check dependencies
    try:
        # This section was commented out in your original code - keeping it commented as a placeholder
        # You can uncomment and configure this to check external dependencies on startup.
        # ping_url = "https://autonomous-debug.onrender.com/health" # Example external service
        # logger.info(f"Attempting health check for {ping_url}...")
        # ping_response = requests.get(ping_url, timeout=5) # Added timeout
        # ping_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        # logger.info(f"External service health ping successful: {ping_response.status_code}")
        logger.info("External service health check skipped (commented out).")
    except requests.exceptions.RequestException as e:
        logger.error(f"External service health check failed: {e}", exc_info=True) # Log the error details
    except Exception as e:
         logger.error(f"An unexpected error occurred during startup health check: {e}", exc_info=True)


    logger.info("Startup sequence complete.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Executed once when the API is stopping.
    Useful for cleanup (closing connections, saving state, logging).
    """
    logger = logging.getLogger(__name__) # Get logger again within the event function
    logger.info("🛑 DebugIQ API shutting down...")

    # Example: Clean up in-memory state
    if hasattr(app.state, "active_agents"):
        count = len(app.state.active_agents)
        logger.info(f"🧹 Releasing {count} active agents from app.state")
        app.state.active_agents.clear()

    # Optional: Add logic to properly close database connections, flush logs, etc.
    try:
         # Example: db_connection.close()
         logger.info("✅ Shutdown complete.")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}", exc_info=True)


# Example of how to run the app (typically done by a Uvicorn command, not in the file itself)
# if __name__ == "__main__":
#     import uvicorn
#     # This runs the app with auto-reloading for development
#     # Make sure to pass the correct app object: "main:app" if this file is main.py and the app instance is named 'app'
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
