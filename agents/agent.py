import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    SystemMessage
)

from guardrails.output_guardrails import verify_assistant_output
from mcp_core.tool_routing import ToolRouter
from system_prompt import SYSTEM_PROMPT


load_dotenv()


# LLM
model = init_chat_model(
        os.getenv("AGENT_MODEL"),
        model_provider="openrouter",
        temperature=0
)


async def run_agent(query: str, tools, tool_map):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]
    router = ToolRouter(tool_map)

    model_with_tools = model.bind_tools(tools)
    messages.append(HumanMessage(content=query))


    while True:
        print("🤖 Thinking...")

        response = await model_with_tools.ainvoke(messages)


        if response.tool_calls:

            messages.append(response)

            for call in response.tool_calls:

                tool_name = call["name"]
                tool_args = call["args"]

                tool_result = await router.call(tool_name, tool_args)

                # Guard tool result (only deep-check audio transcripts)
                tool_text = str(tool_result.content)

                if "transcript" in tool_text:
                    tool_guard = verify_assistant_output(tool_text)
                else:
                    tool_guard = type(
                        "Guard", (), {"allowed": True, "reason": ""}
                    )()

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