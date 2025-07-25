# File: backend/app/database.py (DebugIQ Service)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from .models import Base # Import DebugIQ's specific Base

logger = logging.getLogger(__name__)

# --- Database URL from environment variables for DebugIQ ---
DATABASE_URL = os.getenv("DEBUGIQ_DATABASE_URL") # Use a unique env var for DebugIQ's DB
if not DATABASE_URL:
    raise ValueError("DEBUGIQ_DATABASE_URL environment variable not set for DebugIQ Backend.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to create tables (run once, e.g., at app startup or via migration)
def create_db_tables():
    logger.info("Creating DebugIQ database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("DebugIQ database tables created.")

# Dependency to get DB session in FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
