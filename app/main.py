# File: backend/app/main.py (DebugIQ Service - Updated)

import sys
import os
import datetime
import logging
# removed 'requests' as it's not used in this main.py and httpx is preferred for async contexts
# import requests

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session # For DB dependency injection
from sqlalchemy import text # <--- ADDED: For SQLAlchemy 2.0 raw SQL compatibility

# === DebugIQ Specific Imports ===
from app.api import analyze, qa, doc, config, voice # Your existing routers
from app.api.voice_ws_router import router as voice_ws_router
from app.api.autonomous_router import router as autonomous_router
from app.api.issues_router import router as issues_router
from app.api.metrics_router import router as metrics_router

# --- NEW DB, Redis, Celery Imports ---
from app.database import SessionLocal, get_db, create_db_tables # DebugIQ's DB setup
from app.models import Base # DebugIQ's SQLAlchemy Base for metadata.create_all
from debugiq_celery import celery_app # DebugIQ's Celery app instance
from debugiq_utils import get_debugiq_redis_client # DebugIQ's Redis utilities

# Ensure project root is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

# Setup main application logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI App Initialization
app = FastAPI(
    title="DebugIQ API",
    description="Autonomous debugging pipeline powered by GPT-4o and agents.",
    version="1.0.0"
)

# === Global Async Redis Client instance for DebugIQ ===
_global_debugiq_redis_aio_client = None

@app.on_event("startup")
async def startup_event():
    global _global_debugiq_redis_aio_client
    logger.info(f"🚀 DebugIQ API starting up at {datetime.datetime.now().isoformat()}")

    # Initialize DebugIQ's Redis client
    _global_debugiq_redis_aio_client = await get_debugiq_redis_client()

    # Optional: Create DB tables on startup for development environment
    # create_db_tables() # CAUTION: Only for development, use Alembic for production migrations!

    app.state.active_agents = {} # Your existing app state management
    app.state.launch_time = datetime.datetime.now().isoformat()

    try:
        # Check Redis and DB connectivity as part of startup
        await _global_debugiq_redis_aio_client.ping()
        db_session = SessionLocal()
        # --- FIX APPLIED HERE ---
        db_session.execute(text("SELECT 1")) # <--- UPDATED: Wrap raw SQL with text()
        db_session.close()
        logger.info("✅ DebugIQ: Redis and Database connected successfully during startup.")
    except Exception as e:
        logger.error(f"❌ DebugIQ: Critical startup dependency check failed: {e}", exc_info=True)
        # You might want to raise a more critical error here to prevent startup
        # if DB/Redis are absolutely essential.
        # raise RuntimeError("DebugIQ failed to connect to critical dependencies on startup.") from e

    logger.info("Startup sequence complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 DebugIQ API shutting down...")

    if hasattr(app.state, "active_agents"):
        count = len(app.state.active_agents)
        logger.info(f"🧹 Releasing {count} active agents from app.state")
        app.state.active_agents.clear()

    if _global_debugiq_redis_aio_client:
        await _global_debugiq_redis_aio_client.close()
        logger.info("🧹 DebugIQ: Redis connection closed.")

    # Assuming DB engine disposal is handled by app.database or similar global cleanup
    # if app.state.database_engine:
    #     app.state.database_engine.dispose()

    logger.info("✅ Shutdown complete.")


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, replace with actual frontend URL(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
# Note: analyze.router will now contain the /suggest_patch and status endpoints
app.include_router(analyze.router, prefix="/debugiq", tags=["Analysis"])
app.include_router(qa.router, prefix="/qa", tags=["Quality Assurance"])
app.include_router(doc.router, prefix="/doc", tags=["Documentation"])
app.include_router(config.config_router, prefix="/api", tags=["Configuration"])
app.include_router(voice_ws_router, tags=["Voice WebSocket"])
app.include_router(autonomous_router, prefix="/workflow", tags=["Autonomous Workflow"])
app.include_router(issues_router, tags=["Issues"])
app.include_router(metrics_router, tags=["Metrics"])

# Root Endpoint
@app.get("/")
def read_root():
    logger.info("Root endpoint called.")
    return {"message": "Welcome to the DebugIQ API"}

# Health Check Endpoint (now async and checks dependencies)
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        await _global_debugiq_redis_aio_client.ping()
        # --- FIX APPLIED HERE ---
        db.execute(text("SELECT 1")) # <--- UPDATED: Wrap raw SQL with text()
        return {"status": "ok", "message": "API is running", "database": "connected", "redis": "connected"}
    except Exception as e:
        logger.error(f"DebugIQ Health Check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"status": "unhealthy", "message": str(e)})


# If you run the DebugIQ service using uvicorn main:app
if __name__ == "__main__":
    import uvicorn
    # IMPORTANT: Ensure your DEBUGIQ_DATABASE_URL, DEBUGIQ_REDIS_URL, and OPENAI_API_KEY
    # are set (e.g., in a .env file) before running.
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True) # Use a different port, e.g., 8004
