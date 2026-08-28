from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.database import get_database
from app.models.domain import COLLECTION_QUIZZES, COLLECTION_QUIZ_ATTEMPTS
from app.schemas.quiz import (
    QuizTakeOut,
    MCQQuestionPublic,
    QuizSubmitRequest,
    QuizAttemptOut,
    QuestionReview
)
from app.dependencies import get_current_user
from app.services.competency_service import grade_quiz_attempt

router = APIRouter(prefix="/quizzes", tags=["Quizzes & Assessment"])

@router.get("/{quiz_id}", response_model=QuizTakeOut)
async def get_quiz_for_taking(
    quiz_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Fetch quiz questions for a learner to attempt.
    SECURITY: Answers ('correct_index') and explanations are scrubbed from the response payload.
    """
    if db is None or not ObjectId.is_valid(quiz_id):
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz = await db[COLLECTION_QUIZZES].find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    public_questions = []
    for idx, q in enumerate(quiz.get("questions", [])):
        public_questions.append(MCQQuestionPublic(
            question_index=idx,
            question=q.get("question", ""),
            options=q.get("options", [])
        ))

    return QuizTakeOut(
        _id=str(quiz["_id"]),
        material_id=str(quiz.get("material_id", "")),
        title=quiz.get("title", "Assessment Quiz"),
        competency_area=quiz.get("competency_area", "General Statistical Knowledge"),
        questions=public_questions
    )

@router.post("/{quiz_id}/submit", response_model=QuizAttemptOut)
async def submit_quiz_attempt(
    quiz_id: str,
    submission: QuizSubmitRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Submit learner answers for a quiz.
    Evaluates score, classifies competency gap level (Weak / Moderate / Strong),
    saves the attempt to DB, and returns graded feedback.
    """
    if db is None or not ObjectId.is_valid(quiz_id):
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz = await db[COLLECTION_QUIZZES].find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz_questions = quiz.get("questions", [])
    
    score_percent, correct_count, total_questions, gap_lvl, question_reviews = grade_quiz_attempt(
        user_answers=submission.answers,
        quiz_questions=quiz_questions
    )

    user_id_str = str(current_user["_id"])
    attempt_doc = {
        "user_id": ObjectId(user_id_str),
        "quiz_id": ObjectId(quiz_id),
        "competency_area": quiz.get("competency_area", "General Statistical Knowledge"),
        "score_percent": score_percent,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "gap_level": gap_lvl,
        "user_answers": submission.answers,
        "attempted_at": datetime.now(timezone.utc)
    }

    result = await db[COLLECTION_QUIZ_ATTEMPTS].insert_one(attempt_doc)
    attempt_id_str = str(result.inserted_id)

    formatted_reviews = [
        QuestionReview(
            question_index=r["question_index"],
            question=r["question"],
            options=r["options"],
            user_answer_index=r["user_answer_index"],
            correct_index=r["correct_index"],
            is_correct=r["is_correct"],
            explanation=r["explanation"]
        ) for r in question_reviews
    ]

    return QuizAttemptOut(
        _id=attempt_id_str,
        quiz_id=quiz_id,
        competency_area=quiz.get("competency_area", "General Statistical Knowledge"),
        score_percent=score_percent,
        correct_count=correct_count,
        total_questions=total_questions,
        gap_level=gap_lvl,
        question_reviews=formatted_reviews,
        attempted_at=attempt_doc["attempted_at"]
    )
