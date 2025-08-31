from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel


class ModelsConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama2"


class RagConfig(BaseModel):
    expert_url: str = ""
    evaluation_url: str = ""
    timeout: float = 30.0


class ObservabilityConfig(BaseModel):
    """Configuration block for observability hooks."""

    enabled: bool = False


class AppConfig(BaseModel):
    models: ModelsConfig = ModelsConfig()
    rag: RagConfig = RagConfig()
    prompts: Dict[str, Any] = {}
    policy: Dict[str, Any] = {}
    lora: Dict[str, Any] = {}
    observability: ObservabilityConfig = ObservabilityConfig()


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


@lru_cache
def load_config() -> AppConfig:
    base = Path(__file__).resolve().parents[2] / "config"
    models = _load_yaml(Path(os.getenv("MODELS_CONFIG", base / "models.yaml")))
    rag = _load_yaml(Path(os.getenv("RAG_CONFIG", base / "rag.yaml")))
    prompts = _load_yaml(Path(os.getenv("PROMPTS_CONFIG", base / "prompts.yaml")))
    policy = _load_yaml(Path(os.getenv("POLICY_CONFIG", base / "policy.yaml")))
    lora = _load_yaml(Path(os.getenv("LORA_CONFIG", base / "lora.yaml")))
    observability = _load_yaml(
        Path(os.getenv("OBSERVABILITY_CONFIG", base / "observability.yaml"))
    )
    return AppConfig(
        models=ModelsConfig(**models),
        rag=RagConfig(**rag),
        prompts=prompts,
        policy=policy,
        lora=lora,
        observability=ObservabilityConfig(**observability),
    )
