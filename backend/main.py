import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from .config import settings, PROVIDERS
from .sessions import sessions
from .agent import run_agent_loop

app = FastAPI(title="Code-Buddy Agent", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CreateSessionRequest(BaseModel):
    workspace: str = "."
    model: str
    provider: str
    api_key: str

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
async def health():
    return {"ok": True, "providers": list(PROVIDERS.keys())}

@app.post("/sessions")
async def create_session(req: CreateSessionRequest):
    ws = Path(req.workspace).expanduser().resolve()
    if not ws.exists():
        raise HTTPException(400, f"Workspace does not exist: {ws}")
    
    provider_info = PROVIDERS.get(req.provider)
    if not provider_info:
        raise HTTPException(400, "Invalid provider")
        
    s = sessions.create(ws, req.model, req.api_key, provider_info["base_url"])
    return {"session_id": s.id, "workspace": str(s.workspace), "model": s.model}

@app.post("/sessions/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    async def event_gen():
        try:
            async for ev in run_agent_loop(s, req.message):
                yield {"event": ev["type"], "data": json.dumps(ev)}
        except asyncio.CancelledError:
            yield {"event": "aborted", "data": "{}"}

    return EventSourceResponse(event_gen())