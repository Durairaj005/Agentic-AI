from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1)
    job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class ChatQueryResponse(BaseModel):
    reply: str
    intent: str
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    suggested_actions: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class QuestionGenRequest(BaseModel):
    candidate_id: str
    job_id: Optional[str] = None
    focus_area: Optional[str] = None


class OutreachGenRequest(BaseModel):
    candidate_id: str
    job_id: Optional[str] = None
    tone: Optional[str] = "PROFESSIONAL"
