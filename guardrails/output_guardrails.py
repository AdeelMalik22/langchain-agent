from dataclasses import dataclass
import re

_PROTECTED_GROUPS = (
    "race",
    "religion",
    "ethnicity",
    "nationality",
    "immigrant",
    "refugee",
    "black",
    "white",
    "asian",
    "latino",
    "muslim",
    "christian",
    "jewish",
    "hindu",
    "woman",
    "women",
    "man",
    "men",
    "disabled",
)

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
class OutputGaurdrils:
    allowed: bool
    normalize_text: str
    reason: str = ""

def contain_hate_speach(input:str):
    for pattern in HATEFUL_PHRASES:
        hate_speach = pattern.search(input)
        if hate_speach:
            return True
    return False

def normalize_text(input: str):
    return input.strip().lower()


def verify_assistant_output(user_input:str):
    if not user_input:
        return OutputGaurdrils(False,"", "Output cannot be empty")

    normalize_input = normalize_text(user_input)
    if not normalize_input:
        return OutputGaurdrils(False,"", "Output cannot be empty")
    normalize_lower = normalize_input.lower()

    if contain_hate_speach(normalize_input):
        return OutputGaurdrils(
            False,
            "",
            "Hateful content detected"
        )

    if PROMPT_INJECTION.search(normalize_lower):
        return OutputGaurdrils(
            False,
            "",
            "Output injection detected"
        )
    return OutputGaurdrils(True,normalize_input)

