# File: app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core DebugIQ Modules
from app.api import analyze, qa, doc, config, voice
from app.api.voice_interactive_router import router as voice_interactive_router
from app.api.voice_ws_router import router as voice_ws_router
from app.api.autonomous_router import router as autonomous_router
from app.api.metrics_router import router as metrics_router
from app.api.issues_router import router as issues_router

# Initialize the app
app = FastAPI(
    title="DebugIQ API",
    description="Autonomous debugging pipeline powered by GPT-4o and agents.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Replace with your frontend domain(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analyze.router, prefix="/debugiq", tags=["Analysis"])
app.include_router(qa.router, prefix="/qa", tags=["Quality Assurance"])
app.include_router(doc.router, prefix="/doc", tags=["Documentation"])
app.include_router(config.config_router, prefix="/api", tags=["Configuration"])
app.include_router(voice.router, prefix="/voice", tags=["Voice REST"])
app.include_router(voice_interactive_router, prefix="/voice", tags=["Voice Interactive"])
app.include_router(voice_ws_router, tags=["Voice WebSocket"])
app.include_router(autonomous_router, prefix="/workflow", tags=["Autonomous Workflow"])
app.include_router(metrics_router, tags=["Metrics"])
app.include_router(issues_router, tags=["Issues"])

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the DebugIQ API"}

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}
