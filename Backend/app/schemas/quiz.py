from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class MCQQuestionInternal(BaseModel):
    """Full question object stored in DB (includes correct answer & explanation)."""
    question: str
    options: List[str]
    correct_index: int
    explanation: Optional[str] = ""

class MCQQuestionPublic(BaseModel):
    """Sanitized question object returned to learner for taking quiz (scrubbed answers)."""
    question_index: int
    question: str
    options: List[str]

class QuizGenerateResponse(BaseModel):
    """Response after calling Gemini AI to generate quiz."""
    quiz_id: str
    material_id: str
    competency_area: str
    total_questions: int
    created_at: datetime

class QuizTakeOut(BaseModel):
    """Public schema for fetching quiz to attempt."""
    model_config = ConfigDict(populate_by_name=True)

    quiz_id: str = Field(alias="_id")
    material_id: str
    title: str
    competency_area: str
    questions: List[MCQQuestionPublic]

class QuizSubmitRequest(BaseModel):
    """Submission payload containing user selected option indices."""
    answers: List[int] = Field(..., description="List of 0-based selected option indices matching question order")

class QuestionReview(BaseModel):
    """Detailed breakdown of individual question result after submission."""
    question_index: int
    question: str
    options: List[str]
    user_answer_index: int
    correct_index: int
    is_correct: bool
    explanation: Optional[str] = ""

class QuizAttemptOut(BaseModel):
    """Result of quiz attempt after grading."""
    model_config = ConfigDict(populate_by_name=True)

    attempt_id: str = Field(alias="_id")
    quiz_id: str
    competency_area: str
    score_percent: float
    correct_count: int
    total_questions: int
    gap_level: str  # 'Strong' | 'Moderate' | 'Weak'
    question_reviews: Optional[List[QuestionReview]] = []
    attempted_at: datetime
