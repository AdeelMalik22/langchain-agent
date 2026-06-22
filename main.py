from dotenv import load_dotenv
import asyncio

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    SystemMessage
)

from guardrails.input_guardrails import verify_user_input
from system_prompt import SYSTEM_PROMPT
from tools import encode_image, encode_audio_to_base64
from langchain_mcp_adapters.tools import load_mcp_tools

from mcp import ClientSession, stdio_client, StdioServerParameters

load_dotenv()


# LLM
model = init_chat_model(
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    model_provider="openrouter",
    temperature=0
)



messages = [
    SystemMessage(content=SYSTEM_PROMPT)
]
SERVER_PATH = "python tools.py"
async def run_agent(query: str):

    server_params = StdioServerParameters(
        command="python",
        args=["tools.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()
            langchain_tools = await load_mcp_tools(session)
            model_with_tools = model.bind_tools(langchain_tools)
            messages.append(HumanMessage(content=query))


            while True:
                print("🤖 Thinking...")

                response = model_with_tools.invoke(messages)

                messages.append(response)
                print(response)

                if not hasattr(response, "tool_calls") or not response.tool_calls:
                    return response.content or "No response"

                for call in response.tool_calls:

                    tool_name = call["name"]
                    tool_args = call["args"]

                    print(f"🔧 Calling MCP tool: {tool_name}")

                    tool_result = await session.call_tool(
                        tool_name,
                        tool_args
                    )

                    messages.append(
                        ToolMessage(
                            content=str(tool_result.content),
                            tool_call_id=call["id"]
                        )
                    )

def main():
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

        answer = asyncio.run(run_agent(query))

        print(f"\n✅ Answer: {answer}\n")


if __name__ == "__main__":
    main()