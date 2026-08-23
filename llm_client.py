"""
Thin wrapper around the Gemini API. Swap providers by editing this file
only -- routing, cost tracking, retry, and the budget guard don't touch
it.
"""
from google import genai

from observability.decorator import track
from observability.retry import call_with_backoff

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client()  # picks up GEMINI_API_KEY from the environment
    return _client


@track(model_arg="model")
def call_model(prompt: str, model: str):
    client = get_client()
    response = call_with_backoff(client.models.generate_content, model=model, contents=prompt)
    return response
