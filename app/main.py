import sys
import os
import datetime
import logging
import traceback
import requests

# Ensure project root is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, qa, doc, config, voice
from app.api.voice_ws_router import router as voice_ws_router
from app.api.autonomous_router import router as autonomous_router
from app.api.issues_router import router as issues_router
from app.api.metrics_router import router as metrics_router

# Attempt to import agent_suggest_patch router
try:
    from scripts.agent_suggest_patch import router as agent_suggest_patch_router
    logger = logging.getLogger(__name__)
    logger.info("Successfully imported agent_suggest_patch router.")
except ImportError:
    logging.error("Could not import agent_suggest_patch router. Check the path 'scripts.agent_suggest_patch'.")
    agent_suggest_patch_router = None
except Exception as e:
    logging.error(f"Unexpected error importing agent_suggest_patch router: {e}", exc_info=True)
    agent_suggest_patch_router = None

# Setup main application logger
logger = logging.getLogger(__name__)

# FastAPI App Initialization
app = FastAPI(
    title="DebugIQ API",
    description="Autonomous debugging pipeline powered by GPT-4o and agents.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your actual frontend URL(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(analyze.router, prefix="/debugiq", tags=["Analysis"])
app.include_router(qa.router, prefix="/qa", tags=["Quality Assurance"])
app.include_router(doc.router, prefix="/doc", tags=["Documentation"])
app.include_router(config.config_router, prefix="/api", tags=["Configuration"])
app.include_router(voice_ws_router, tags=["Voice WebSocket"])
app.include_router(autonomous_router, prefix="/workflow", tags=["Autonomous Workflow"])
app.include_router(issues_router, tags=["Issues"])
app.include_router(metrics_router, tags=["Metrics"])

if agent_suggest_patch_router:
    app.include_router(agent_suggest_patch_router, prefix="/debugiq", tags=["Agent Patch Suggestions"])

# Root Endpoint
@app.get("/")
def read_root():
    logger.info("Root endpoint called.")
    return {"message": "Welcome to the DebugIQ API"}

# Health Check Endpoint
@app.get("/health")
def health_check():
    logger.info("Health check endpoint called.")
    return {"status": "ok", "message": "API is running"}

# Startup Event
@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger(__name__)
    now = datetime.datetime.now().isoformat()
    logger.info(f"🚀 DebugIQ API starting up at {now}")

    app.state.active_agents = {}  # Example: Track active agent instances
    app.state.launch_time = now

    try:
        logger.info("External service health check skipped (commented out).")
    except requests.exceptions.RequestException as e:
        logger.error(f"External service health check failed: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error during startup health check: {e}", exc_info=True)

    logger.info("Startup sequence complete.")

# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    logger = logging.getLogger(__name__)
    logger.info("🛑 DebugIQ API shutting down...")

    if hasattr(app.state, "active_agents"):
        count = len(app.state.active_agents)
        logger.info(f"🧹 Releasing {count} active agents from app.state")
        app.state.active_agents.clear()

    try:
        logger.info("✅ Shutdown complete.")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}", exc_info=True)
