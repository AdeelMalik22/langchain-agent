from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from tools import ALL_TOOLS, TOOL_MAP

load_dotenv()


model = init_chat_model(
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    model_provider="openrouter",
    temperature=0
)

agent = model.bind_tools(ALL_TOOLS)


messages = []
def run_agent(query: str) -> str:
    messages.append(HumanMessage(content=query))

    while True:
        print("🤖 Thinking...")
        response = agent.invoke(messages)

        messages.append(response) # adding response in messages

        # If no tool calls --> model has a final answer
        if not response.tool_calls:
            return response.content or "No response."

        # Execute each tool the model requested
        for call in response.tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            tool_id   = call["id"]

            if tool_name not in TOOL_MAP:
                tool_result = f"Error: unknown tool '{tool_name}'"
            else:
                tool_result = TOOL_MAP[tool_name].invoke(tool_args)

            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_id)
            )

        # Loop continues --> model now sees tool results and decides next step


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

        answer = run_agent(query)
        print(f"\n✅ Answer: {answer}\n")


if __name__ == "__main__":
    main()