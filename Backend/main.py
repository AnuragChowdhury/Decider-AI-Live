import sys
print(">>> [MAIN] Starting script...", flush=True)
import dotenv
import os

# Load env vars before importing agents that initialize LLMs
print(">>> [MAIN] Loading dotenv...", flush=True)
dotenv.load_dotenv()

from fastapi import FastAPI, HTTPException
print(">>> [MAIN] Core imports done.", flush=True)
from core.schemas import AnalyticsInput, AnalyticsOutput, UIControllerInput, UIControllerOutput
from agents.analytics_agent import analytics_agent
from agents.ui_agent import ui_agent
import uvicorn
import os

print(">>> [MAIN] Initializing FastAPI app...", flush=True)
app = FastAPI(title="Decider-AI Backend", version="0.1.0")

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

# Get origins from env, strip whitespace and trailing slashes, and handle multiple origins
raw_origins = os.getenv("FRONTEND_URLS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173")
allowed_origins = [o.strip().rstrip('/') for o in raw_origins.split(",") if o.strip()]

print(f">>> [CORS] Allowed Origins: {allowed_origins}", flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Initialization
from core.database import engine
from core import models
models.Base.metadata.create_all(bind=engine)

# Routers
from routers import auth, session
app.include_router(auth.router)
app.include_router(session.router)
@app.get("/")
def read_root():
    return {"message": "Decider-AI Backend is running. Access /docs for API documentation."}

@app.post("/api/analyze", response_model=AnalyticsOutput)
def run_analytics(input_data: AnalyticsInput):
    """
    Endpoint to run the Analytics Agent.
    """
    try:
        result = analytics_agent.run(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ui", response_model=UIControllerOutput)
def run_ui_controller(input_data: UIControllerInput):
    """
    Endpoint to run the UI Controller Agent.
    """
    try:
        result = ui_agent.run(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Legacy Endpoints (Deprecated - use /api/upload and /api/chat instead) ---
# Keeping for backwards compatibility during transition

# from fastapi import File, UploadFile, Form
# from agents.orchestrator import orchestrator_graph

# @app.post("/api/chat_with_data")
# async def chat_with_data(
#     file: UploadFile = File(...),
#     query: str = Form(...),
#     validation_mode: str = Form("lenient"),
#     persist: bool = Form(True)
# ):
#     """
#     DEPRECATED: Use POST /api/upload followed by POST /api/chat instead.
#     """
#     pass

if __name__ == "__main__":
    # Ensure GROQ_API_KEY is available
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ Warning: GROQ_API_KEY not set. Agents may fail.")
        
    uvicorn.run(app, host="0.0.0.0", port=8000)
