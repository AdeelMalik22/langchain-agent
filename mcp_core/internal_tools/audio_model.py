from faster_whisper import WhisperModel


whisper = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


def transcribe_file(path):

    segments, info = whisper.transcribe(path)

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text.strip()
