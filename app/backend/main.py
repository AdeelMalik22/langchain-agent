import sys
import os

# Ensure project root is on sys.path so agent/ guardrails/ mcp_core/ resolve
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.user.router import router as user_routers
from api.books.router import router as books_routers
from api.university.router import router as university_routers
from api.department.router import router as department_routers
from api.chat.router import router as chat_router, set_mcp_state

from mcp_core.mcp_clients.audio_image_client import AudioImageClient
from mcp_core.mcp_clients.github_client import GithubClient
from mcp_core.mcp_clients.uni_client import UniClient
from mcp_core.mcp_clients.gmail_mcp_client import GmailClient
from mcp_core.mcp_manager import MCPManager


# ── Lifespan: boot MCP clients once ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # MCP clients use relative paths (e.g. "mcp_core/mcp_servers/gmail_server.py")
    # so we must run from the project root regardless of where uvicorn was launched.
    os.chdir(_PROJECT_ROOT)

    manager = MCPManager([
        GmailClient(),
        AudioImageClient(),
        GithubClient(),
        UniClient(),
    ])
    _, tools, tool_map = await manager.__aenter__()
    set_mcp_state(tools, tool_map)
    print("✅ MCP clients ready")

    yield

    await manager.__aexit__(None, None, None)
    print("🔌 MCP clients shut down")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Agent API",
    description="LangChain MCP-powered agent + University backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Existing routers ───────────────────────────────────────────────────────────
app.include_router(user_routers)
app.include_router(books_routers)
app.include_router(university_routers)
app.include_router(department_routers)

# ── Chat router ────────────────────────────────────────────────────────────────
app.include_router(chat_router)

# ── Serve frontend static files ────────────────────────────────────────────────
_FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_FRONTEND):
    app.mount("/static", StaticFiles(directory=_FRONTEND), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_ui():
        return FileResponse(os.path.join(_FRONTEND, "index.html"))