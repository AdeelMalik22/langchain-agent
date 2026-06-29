import sys
import os

from api.utils.redis_client import cache

# Project root is 3 levels up from here (api/chat/router.py → backend → app → agent)
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.agent import run_agent
from guardrails.input_guardrails import verify_user_input

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    blocked: bool = False
    reason: str = ""


# ── Dependency: shared MCP state set by lifespan ───────────────────────────────
# Populated in main.py after MCPManager starts up.
_tools = None
_tool_map = None


def set_mcp_state(tools, tool_map):
    global _tools, _tool_map
    _tools = tools
    _tool_map = tool_map


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    """Check if the agent is ready."""
    return {"status": "ok", "agent_ready": _tools is not None}


@router.post("/message", response_model=ChatResponse)
@cache(expire=120)
async def send_message(request: ChatRequest):
    """Send a message to the AI agent and receive a reply."""
    if _tools is None or _tool_map is None:
        raise HTTPException(status_code=503, detail="Agent not ready yet. MCP clients are still starting.")

    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Input guardrail (same as main.py)
    guard = verify_user_input(query)
    if not guard.allowed:
        return ChatResponse(reply="", blocked=True, reason=guard.reason)

    try:
        answer = await run_agent(query, _tools, _tool_map)
        return ChatResponse(reply=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")
