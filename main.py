from dotenv import load_dotenv
import asyncio

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    SystemMessage
)

from guardrails.input_guardrails import verify_user_input
from guardrails.output_guardrails import verify_assistant_output
from mcp_clients.gmail_mcp_client import GmailClient
from system_prompt import SYSTEM_PROMPT

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
async def run_agent(query: str,session,tools):

    model_with_tools = model.bind_tools(tools)
    messages.append(HumanMessage(content=query))


    while True:
        print("🤖 Thinking...")

        response = model_with_tools.invoke(messages)


        if response.tool_calls:

            messages.append(response)

            for call in response.tool_calls:

                tool_name = call["name"]
                tool_args = call["args"]

                tool_result = await session.call_tool(
                    tool_name,
                    tool_args
                )


                # Guard tool result
                tool_guard = verify_assistant_output(
                    str(tool_result.content)
                )

                if not tool_guard.allowed:
                    return (
                        f"Blocked tool output: "
                        f"{tool_guard.reason}"
                    )


                messages.append(
                    ToolMessage(
                        content=str(tool_result.content),
                        tool_call_id=call["id"]
                    )
                )
            continue

        guard = verify_assistant_output(
            response.content
        )

        if not guard.allowed:
            return (
                f"Blocked: {guard.reason}"
            )

        messages.append(response)

        return guard.normalize_text

async def main():
    async with GmailClient() as (session, tools):

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

            answer = await run_agent(query, session, tools)
            print(f"\n🤖 Answer: {answer}\n")

if __name__ == "__main__":
    asyncio.run(main())