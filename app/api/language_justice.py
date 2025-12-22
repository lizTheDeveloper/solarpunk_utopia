"""
Language Justice API Routes

API endpoints for multi-language support and community translation.
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.database.db import get_db
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/api/language-justice", tags=["language-justice"])


# Request/Response Models


class LanguagePreferenceUpdate(BaseModel):
    """Update user language preference"""

    preferred_language: str = Field(..., description="ISO 639-1 language code (en, es, ar, etc.)")


class SupportedLanguageResponse(BaseModel):
    """Supported language information"""

    language_code: str
    language_name: str
    native_name: str
    rtl: bool
    status: str
    completion_percentage: float


class TranslationResponse(BaseModel):
    """Translation response"""

    string_key: str
    source_text: str
    translated_text: str
    language_code: str


class TranslationSuggestionCreate(BaseModel):
    """Create translation suggestion"""

    string_key: str
    language_code: str
    suggested_text: str
    suggestion_notes: Optional[str] = None


class MetricsResponse(BaseModel):
    """Language usage metrics"""

    total_active_users: int
    users_by_language: Dict[str, int]
    non_english_percentage: float
    fully_translated_languages: int
    period_start: str
    period_end: str


# Endpoints


@router.patch("/preferences", response_model=dict)
async def update_language_preference(
    request: LanguagePreferenceUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update user's preferred language"""
    await db.execute(
        "UPDATE users SET preferred_language = ? WHERE id = ?",
        (request.preferred_language, current_user["id"]),
    )
    await db.commit()

    return {"success": True, "language": request.preferred_language}


@router.get("/preferences", response_model=dict)
async def get_language_preference(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get user's preferred language"""
    cursor = await db.execute(
        "SELECT preferred_language, rtl_enabled FROM users WHERE id = ?",
        (current_user["id"],),
    )
    row = await cursor.fetchone()

    if not row:
        return {"preferred_language": "en", "rtl_enabled": False}

    return {
        "preferred_language": row[0] or "en",
        "rtl_enabled": bool(row[1]),
    }


@router.get("/supported", response_model=List[SupportedLanguageResponse])
async def get_supported_languages(db=Depends(get_db)):
    """Get list of supported languages"""
    cursor = await db.execute(
        """
        SELECT language_code, language_name, native_name, rtl, status, completion_percentage
        FROM supported_languages
        ORDER BY completion_percentage DESC, language_name
        """
    )
    rows = await cursor.fetchall()

    return [
        SupportedLanguageResponse(
            language_code=row[0],
            language_name=row[1],
            native_name=row[2],
            rtl=bool(row[3]),
            status=row[4],
            completion_percentage=row[5],
        )
        for row in rows
    ]


@router.post("/suggest", response_model=dict)
async def suggest_translation(
    request: TranslationSuggestionCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Suggest a translation for a string"""
    import uuid
    from datetime import datetime

    # Get string_id from string_key
    cursor = await db.execute(
        "SELECT id FROM translation_strings WHERE string_key = ?",
        (request.string_key,),
    )
    row = await cursor.fetchone()

    if not row:
        return {"success": False, "error": "String not found"}

    string_id = row[0]

    # Create suggestion
    suggestion_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    await db.execute(
        """
        INSERT INTO translation_suggestions (
            id, string_id, language_code, suggested_text,
            suggestion_notes, suggested_by, suggested_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            suggestion_id,
            string_id,
            request.language_code,
            request.suggested_text,
            request.suggestion_notes,
            current_user["id"],
            now,
        ),
    )
    await db.commit()

    return {"success": True, "suggestion_id": suggestion_id}


@router.get("/translations/{language_code}", response_model=Dict[str, str])
async def get_translations_for_language(
    language_code: str,
    db=Depends(get_db),
):
    """Get all translations for a language as key-value pairs"""
    cursor = await db.execute(
        """
        SELECT ts.string_key, t.translated_text
        FROM translations t
        JOIN translation_strings ts ON t.string_id = ts.id
        WHERE t.language_code = ?
        AND t.translation_status IN ('approved', 'reviewed')
        """,
        (language_code,),
    )
    rows = await cursor.fetchall()

    return {row[0]: row[1] for row in rows}


@router.get("/metrics", response_model=MetricsResponse)
async def get_language_metrics(
    days_back: int = 30,
    db=Depends(get_db),
):
    """Get language usage metrics"""
    from datetime import datetime, timedelta
    import json

    period_end = datetime.now(UTC)
    period_start = period_end - timedelta(days=days_back)

    # Total active users
    cursor = await db.execute(
        "SELECT COUNT(*) FROM users WHERE created_at <= ?",
        (period_end.isoformat(),),
    )
    total_active = (await cursor.fetchone())[0]

    # Users by language
    cursor = await db.execute(
        """
        SELECT preferred_language, COUNT(*) as count
        FROM users
        WHERE created_at <= ?
        GROUP BY preferred_language
        """,
        (period_end.isoformat(),),
    )
    rows = await cursor.fetchall()

    users_by_language = {row[0]: row[1] for row in rows if row[0]}

    # Calculate non-English percentage
    non_english_count = sum(
        count for lang, count in users_by_language.items() if lang != "en"
    )
    non_english_percentage = (
        (non_english_count / total_active * 100) if total_active > 0 else 0.0
    )

    # Fully translated languages
    cursor = await db.execute(
        "SELECT COUNT(*) FROM supported_languages WHERE completion_percentage >= 100.0"
    )
    fully_translated = (await cursor.fetchone())[0]

    return MetricsResponse(
        total_active_users=total_active,
        users_by_language=users_by_language,
        non_english_percentage=non_english_percentage,
        fully_translated_languages=fully_translated,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
    )
