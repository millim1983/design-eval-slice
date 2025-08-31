import base64
import json
import os
from typing import Optional

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava:7b")

def generate(prompt: str, image: Optional[bytes] = None) -> str:
    """Send a prompt (and optional image) to a local Ollama server.

    The server must have the specified model pulled.  This function streams
    the response text and returns the concatenated string.
    """
    payload: dict[str, object] = {"model": OLLAMA_MODEL, "prompt": prompt}
    if image is not None:
        payload["images"] = [base64.b64encode(image).decode("utf-8")]
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate", json=payload, stream=True, timeout=120
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    text = ""
    for line in resp.iter_lines():
        if not line:
            continue
        data = json.loads(line)
        text += data.get("response", "")
        if data.get("done"):
            break
    return text
