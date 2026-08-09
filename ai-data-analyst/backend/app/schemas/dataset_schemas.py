from pydantic import BaseModel
from typing import Dict, Any

class UploadResponse(BaseModel):
    """Schema returned after a successful dataset upload and profiling."""
    filename: str
    total_rows: int
    total_columns: int
    profile: Dict[str, Any]
