from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    """Schema for incoming analysis queries."""
    filename: str
    query: str

class AnalysisResponse(BaseModel):
    """Schema returned after executing analysis queries."""
    success: bool
    explanation: str
    result: Optional[str] = None
    chart_url: Optional[str] = None   # Full HTTP URL to chart PNG, if generated
    errors: List[str] = []
