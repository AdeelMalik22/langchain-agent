import asyncio
from agents.agent import run_agent
from guardrails.input_guardrails import verify_user_input
from mcp_core.mcp_clients.audio_image_client import AudioImageClient
from mcp_core.mcp_clients.gmail_mcp_client import GmailClient
from mcp_core.mcp_manager import MCPManager


async def main():
    async with MCPManager([
        GmailClient(),
        AudioImageClient()
    ]) as (sessions, tools, tool_map):
        while True:
            try:
                query = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                break

            if not query:
                continue

            if query.lower() in ("exit", "quit"):
                print("👋 Goodbye!")
                break

            query_input = verify_user_input(query)
            if not query_input.allowed:
                print(f"Invalid input: {query_input.reason}")
                continue

            answer = await run_agent(query, tools, tool_map)
            print(f"\n🤖 Answer: {answer}\n")

if __name__ == "__main__":
    asyncio.run(main())