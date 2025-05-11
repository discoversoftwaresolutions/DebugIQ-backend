# app/main.py
from fastapi import FastAPI
from app.api.autonomous_router import router as autonomous_router

app = FastAPI()
app.include_router(autonomous_router, prefix="/workflow")

@app.get("/")
def health_check():
    return {"status": "DebugIQ Core API running"}
