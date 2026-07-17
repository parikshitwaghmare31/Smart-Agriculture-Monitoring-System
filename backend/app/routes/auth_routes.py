"""
Routes for authentication.

  POST /api/v1/auth/register -> self-service farmer registration
  POST /api/v1/auth/login    -> returns a JWT bearer token
  GET  /api/v1/auth/me       -> current authenticated user's profile
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.models.auth_schemas import UserRegister, UserOut, Token
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.services.auth_deps import get_current_user
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserRegister):
    """
    Public self-service registration for farmers. Admin accounts are never
    created through this endpoint — they're bootstrapped on server startup
    from ADMIN_BOOTSTRAP_EMAIL/PASSWORD, or created by an existing admin
    directly in the database.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    existing = await db[settings.USER_COLLECTION].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user_doc = {
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hash_password(payload.password),
        "role": "farmer",
        "created_at": datetime.now(timezone.utc),
    }
    await db[settings.USER_COLLECTION].insert_one(user_doc)
    app_logger.info(f"New farmer account registered: {payload.email}")

    return UserOut(**user_doc)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Standard OAuth2 password flow. `form_data.username` is the user's email
    (OAuth2PasswordRequestForm always calls the identifier field "username").
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    user = await db[settings.USER_COLLECTION].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(subject_email=user["email"], role=user["role"])
    app_logger.info(f"User logged in: {user['email']} ({user['role']})")

    return Token(access_token=token, user=UserOut(**user))


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)
