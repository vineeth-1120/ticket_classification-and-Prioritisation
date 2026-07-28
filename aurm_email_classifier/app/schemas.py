from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ClassifyRequest(BaseModel):
    email_id: str
    sender: str
    title: str
    body: str
    received_at: datetime

class ClassifyResponse(BaseModel):
    email_id: str
    classification_id: int
    category: str
    priority: str
    confidence: float
    summary: str
    suggested_action: str
    estimated_response_time_hours: int
    tags: List[str]
    routed_to: str
    sla_deadline: datetime
    status: str
    needs_human_review: bool
    language: str
    feedback: Optional[List["FeedbackData"]] = None

class FeedbackRequest(BaseModel):
    classification_id: int
    corrected_category: Optional[str] = None
    corrected_priority: Optional[str] = None
    notes: Optional[str] = None
    agent_id: str

class FeedbackData(BaseModel):
    id: int
    classification_id: int
    corrected_category: Optional[str]
    corrected_priority: Optional[str]
    notes: Optional[str]
    agent_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str

class StatsResponse(BaseModel):
    total_classified: int
    by_category: dict
    by_priority: dict
    avg_confidence: float
    pending_human_review_count: int
