# File: backend/debugiq_celery.py (DebugIQ Service)
from celery import Celery
import os

# --- Redis URL from environment variable for this Celery app ---
REDIS_URL = os.getenv("DEBUGIQ_REDIS_URL", "redis://localhost:6379/3")

celery_app = Celery(
    'debugiq_tasks', # Unique name for this Celery app
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks.debugging_tasks'] # Tell Celery where to find your tasks
)

celery_app.conf.timezone = 'UTC'
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
