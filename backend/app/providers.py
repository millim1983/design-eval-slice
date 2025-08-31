"""Inference provider abstractions.

This module exposes a minimal provider factory so different backends
(ollama, vLLM, TGI, etc.) can be swapped without changing the application
logic.  Only the Ollama provider is implemented for now.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import os
from typing import Any, Dict, Type

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class Provider(ABC):
    """Abstract interface for inference providers."""

    @abstractmethod
    async def generate(self, prompt: str, model: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a generation request against the provider."""


class OllamaProvider(Provider):
    """Provider implementation that talks to an Ollama server."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")

    async def generate(self, prompt: str, model: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {"model": model, "prompt": prompt, **kwargs}
        try:
            timeout = httpx.Timeout(60.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.ConnectError as exc:
            logger.error("Ollama server unreachable at %s", url)
            raise HTTPException(
                status_code=503,
                detail=f"Ollama server is unreachable at {url}",
            ) from exc
        except httpx.ReadTimeout as exc:
            raise HTTPException(status_code=504, detail="Ollama server timed out") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid response from Ollama server") from exc


class ProviderFactory:
    """Factory class returning provider instances by name."""

    _registry: Dict[str, Type[Provider]] = {
        "ollama": OllamaProvider,
        # Future providers can be added here, e.g.:
        # "vllm": VLLMProvider,
        # "tgi": TGIProvider,
    }

    @classmethod
    def get(cls, name: str) -> Provider:
        """Return a provider instance for ``name``.

        Args:
            name: Identifier for the provider (e.g. ``"ollama"``).

        Raises:
            ValueError: If the provider name is unknown.
        """
        provider_cls = cls._registry.get(name)
        if provider_cls is None:
            raise ValueError(f"Unknown provider: {name}")
        return provider_cls()
