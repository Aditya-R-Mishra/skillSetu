from typing import List, Optional
from pydantic import BaseModel

class CourseCatalogItem(BaseModel):
    competency_area: str
    igot_course_code: str
    course_title: str
    description: str
    duration: Optional[str] = "4 Hours"
    difficulty: Optional[str] = "Intermediate"

class RecommendationItem(BaseModel):
    competency_area: str
    gap_level: str  # 'Weak' | 'Moderate'
    latest_score_percent: float
    recommended_course: Optional[CourseCatalogItem] = None

class IGOTSyncResponse(BaseModel):
    status: str = "synced"
    competency_area: str
    igot_course_code: str
    course_title: str
    message: str
    timestamp: str
