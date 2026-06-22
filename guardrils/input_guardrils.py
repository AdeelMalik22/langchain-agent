from dataclasses import dataclass
import re


_BLOCKED_PHRASES = (
    "ignore previous instructions",
    "reveal your system prompt",
    "show hidden prompt",
    "bypass safety",
    "jailbreak",
)

_PROTECTED_GROUPS = [
    "muslim",
    "christian",
    "jain",
    "hindu",
    "white",
    "black",
    "religion",
    "language",
    "children",
    "man",
    "woman",
]

_GROUP_PATTERN = "|".join(_PROTECTED_GROUPS)

HATEFUL_PHRASES = (
    re.compile(
    rf"\b(hate|kill|humiliate|bully|attack|murder|racism|deport)\b"
    rf".{{0,30}}?"
    rf"\b({_GROUP_PATTERN})s?\b",
    re.IGNORECASE
),
    re.compile(
        rf"{_GROUP_PATTERN}s?\b"
          rf".{0,30}?"
          rf"\b(hate|kill|humiliate|bully|attack|murder|racism|deport)\b",
          re.IGNORECASE
    )
)


PROMPT_INJECTION = re.compile(
    r"(show|tell|reveal|give).{0,30}(system|hidden|prompt|instruction)",
    re.I
)


@dataclass(frozen=True)
class InputGaurdrils:
    allowed: bool
    normalize_text: str
    reason: str = ""

def contain_hate_speach(input:str):
    if HATEFUL_PHRASES.search(input):
        return True
    return False

def normalize_text(input: str):
    return input.strip().lower()


def verify_user_input(user_input: str):
    if not user_input:
        return InputGaurdrils(False,"", "Input cannot be empty")

    normalize_input = normalize_text(user_input)
    if not normalize_input:
        return InputGaurdrils(False,"", "Input cannot be empty")
    normalize_lower = normalize_input.lower()

    for phrase in _BLOCKED_PHRASES:
        if phrase in normalize_lower:
            return InputGaurdrils(False, "",f"Input contains blocked phrase: {phrase}")

    if contain_hate_speach(normalize_input):
        return InputGaurdrils(
            False,
            "",
            "Hateful content detected"
        )

    if PROMPT_INJECTION.search(normalize_lower):
        return InputGaurdrils(
            False,
            "",
            "Prompt injection detected"
        )
    return InputGaurdrils(True,normalize_input)

