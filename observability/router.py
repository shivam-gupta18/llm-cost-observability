LITE_MODEL = "gemini-3.5-flash-lite"
FLASH_MODEL = "gemini-3.5-flash"

COMPLEX_KEYWORDS = ("explain why", "compare", "analyze", "reason", "step by step", "design")
LONG_PROMPT_THRESHOLD = 400  # characters


def choose_model(prompt: str) -> str:
    prompt_lower = prompt.lower()
    is_long = len(prompt) > LONG_PROMPT_THRESHOLD
    looks_complex = any(kw in prompt_lower for kw in COMPLEX_KEYWORDS)

    if is_long or looks_complex:
        return FLASH_MODEL
    return LITE_MODEL
