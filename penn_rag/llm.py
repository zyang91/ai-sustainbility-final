"""Minimal client for the local Ollama server."""
import requests

from .config import LLM_MODEL, NUM_CTX, OLLAMA_URL, TEMPERATURE


class LLMError(RuntimeError):
    """Ollama is not running, or the model is missing. The message says what to do."""


def status(model: str = LLM_MODEL) -> str:
    """Empty string when the model is ready; otherwise what to fix."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
    except requests.RequestException:
        return "Ollama is not running. Install it from ollama.com, then start it (`ollama serve` or open the app)."
    names = [m["name"] for m in r.json().get("models", [])]
    if not any(n == model or n.split(":")[0] == model for n in names):
        return f"The model `{model}` is not downloaded. Run `ollama pull {model}`."
    return ""


def chat(messages: list[dict], tools: list[dict] | None = None, model: str = LLM_MODEL,
         temperature: float = TEMPERATURE) -> dict:
    """One round with the chat model. Returns its reply message."""
    body = dict(model=model, messages=messages, stream=False, options={"temperature": temperature, "num_ctx": NUM_CTX})
    if tools:
        body["tools"] = tools
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=180)
    except requests.RequestException as e:
        raise LLMError(status(model) or str(e)) from e
    if not r.ok:
        try:
            detail = r.json().get("error", r.text)
        except ValueError:
            detail = r.text
        raise LLMError(status(model) or f"Ollama error {r.status_code}: {detail}")
    return r.json()["message"]
