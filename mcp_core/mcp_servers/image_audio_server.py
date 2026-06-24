import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
import base64
import tempfile
import requests
from mcp_core.internal_tools.audio_model import transcribe_file

audio_img_mcp = FastMCP("Audio Img Server")


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def encode_audio_to_base64(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")


@audio_img_mcp.tool(
    description="Transcribe an audio file. Accepts local file paths."
)
def audio_to_text(audio_path: str):
    try:
        text = transcribe_file(audio_path)

        return {
            "type": "transcript",
            "text": text
        }

    except Exception as e:
        return f"Audio error: {e}"


@audio_img_mcp.tool(
    description="Download audio from URL and transcribe it"
)
def transcribe_audio_url(url: str):
    try:
        from internal_tools.audio_model import transcribe_file
        r = requests.get(url)

        tmp = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )

        tmp.write(r.content)
        tmp.close()

        text = transcribe_file(tmp.name)

        return {
            "type": "transcript",
            "text": text
        }

    except Exception as e:
        return str(e)


@audio_img_mcp.tool(description="Use this tool for image analysis")
def image_to_text(path: str):
    image_str = encode_image(path)

    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpg;base64,{image_str}"
        }
    }


if __name__ == "__main__":
    audio_img_mcp.run()
