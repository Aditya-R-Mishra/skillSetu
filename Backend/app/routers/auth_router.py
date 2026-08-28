from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from bson import ObjectId
from app.database import get_database
from app.models.domain import COLLECTION_USERS
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserRegister, db = Depends(get_database)):
    """
    Register a new learner account in the platform.
    Checks for duplicate emails, hashes password, and returns JWT.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
        
    existing_user = await db[COLLECTION_USERS].find_one({"email": user_in.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
        
    new_user_doc = {
        "name": user_in.name,
        "email": user_in.email.lower(),
        "password_hash": hash_password(user_in.password),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db[COLLECTION_USERS].insert_one(new_user_doc)
    user_id_str = str(result.inserted_id)
    
    access_token = create_access_token(data={"sub": user_id_str, "email": user_in.email.lower(), "name": user_in.name})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id_str,
        name=user_in.name,
        email=user_in.email.lower()
    )

@router.post("/login", response_model=Token)
async def login_user(credentials: UserLogin, db = Depends(get_database)):
    """
    Authenticate learner credentials and issue a JWT access token.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
        
    user = await db[COLLECTION_USERS].find_one({"email": credentials.email.lower()})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    user_id_str = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id_str, "email": user["email"], "name": user.get("name", "")})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id_str,
        name=user.get("name", ""),
        email=user["email"]
    )

@router.post("/token", include_in_schema=False)
async def login_for_swagger_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_database)
):
    """
    GAP FIX #1: OAuth2 form-encoded login endpoint required by Swagger UI's
    'Authorize' button (tokenUrl="auth/token"). Frontend should use POST /auth/login
    with a JSON body instead — this route exists only for Swagger compatibility.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    user = await db[COLLECTION_USERS].find_one({"email": form_data.username.lower()})
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id_str = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id_str, "email": user["email"], "name": user.get("name", "")}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Retrieve profile details of currently authenticated learner.
    """
    return UserOut(
        _id=str(current_user.get("_id", "")),
        name=current_user.get("name", "Learner"),
        email=current_user.get("email", ""),
        created_at=current_user.get("created_at", datetime.now(timezone.utc))
    )
