# LangChain AI Agent with Model Context Protocol (MCP)

An intelligent, guardrailed AI agent built with LangChain and powered by OpenRouter. The agent is served through a **FastAPI backend** with a built-in **chat UI**, Redis response caching, and Kafka event logging. It communicates with multiple local MCP servers to perform complex tasks — reading email, browsing GitHub, transcribing audio, and interacting with a University management backend.

---

## Architecture Overview

```
Browser / Chat UI
       │  HTTP
       ▼
┌─────────────────────────────────┐
│        FastAPI Backend          │
│  ┌──────────┐  ┌─────────────┐  │
│  │  REST    │  │  /chat      │  │
│  │  Routers │  │  /message   │  │
│  └──────────┘  └──────┬──────┘  │
│                        │        │
│          ┌─────────────▼──────┐  │
│          │  Input Guardrails  │  │
│          └─────────────┬──────┘  │
│                        │        │
│          ┌─────────────▼──────┐  │
│          │  LangChain Agent   │  │
│          │  (OpenRouter LLM)  │  │
│          └─────────────┬──────┘  │
│                        │        │
│          ┌─────────────▼──────┐  │
│          │   MCP Tool Router  │  │
│          └──┬──┬──┬──┬────────┘  │
└────────────────────────────────┘
             │  │  │  │
    ┌────────┘  │  │  └──────────┐
    ▼           ▼  ▼             ▼
 Gmail      GitHub  Audio/   University
 Server     Server  Image    Backend
                    Server   Server
```

**Request lifecycle:**
1. **Chat UI / API client** sends a message to `POST /chat/message`
2. **Redis Cache** is checked — cache hit returns instantly, no LLM call made
3. **Input Guardrails** reject unsafe, hateful, or injected content
4. **LangChain Agent** reasons over the query and invokes MCP tools as needed
5. **MCP Servers** execute the actual actions (email, GitHub, audio, university data)
6. The reply is cached in Redis and returned to the client
7. **Kafka** logs key events (logins, etc.) asynchronously

---

## Features & Tools

### 🤖 AI Agent
- Powered by `openai/gpt-oss-120b:free` via **OpenRouter**
- Full ReAct tool-use loop via **LangChain**
- Guardrailed input/output for safety

### 📧 Gmail Tools (MCP)
| Tool | Description |
|---|---|
| `gmail_read` | Read latest emails from inbox |
| `gmail_search` | Search by sender or subject |
| `gmail_save_draft` | Save a draft without sending |
| `gmail_send_draft` | Find a draft by subject and send it |
| `gmail_send` | Directly compose and send an email |

### 🐙 GitHub Tools (MCP)
| Tool | Description |
|---|---|
| `search_repositories` | Search GitHub repos by query |
| `get_repository` | Get details of a specific repo |
| `list_commits` | List recent commits on a branch |
| `get_file_contents` | Read a file from a repo |
| `create_issue` | Open a new issue |
| `list_issues` | List open issues on a repo |
| `create_pull_request` | Open a pull request |

### 🎵 Audio & Image Tools (MCP)
| Tool | Description |
|---|---|
| `audio_to_text` | Transcribe a local audio file |
| `transcribe_audio_url` | Download and transcribe audio from a URL |
| `image_to_text` | Encode a local image as base64 for analysis |

### 🏫 University Backend Tools (MCP)
| Tool | Description |
|---|---|
| `user_login` | Authenticate a user and retrieve a token |
| `get_departments` | Fetch all departments |

### 🛡️ Guardrails
- **Input**: Blocks hate speech, prompt injection, and blacklisted terms before hitting the LLM
- **Output**: Validates agent replies and transcripts before returning to the user

### ⚡ Redis Caching
- Identical queries are served from cache — **no repeated LLM or tool calls**
- Cache TTL: 120 seconds (configurable per route)

### 📨 Kafka Event Logging
- Key events (e.g. user login) are published to a Kafka topic
- Kafka + Zookeeper run via Docker Compose

---

## Project Structure

```
agent/
├── main.py                        # CLI entry point (terminal-based agent)
├── system_prompt.py               # Agent guidelines and prompt constraints
├── requirements.txt               # Root-level Python dependencies
├── .env                           # Environment variables (create from .env.example)
├── .env.example                   # Template for required env vars
├── claude.md                      # Developer documentation and execution flow
│
├── agents/
│   └── agent.py                   # LangChain agent: model binding and reasoning loop
│
├── guardrails/
│   ├── input_guardrails.py        # Pre-LLM safety checks
│   └── output_guardrails.py       # Post-LLM output validation
│
├── mcp_core/
│   ├── mcp_manager.py             # Lifecycle manager for all MCP stdio clients
│   ├── tool_routing.py            # Routes tool calls to the correct MCP session
│   ├── internal_tools/
│   │   └── audio_model.py         # Local Whisper model loader
│   ├── mcp_clients/
│   │   ├── gmail_mcp_client.py    # Gmail MCP client
│   │   ├── github_client.py       # GitHub MCP client
│   │   ├── audio_image_client.py  # Audio/Image MCP client
│   │   └── uni_client.py          # University backend MCP client
│   └── mcp_servers/
│       ├── gmail_server.py        # IMAP/SMTP FastMCP server
│       ├── github_server.py       # GitHub API FastMCP server
│       ├── image_audio_server.py  # Audio/Image FastMCP server
│       └── uni_backend_server.py  # University backend FastMCP server
│
└── app/
    └── backend/
        ├── main.py                # FastAPI app: lifespan, routers, static files
        ├── docker-compose.yaml    # Kafka + Zookeeper services
        ├── requirements.txt       # Backend-specific dependencies
        ├── frontend/              # Chat UI (HTML/CSS/JS)
        └── api/
            ├── chat/
            │   └── router.py      # POST /chat/message — agent endpoint with caching
            ├── user/              # User auth endpoints
            ├── books/             # Books CRUD endpoints
            ├── university/        # University endpoints
            ├── department/        # Department endpoints
            └── utils/
                ├── redis_client.py   # Redis client + @cache decorator
                ├── kafka_producer.py # Kafka event publisher
                ├── kafka_consumer.py # Kafka event consumer
                ├── auth.py           # JWT auth utilities
                ├── hash_password.py  # Password hashing
                └── db_collection.py  # Database helpers
```

---

## Prerequisites

- Python 3.9+
- Redis (running on `localhost:6379`)
- Docker & Docker Compose (for Kafka)
- An active **OpenRouter API Key**
- A **Gmail** address with an App Password
- A **GitHub Personal Access Token** (scopes: `repo`, `workflow`, `public_repo`)

---

## Installation & Setup

### 1. Clone and enter the repo
```bash
git clone <repository-url>
cd agent
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
# Root-level agent dependencies
pip install -r requirements.txt

# Backend dependencies
pip install -r app/backend/requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password_here
```

> [!IMPORTANT]
> **Gmail requires an App Password**, not your regular Google password. Generate one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

> [!IMPORTANT]
> **GitHub token** needs `repo`, `workflow`, and `public_repo` scopes. Generate one at [github.com/settings/tokens](https://github.com/settings/tokens).

### 5. Start infrastructure services
```bash
cd app/backend
docker-compose up -d
```
This starts Kafka and Zookeeper.

### 6. Start Redis
```bash
redis-server
```

---

## Running the Application

### Web Backend (with Chat UI)
```bash
cd app/backend
uvicorn main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser to use the chat interface.

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Chat UI frontend |
| `/chat/message` | POST | Send a message to the agent |
| `/chat/health` | GET | Check if the agent is ready |
| `/user/api/v1/login` | POST | User authentication |
| `/department/api/v1` | GET | List departments |

### Terminal CLI (standalone agent)
```bash
python main.py
```

Type `exit` or `quit` to end the session.

### Example Prompts
- *"Read my latest 3 emails"*
- *"Search GitHub for LangChain repositories"*
- *"Get all departments"*
- *"Transcribe the audio file at media/recording.mp3"*
- *"Save a draft to test@example.com with subject 'Hello'"*

---

## Caching Behaviour

Responses from `POST /chat/message` are cached in Redis for **120 seconds**. If the same message is sent again within that window, the cached response is returned immediately without calling the LLM or any MCP tools.

You will see these log messages:
```
CACHE HIT   ← served from Redis, no API call made
CACHE MISS  ← first time seen, agent runs and result is stored
```

---

## Developer Documentation

For deep dives into the execution flow, MCP message formats, and lifecycle events, see [claude.md](./claude.md).