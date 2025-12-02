from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# --- Input Schemas ---


class RunCreate(BaseModel):
    brands: List[str]
    prompts: List[str]
    models: List[str] = ["mock-model"]  # Default to mock
    notes: Optional[str] = None


# --- Output Schemas ---


class BrandRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PromptRead(BaseModel):
    id: int
    text: str

    model_config = ConfigDict(from_attributes=True)


class ResponseBrandMentionRead(BaseModel):
    brand_name: str
    mentioned: bool
    position_index: Optional[int]


class ResponseRead(BaseModel):
    id: int
    prompt_text: str
    model: str
    latency_ms: float
    raw_text: str
    mentions: List[ResponseBrandMentionRead]
    error: Optional[str] = None


class RunRead(BaseModel):
    id: UUID
    created_at: datetime
    status: str
    notes: Optional[str]
    brands: List[BrandRead]
    prompts: List[PromptRead]
    # We might not want to return ALL responses in the list view,
    # but maybe in detail view

    model_config = ConfigDict(from_attributes=True)


class RunDetail(RunRead):
    responses: List[ResponseRead] = []


# --- Summary Schemas ---


class BrandVisibilityMetric(BaseModel):
    brand_name: str
    total_prompts: int
    mentions: int
    visibility_score: float  # percentage


class RunSummary(BaseModel):
    run_id: UUID
    status: str
    total_prompts: int
    total_responses: int
    metrics: List[BrandVisibilityMetric]
