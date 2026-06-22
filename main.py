from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage
)

from guardrils.input_guardrils import verify_user_input
from system_prompt import SYSTEM_PROMPT
from tools import ALL_TOOLS, TOOL_MAP, encode_image, encode_audio_to_base64

load_dotenv()


model = init_chat_model(
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    model_provider="openrouter",
    temperature=0
)

agent = model.bind_tools(ALL_TOOLS)


messages = [
    SystemMessage(content=SYSTEM_PROMPT)
]
def run_agent(query: str, image_path="/home/enigmatix/agent/media/istockphoto-1277822133-612x612.jpg", audio_path="/home/enigmatix/agent/media/thesoundofenglish-pronunciationstudio/transcribing_1.mp3"):

    if image_path:
        image_data = encode_image(image_path)

        messages.append(
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": query
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpg;base64,{image_data}"
                        }
                    }
                ]
            )
        )
    if audio_path:
        audio_data = encode_audio_to_base64(audio_path)

        messages.append(
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": query
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_data,
                            "format": "mp3"
                        }
                    }
                ]
            )
        )

    else:
        messages.append(
            HumanMessage(content=query)
        )


    while True:
        print("🤔 Thinking...")

        response = agent.invoke(messages)

        messages.append(response)

        if not response.tool_calls:
            return response.content or "No response."


        for call in response.tool_calls:

            tool_result = TOOL_MAP[call["name"]].invoke(
                call["args"]
            )

            messages.append(
                ToolMessage(
                    content=str(tool_result),
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

        answer = run_agent(query)
        print(f"\n✅ Answer: {answer}\n")


if __name__ == "__main__":
    main()