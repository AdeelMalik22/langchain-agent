# LangChain AI Agent with Model Context Protocol (MCP)

An intelligent, guardrailed AI agent built with LangChain that leverages the `openai/gpt-oss-120b:free` model from OpenRouter. The agent communicates with local services (Gmail and Audio/Image helpers) using the Model Context Protocol (MCP) to perform complex tasks on behalf of the user.

---

## Architecture Overview

This project implements a modular agent loop featuring input/output guardrails and an MCP Server ecosystem:

1. **User Command Line Interface**: Reads user requests.
2. **Input Guardrails**: Rejects safety violations, hateful content, and prompt injection attempts before they reach the LLM.
3. **Agent Loop (LangChain)**: Binds active MCP tools to the OpenRouter LLM. Invocations and tool executions are routed dynamically.
4. **MCP Servers**: Standalone subprocesses running FastMCP servers for Gmail actions and Image/Audio processing.
5. **Output Guardrails**: Validates final replies and intermediate tool results (like audio transcripts) against safety policies.

---

## Active Features & Tools

### 1. Gmail Tools (MCP-driven)
*   **`gmail_read`**: Reads the latest emails from your inbox.
*   **`gmail_search`**: Searches your inbox by sender or subject.
*   **`gmail_save_draft`**: Creates and saves an email draft in your draft folder without sending.
*   **`gmail_send_draft`**: Locates a draft by subject and sends it.
*   **`gmail_send`**: Directly drafts and sends an email via SMTP.

### 2. Audio & Image Tools (MCP-driven)
*   **`audio_to_text`**: Transcribes a local audio file.
*   **`transcribe_audio_url`**: Downloads audio from a URL and transcribes it.
*   **`image_to_text`**: Prepares local images for analysis (encodes them as base64 data URIs).

### 3. Guardrail Protections
*   **Input Guardrails**: Sanitizes input and checks against hate speech regex, prompt injections, and blocked terms.
*   **Output Guardrails**: Filters LLM responses and generated audio transcripts for injection attempts or inappropriate language.

---

## Project Structure

```
agent/
├── main.py                    # Application entry point and interactive CLI loop
├── system_prompt.py           # Core agent guidelines, rules, and prompt constraints
├── requirements.txt           # Python packages and project dependencies
├── .env                       # Environment variables (to be created)
├── claude.md                  # Detailed developer and AI assistant documentation
│
├── agents/
│   └── agent.py               # Configures the LangChain chat model and coordinates the reasoning loop
│
├── guardrails/
│   ├── input_guardrails.py    # Checks user inputs before invoking the agent
│   └── output_guardrails.py   # Checks agent outputs and transcripts before printing
│
└── mcp_core/
    ├── mcp_manager.py         # Asynchronously manages the lifecycle of stdio-based MCP clients
    ├── tool_routing.py        # Routes tool executions to their designated MCP server sessions
    ├── internal_tools/
    │   └── audio_model.py     # Local Whisper model loader for transcribing audio
    ├── mcp_clients/
    │   ├── gmail_mcp_client.py   # Client interface for Gmail MCP server
    │   └── audio_image_client.py # Client interface for Audio/Image MCP server
    └── mcp_servers/
        ├── gmail_server.py       # IMAP/SMTP FastMCP server for Gmail integrations
        └── image_audio_server.py # FastMCP server for image-to-text formatting and audio transcription
```

---

## Prerequisites

*   Python 3.8+
*   An active OpenRouter API Key
*   A Gmail Address and Google App Password (required for IMAP/SMTP integrations)

---

## Installation & Setup

1.  **Clone the repository and enter the directory:**
    ```bash
    git clone <repository-url>
    cd agent
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the project root containing:
    ```env
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    GMAIL_ADDRESS=your_gmail_address_here
    GMAIL_APP_PASSWORD=your_gmail_app_password_here
    ```

    > [!IMPORTANT]
    > **Gmail credentials require an App Password.** Regular Google passwords will fail due to authentication blocks. Visit your Google Account settings, go to Security, and generate a new **App Password**.

---

## Usage

Start the agent in interactive terminal mode:
```bash
python main.py
```

### Example Commands
*   *"Read my latest 3 emails"*
*   *"Search for emails with subject 'Meeting'"*
*   *"Save draft to test@example.com with subject 'Hello' and body 'This is a test draft'"*
*   *"Send the draft with subject 'Hello'"*
*   *"Transcribe the audio file at path media/transcribing_1.mp3"*

Type `exit` or `quit` to terminate the session.


## Developer Documentation

For deep dives into codebase execution flow, lifecycle events, and MCP message formats, refer to [claude.md](./claude.md).