from typing import List, Dict
from pydantic import BaseModel

class CompetencySummary(BaseModel):
    competency_area: str
    latest_score_percent: float
    average_score_percent: float
    gap_level: str  # 'Strong' | 'Moderate' | 'Weak'
    attempts_count: int

class DashboardOut(BaseModel):
    total_quizzes_taken: int
    strong_areas_count: int
    moderate_areas_count: int
    weak_areas_count: int
    competency_breakdown: List[CompetencySummary]
    recent_attempts: List[Dict]
