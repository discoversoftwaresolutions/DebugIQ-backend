# File: backend/app/api/analyze.py (DebugIQ Service - Updated)

from fastapi import APIRouter, HTTPException, Body, Depends, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session # For DB dependency injection
from typing import Dict, Any, List
import uuid # For generating unique task IDs
import json # For WebSocket messages
import asyncio # For async sleep in WebSocket

# === DebugIQ Specific Imports ===
from app.database import get_db # DebugIQ's DB session
from app.models import DebugIQTask, DebugIQTaskStatusResponse # DebugIQ's task model and response schema
from debugiq_celery import celery_app # DebugIQ's Celery app
from debugiq_utils import get_debugiq_redis_client # DebugIQ's Redis client for WebSockets

# === Celery Task Import ===
from tasks.debugging_tasks import run_patch_suggestion_task # The actual task doing the LLM call

# === General Logging ===
import logging
logger = logging.getLogger(__name__)

# --- Initialize the router ---
router = APIRouter(tags=["Analysis"])


# --- Request Model ---
class AnalyzeRequest(BaseModel):
    code: str
    language: str
    context: Dict[str, Any] = {}
    project_id: str = "default_project" # Added for better task tracking


# === API Endpoint: POST /suggest_patch (Dispatches Celery Task) ===
@router.post("/suggest_patch", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def suggest_patch_endpoint(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Accepts code and dispatches a background task to generate a patch using GPT-4o.
    Returns a task ID for status tracking.
    """
    debugiq_task_id = str(uuid.uuid4())

    try:
        # Create initial DebugIQTask record in this service's DB
        new_debugiq_task = DebugIQTask(
            id=debugiq_task_id,
            task_type="suggest_patch",
            status="pending",
            progress=0,
            current_stage="Queued",
            payload=request.dict(), # Store the full incoming request payload
            logs="Patch suggestion task received and queued."
        )
        db.add(new_debugiq_task)
        db.commit()
        db.refresh(new_debugiq_task)

        # Dispatch the patch suggestion task to DebugIQ's Celery queue
        run_patch_suggestion_task.delay(request.dict(), debugiq_task_id)

        logger.info(f"Patch suggestion request received. Internal Task ID: {debugiq_task_id}. Task created in DB and dispatched.")

        return {
            "status": "accepted",
            "message": "Patch suggestion task started in background.",
            "debugiq_task_id": debugiq_task_id # Return DebugIQ's internal task ID
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"DebugIQ: Error initiating patch suggestion task {debugiq_task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate patch suggestion task: {e}")


# === API Endpoint: GET /debugiq/status/{task_id} (REST for Task Status) ===
@router.get("/status/{task_id}", response_model=DebugIQTaskStatusResponse)
async def get_debugiq_task_status_endpoint(task_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the current status and details of a DebugIQ task from the database.
    """
    task = db.query(DebugIQTask).filter(DebugIQTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="DebugIQ Task not found.")

    # Convert SQLAlchemy model to Pydantic DebugIQTaskStatusResponse
    return DebugIQTaskStatusResponse(
        task_id=task.id,
        task_type=task.task_type,
        status=task.status,
        current_stage=task.current_stage,
        progress=task.progress,
        logs=task.logs if task.logs else "",
        output_data=task.output_data if task.output_data else {},
        details=task.details if task.details else {}
    )


# === WebSocket Endpoint: /ws/debugiq/status/{task_id} (Real-time Task Updates) ===
@router.websocket("/ws/status/{task_id}")
async def websocket_debugiq_status_endpoint(websocket: WebSocket, task_id: str):
    """
    Provides real-time updates for a specific DebugIQ task via WebSocket.
    """
    await websocket.accept()
    logger.info(f"DebugIQ WebSocket client connected for task_id: {task_id}")

    r = await get_debugiq_redis_client() # Get DebugIQ's async Redis client
    pubsub = r.pubsub()
    channel_name = f"debugiq_task_updates:{task_id}" # Specific channel for DebugIQ tasks
    await pubsub.subscribe(channel_name)

    try:
        # Frontend should make an initial GET request to /debugiq/status/{task_id} first
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
            await asyncio.sleep(0.1) # Small sleep to prevent busy-waiting
    except WebSocketDisconnect:
        logger.info(f"DebugIQ WebSocket client disconnected from task_id: {task_id}")
    except Exception as e:
        logger.error(f"DebugIQ WebSocket error for task_id {task_id}: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
