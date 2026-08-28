from datetime import datetime
from fastapi import APIRouter, Depends
from bson import ObjectId
from app.database import get_database
from app.models.domain import COLLECTION_QUIZ_ATTEMPTS
from app.schemas.dashboard import DashboardOut, CompetencySummary
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("", response_model=DashboardOut)
async def get_learner_dashboard(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Retrieve comprehensive competency dashboard analytics for learner.
    Aggregates quiz attempts, identifies strong/moderate/weak domains,
    and returns progress breakdown over time.
    """
    if db is None:
        return DashboardOut(
            total_quizzes_taken=0,
            strong_areas_count=0,
            moderate_areas_count=0,
            weak_areas_count=0,
            competency_breakdown=[],
            recent_attempts=[]
        )

    user_id_obj = ObjectId(str(current_user["_id"]))
    
    # Fetch all attempts sorted by attempted_at desc
    cursor = db[COLLECTION_QUIZ_ATTEMPTS].find({"user_id": user_id_obj}).sort("attempted_at", -1)
    attempts = await cursor.to_list(length=100)

    if not attempts:
        return DashboardOut(
            total_quizzes_taken=0,
            strong_areas_count=0,
            moderate_areas_count=0,
            weak_areas_count=0,
            competency_breakdown=[],
            recent_attempts=[]
        )

    grouped_data = {}
    recent_attempts_list = []

    for att in attempts:
        area = att.get("competency_area", "General Statistical Knowledge")
        score = float(att.get("score_percent", 0.0))
        gap_lvl = att.get("gap_level", "Weak")

        if area not in grouped_data:
            grouped_data[area] = {
                "latest_score": score,
                "latest_gap": gap_lvl,
                "scores": [score],
                "count": 1
            }
        else:
            grouped_data[area]["scores"].append(score)
            grouped_data[area]["count"] += 1

        recent_attempts_list.append({
            "attempt_id": str(att["_id"]),
            "quiz_id": str(att["quiz_id"]),
            "competency_area": area,
            "score_percent": score,
            "gap_level": gap_lvl,
            "attempted_at": att["attempted_at"].isoformat() if isinstance(att["attempted_at"], datetime) else str(att["attempted_at"])
        })

    competency_breakdown = []
    strong_count = 0
    moderate_count = 0
    weak_count = 0

    for area, info in grouped_data.items():
        avg_score = round(sum(info["scores"]) / len(info["scores"]), 2)
        latest_gap = info["latest_gap"]

        if latest_gap == "Strong":
            strong_count += 1
        elif latest_gap == "Moderate":
            moderate_count += 1
        else:
            weak_count += 1

        competency_breakdown.append(CompetencySummary(
            competency_area=area,
            latest_score_percent=info["latest_score"],
            average_score_percent=avg_score,
            gap_level=latest_gap,
            attempts_count=info["count"]
        ))

    return DashboardOut(
        total_quizzes_taken=len(attempts),
        strong_areas_count=strong_count,
        moderate_areas_count=moderate_count,
        weak_areas_count=weak_count,
        competency_breakdown=competency_breakdown,
        recent_attempts=recent_attempts_list[:10]
    )
