import os
from fastapi import HTTPException
import httpx
from typing import Any, Dict

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

async def generate(prompt: str, model: str, **kwargs: Any) -> Dict[str, Any]:
    """Request a completion from the Ollama server.

    Args:
        prompt: Prompt text to send.
        model: Model name on the Ollama server.
        **kwargs: Additional fields to include in the payload.

    Returns:
        Parsed JSON response from the server.

    Raises:
        HTTPException: If unable to reach server, timeout occurs,
            or response cannot be decoded as JSON.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload: Dict[str, Any] = {"model": model, "prompt": prompt, **kwargs}
    payload["images"] = [base64.b64encode(image).decode("utf-8")]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail="Ollama server is unreachable") from exc
    except httpx.ReadTimeout as exc:
        raise HTTPException(status_code=504, detail="Ollama server timed out") from exc
    except httpx.HTTPError as exc:
        # Propagate other HTTP errors with status code 502
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Invalid response from Ollama server") from exc
main
