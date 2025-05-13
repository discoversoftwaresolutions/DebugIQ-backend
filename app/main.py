import sys
import os
import datetime
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))  # root of project
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core DebugIQ Modules
from app.api import analyze, qa, doc, config, voice
from app.api.voice_ws_router import router as voice_ws_router
from app.api.autonomous_router import router as autonomous_router
from app.api.issues_router import router as issues_router
from app.api.metrics_router import router as metrics_router

# Import the agent_suggest_patch router
from scripts.agent_suggest_patch import router as agent_suggest_patch_router

# Initialize the app
app = FastAPI(
    title="DebugIQ API",
    description="Autonomous debugging pipeline powered by GPT-4o and agents.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analyze.router, prefix="/debugiq", tags=["Analysis"])
app.include_router(qa.router, prefix="/qa", tags=["Quality Assurance"])
app.include_router(doc.router, prefix="/doc", tags=["Documentation"])
app.include_router(config.config_router, prefix="/api", tags=["Configuration"])
app.include_router(voice_ws_router, tags=["Voice WebSocket"])
app.include_router(autonomous_router, prefix="/workflow", tags=["Autonomous Workflow"])
app.include_router(issues_router, tags=["Issues"])
app.include_router(metrics_router, tags=["Metrics"])
app.include_router(agent_suggest_patch_router, prefix="/debugiq", tags=["Agent Patch Suggestions"])  # Include agent_suggest_patch router

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the DebugIQ API"}

@app.on_event("startup")
async def startup_event():
    """
    Runs once when the API server starts.
    Initializes agent state, logs launch, and primes key services.
    """
    # Log startup event
    now = datetime.datetime.now().isoformat()
    logging.basicConfig(level=logging.INFO)
    logging.info(f"🚀 DebugIQ API started at {now}")

    # Example: Initialize in-memory agent context or counters
    app.state.active_agents = {}
    app.state.launch_time = now

    # Optional: Warm up LLM endpoint
    try:
        import requests
        ping = requests.get("https://autonomous-debug.onrender.com/health")
        logging.info(f"Backend health ping: {ping.status_code}")
    except Exception as e:
        logging.error(f"Health ping failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Executed once when the API is stopping.
    Useful for agent cleanup, logging, cache clearing, etc.
    """
    import logging

    logging.info("🛑 DebugIQ API shutting down...")

    # Example: Clean up in-memory agent state
    if hasattr(app.state, "active_agents"):
        count = len(app.state.active_agents)
        logging.info(f"🧹 Releasing {count} active agents")
        app.state.active_agents.clear()

    # Optionally flush logs or close external connections
    # (e.g., Redis, DB, voice sockets)
    try:
        logging.info("✅ Shutdown complete.")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}
