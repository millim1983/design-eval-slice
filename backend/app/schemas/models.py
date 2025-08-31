from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel
import datetime


class UploadRequest(BaseModel):
    title: str
    author_id: str
    asset_url: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class UploadResponse(BaseModel):
    submission_id: str
    created_at: datetime.datetime


class AnalyzeRequest(BaseModel):
    submission_id: str


class Region(BaseModel):
    x: float
    y: float
    w: float
    h: float


class AnalyzeFinding(BaseModel):
    region: Region
    label: str
    confidence: float
    explanation: str
    citations: List[str] = []


class AnalyzeResponse(BaseModel):
    findings: List[AnalyzeFinding]
    model_version: str
    prompt_snapshot: str


class ChatRequest(BaseModel):
    submission_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[str] = []
    model_version: str
    prompt_snapshot: str


class EvaluationScore(BaseModel):
    criteria_id: str
    score: float
    reason: Optional[str] = None
    citation_ids: List[str] = []
    checks: Optional[dict[str, Any]] = None


class ModelSuggestion(BaseModel):
    criteria_id: Optional[str] = None
    suggested_score: Optional[float] = None
    explanation: Optional[str] = None
    citation_ids: List[str] = []


class EvaluateRequest(BaseModel):
    submission_id: str
    judge_id: str
    rubric_version: str
    scores: List[EvaluationScore]
    model_suggestions: List[ModelSuggestion] = []
    submitted_at: Optional[datetime.datetime] = None


class EvaluateResponse(BaseModel):
    ok: bool
