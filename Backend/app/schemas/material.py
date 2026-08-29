from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# ──────────────────────────────────────────────────────────────────────────────
# Constants for content validation
# ──────────────────────────────────────────────────────────────────────────────
MIN_WORDS = 50       # Minimum words required to generate meaningful quiz questions
MAX_WORDS = 15000    # Upper cap to prevent token overflow and abuse


def _validate_text_content(text: str, field_name: str = "Text") -> str:
    """
    Shared text validation logic used by both text-paste and PDF extraction:
    1. Strip whitespace
    2. Reject empty or whitespace-only input
    3. Reject content below MIN_WORDS (too short for quiz generation)
    4. Reject content above MAX_WORDS (too large, risks Gemini token overflow)
    5. Reject content that has no real alphabetic words (pure numbers/symbols)
    """
    cleaned = text.strip()

    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty or contain only whitespace.")

    words = cleaned.split()
    word_count = len(words)

    if word_count < MIN_WORDS:
        raise ValueError(
            f"{field_name} is too short ({word_count} words). "
            f"Please provide at least {MIN_WORDS} words so the AI can generate meaningful quiz questions."
        )

    if word_count > MAX_WORDS:
        raise ValueError(
            f"{field_name} is too large ({word_count} words). "
            f"Please keep content under {MAX_WORDS} words to ensure proper AI processing."
        )

    # Reject content with no real alphabetic words (e.g., pure numbers, symbols, garbage data)
    alpha_words = [w for w in words if any(c.isalpha() for c in w)]
    if len(alpha_words) < (MIN_WORDS // 2):
        raise ValueError(
            f"{field_name} does not appear to contain readable text. "
            "Please ensure the content includes actual words, not just numbers or symbols."
        )

    return cleaned


class MaterialCreate(BaseModel):
    """Material upload payload (text paste)."""
    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Descriptive title for the learning material"
    )
    competency_area: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Target MoSPI statistical competency area (e.g. 'Survey Design')"
    )
    raw_text: str = Field(
        ...,
        description="Pasted learning material text — minimum 50 words required"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Title cannot be empty or contain only whitespace.")
        # Reject titles that are purely numeric or symbolic
        if not any(c.isalpha() for c in cleaned):
            raise ValueError("Title must contain at least some readable letters, not just numbers or symbols.")
        return cleaned

    @field_validator("competency_area")
    @classmethod
    def validate_competency_area(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Competency area cannot be empty.")
        if not any(c.isalpha() for c in cleaned):
            raise ValueError("Competency area must contain readable text.")
        return cleaned

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, v: str) -> str:
        return _validate_text_content(v, field_name="Learning material text")


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

