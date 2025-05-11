from fastapi import APIRouter

config_router = APIRouter()

@config_router.get("/api/config")
def get_frontend_config():
    return {
        "model": "gpt-4o",
        "backend": "FastAPI",
        "frontend": "Streamlit",
        "status": "Production Ready"
    }
