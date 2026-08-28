from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class MaterialCreate(BaseModel):
    """Material upload payload (text paste)."""
    title: str = Field(..., min_length=3, max_length=150, description="Title of learning material")
    competency_area: str = Field(..., min_length=2, max_length=100, description="Target statistical competency area")
    raw_text: Optional[str] = Field(None, description="Pasted raw text content")

class MaterialOut(BaseModel):
    """Material output response schema."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    user_id: str
    title: str
    competency_area: str
    raw_text: str
    file_type: str = "text"  # 'text' or 'pdf'
    created_at: datetime
