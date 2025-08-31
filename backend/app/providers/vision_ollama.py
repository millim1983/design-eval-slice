# app/providers/vision_ollama.py
import os, base64, requests

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("ANALYSIS_MODEL", "llava:7b")

def analyze(prompt: str, image_bytes: bytes | None = None) -> str:
    msg = {"role": "user", "content": []}
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode()
        msg["content"].append({"type": "image", "image": b64})
    msg["content"].append({"type": "text", "text": prompt})

    r = requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json={"model": MODEL, "messages": [msg], "stream": False},
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]
