from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegister(BaseModel):
    """Registration request payload."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password min 6 characters")

class UserLogin(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str

class Token(BaseModel):
    """JWT Token response payload."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str

class UserOut(BaseModel):
    """Public user profile output schema (excludes password hash)."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    name: str
    email: str
    created_at: datetime
