from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from bson import ObjectId
from app.database import get_database
from app.models.domain import COLLECTION_MATERIALS, COLLECTION_QUIZZES
from app.schemas.material import MaterialCreate, MaterialOut
from app.schemas.quiz import QuizGenerateResponse
from app.dependencies import get_current_user
from app.utils.pdf_extractor import extract_text_from_pdf_bytes
from app.services.gemini_service import generate_mcqs_from_text

router = APIRouter(prefix="/materials", tags=["Learning Materials"])

@router.post("", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def create_material(
    material_in: MaterialCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Upload learning material via pasted text, tagged to a competency area.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
        
    if not material_in.raw_text or not material_in.raw_text.strip():
        raise HTTPException(status_code=400, detail="Learning material text content cannot be empty.")

    user_id_str = str(current_user["_id"])
    material_doc = {
        "user_id": ObjectId(user_id_str),
        "title": material_in.title,
        "competency_area": material_in.competency_area,
        "raw_text": material_in.raw_text,
        "file_type": "text",
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db[COLLECTION_MATERIALS].insert_one(material_doc)
    material_id_str = str(result.inserted_id)
    
    return MaterialOut(
        _id=material_id_str,
        user_id=user_id_str,
        title=material_in.title,
        competency_area=material_in.competency_area,
        raw_text=material_in.raw_text,
        file_type="text",
        created_at=material_doc["created_at"]
    )

@router.post("/upload-pdf", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def upload_pdf_material(
    title: str = Form(...),
    competency_area: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Upload learning material via PDF file. Automatically extracts text content using PyPDF.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    try:
        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    user_id_str = str(current_user["_id"])
    material_doc = {
        "user_id": ObjectId(user_id_str),
        "title": title,
        "competency_area": competency_area,
        "raw_text": extracted_text,
        "file_type": "pdf",
        "created_at": datetime.now(timezone.utc)
    }

    result = await db[COLLECTION_MATERIALS].insert_one(material_doc)
    material_id_str = str(result.inserted_id)

    return MaterialOut(
        _id=material_id_str,
        user_id=user_id_str,
        title=title,
        competency_area=competency_area,
        raw_text=extracted_text,
        file_type="pdf",
        created_at=material_doc["created_at"]
    )

@router.get("", response_model=List[MaterialOut])
async def list_user_materials(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    List all uploaded materials for the current learner.
    """
    if db is None:
        return []
        
    user_id_obj = ObjectId(str(current_user["_id"]))
    cursor = db[COLLECTION_MATERIALS].find({"user_id": user_id_obj}).sort("created_at", -1)
    materials = []
    
    async for doc in cursor:
        materials.append(MaterialOut(
            _id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            title=doc["title"],
            competency_area=doc["competency_area"],
            raw_text=doc["raw_text"],
            file_type=doc.get("file_type", "text"),
            created_at=doc["created_at"]
        ))
        
    return materials

@router.get("/{material_id}", response_model=MaterialOut)
async def get_material_by_id(
    material_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Retrieve single material details by ID.
    Ownership enforced: only the material's author can retrieve it.
    """
    if db is None or not ObjectId.is_valid(material_id):
        raise HTTPException(status_code=404, detail="Material not found")

    # GAP FIX #2: scope query to current user to prevent cross-user data leakage
    user_id_obj = ObjectId(str(current_user["_id"]))
    material = await db[COLLECTION_MATERIALS].find_one({
        "_id": ObjectId(material_id),
        "user_id": user_id_obj
    })
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
        
    return MaterialOut(
        _id=str(material["_id"]),
        user_id=str(material["user_id"]),
        title=material["title"],
        competency_area=material["competency_area"],
        raw_text=material["raw_text"],
        file_type=material.get("file_type", "text"),
        created_at=material["created_at"]
    )

@router.post("/{material_id}/generate-quiz", response_model=QuizGenerateResponse)
async def generate_quiz_for_material(
    material_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Triggers Google Gemini AI service to generate a 5-6 question MCQ assessment
    from the uploaded material text, and stores the quiz in MongoDB.
    """
    if db is None or not ObjectId.is_valid(material_id):
        raise HTTPException(status_code=404, detail="Material not found")

    material = await db[COLLECTION_MATERIALS].find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Generate MCQs using AI service
    mcqs = await generate_mcqs_from_text(
        text=material["raw_text"],
        competency_area=material["competency_area"],
        title=material["title"],
        num_questions=5
    )

    user_id_str = str(current_user["_id"])
    quiz_doc = {
        "material_id": ObjectId(material_id),
        "user_id": ObjectId(user_id_str),
        "title": material["title"],
        "competency_area": material["competency_area"],
        "questions": mcqs,
        "created_at": datetime.now(timezone.utc)
    }

    result = await db[COLLECTION_QUIZZES].insert_one(quiz_doc)
    quiz_id_str = str(result.inserted_id)

    return QuizGenerateResponse(
        quiz_id=quiz_id_str,
        material_id=material_id,
        competency_area=material["competency_area"],
        total_questions=len(mcqs),
        created_at=quiz_doc["created_at"]
    )
