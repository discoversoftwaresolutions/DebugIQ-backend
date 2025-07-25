# File: backend/app/models.py (DebugIQ Service)
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any, Optional

# --- SQLAlchemy Base for DebugIQ ---
# Use your existing Base if you have one globally shared, otherwise define it here.
Base = declarative_base()

# --- DebugIQTask Model Definition ---
class DebugIQTask(Base):
    __tablename__ = "debugiq_tasks" # Unique table name for DebugIQ's tasks

    id = Column(String, primary_key=True, index=True) # task_id from incoming request
    task_type = Column(String, nullable=False) # e.g., "suggest_patch", "test_execution", "log_analysis"
    status = Column(String, default="pending", nullable=False) # e.g., "pending", "running", "patch_generated", "failed", "completed"
    current_stage = Column(String, nullable=True) # e.g., "LLM Call", "Parsing Response", "Test Run"
    progress = Column(Integer, default=0, nullable=False) # 0-100

    # Payload (input data for the task, e.g., code, prompt)
    payload = Column(JSON, nullable=False)

    # Output and Logging
    logs = Column(Text, nullable=True) # Accumulated logs or a link to logs
    output_data = Column(JSON, nullable=True) # Final output (e.g., {"diff": "...", "explanation": "..."})
    details = Column(JSON, nullable=True) # For additional structured data like errors

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DebugIQTask(id='{self.id}', type='{self.task_type}', status='{self.status}', progress={self.progress})>"

# This Pydantic model will be used for API responses and task payloads
class DebugIQTaskStatusResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    current_stage: Optional[str] = None
    progress: int = 0
    logs: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
