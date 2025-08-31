"""Pydantic schemas for request/response models."""
from pydantic import BaseModel, Field

from .models import (
    UploadRequest,
    UploadResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeFinding,
    Region,
    ChatRequest,
    ChatResponse,
    EvaluateRequest,
    EvaluateResponse,
    EvaluationScore,
    ModelSuggestion,
)


class LLMChatResponse(BaseModel):
    """Structured output from a chat generation."""

    answer: str
    citations: list[str] = Field(default_factory=list)


class StructuredError(BaseModel):
    """Error payload returned to clients when parsing fails."""

    error: str


class AgentAnswer(BaseModel):
    """Structured answer returned from the LangChain agent."""

    answer: str


__all__ = [
    "UploadRequest",
    "UploadResponse",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "AnalyzeFinding",
    "Region",
    "ChatRequest",
    "ChatResponse",
    "EvaluateRequest",
    "EvaluateResponse",
    "EvaluationScore",
    "ModelSuggestion",
    "LLMChatResponse",
    "StructuredError",
    "AgentAnswer",
]
