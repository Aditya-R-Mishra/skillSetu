from typing import List
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.database import get_database, MOCK_COURSE_CATALOG
from app.models.domain import COLLECTION_QUIZ_ATTEMPTS, COLLECTION_COURSE_CATALOG
from app.schemas.recommendation import RecommendationItem, CourseCatalogItem, IGOTSyncResponse
from app.dependencies import get_current_user
from app.services.igot_adapter import sync_with_igot_karmayogi

router = APIRouter(prefix="/recommendations", tags=["Recommendations & iGOT Integration"])

@router.get("", response_model=List[RecommendationItem])
async def get_personalized_recommendations(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Generate targeted learning module recommendations for competency areas
    where learner gap level is identified as 'Weak' or 'Moderate'.
    """
    if db is None:
        return []

    user_id_obj = ObjectId(str(current_user["_id"]))

    # Aggregate latest attempt per competency area
    pipeline = [
        {"$match": {"user_id": user_id_obj}},
        {"$sort": {"attempted_at": -1}},
        {
            "$group": {
                "_id": "$competency_area",
                "latest_score": {"$first": "$score_percent"},
                "latest_gap": {"$first": "$gap_level"}
            }
        }
    ]

    cursor = db[COLLECTION_QUIZ_ATTEMPTS].aggregate(pipeline)
    latest_gaps = await cursor.to_list(length=50)

    recommendations = []

    for item in latest_gaps:
        area = item["_id"]
        gap_lvl = item["latest_gap"]
        score = float(item["latest_score"])

        # Recommend modules for Weak or Moderate areas
        if gap_lvl in ["Weak", "Moderate"]:
            # Query course catalog
            course_doc = await db[COLLECTION_COURSE_CATALOG].find_one({"competency_area": area})
            
            if not course_doc:
                # Fallback fuzzy match or default catalog item
                matched = next((c for c in MOCK_COURSE_CATALOG if c["competency_area"].lower() in area.lower() or area.lower() in c["competency_area"].lower()), None)
                if matched:
                    catalog_item = CourseCatalogItem(**matched)
                else:
                    code_prefix = area[:3].upper() if len(area) >= 3 else "GEN"
                    catalog_item = CourseCatalogItem(
                        competency_area=area,
                        igot_course_code=f"IGOT-{code_prefix}-101",
                        course_title=f"IGOT-{code_prefix}-101: Essential {area} Refresher",
                        description=f"Targeted competency strengthening module for MoSPI officials in {area}.",
                        duration="3.5 Hours",
                        difficulty="Intermediate"
                    )
            else:
                catalog_item = CourseCatalogItem(
                    competency_area=course_doc.get("competency_area", area),
                    igot_course_code=course_doc.get("igot_course_code", f"IGOT-{area[:3].upper()}-101"),
                    course_title=course_doc.get("course_title", f"IGOT {area} Core Course"),
                    description=course_doc.get("description", f"Capacity building module for {area}"),
                    duration=course_doc.get("duration", "4 Hours"),
                    difficulty=course_doc.get("difficulty", "Intermediate")
                )

            recommendations.append(RecommendationItem(
                competency_area=area,
                gap_level=gap_lvl,
                latest_score_percent=score,
                recommended_course=catalog_item
            ))

    return recommendations

@router.post("/{competency_area}/sync-igot", response_model=IGOTSyncResponse)
async def sync_competency_with_igot(
    competency_area: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Simulated adapter call for syncing identified competency gap with iGOT Karmayogi portal.
    Demonstrates how real iGOT course mapping occurs in production.
    """
    user_id_str = str(current_user["_id"])
    result = sync_with_igot_karmayogi(competency_area, user_id_str)
    return IGOTSyncResponse(**result)
