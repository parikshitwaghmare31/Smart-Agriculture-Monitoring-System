"""
FastAPI dependencies for pulling the current authenticated user off the
request's JWT bearer token, and for enforcing admin-only access.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config.settings import settings
from app.config.database import get_database
from app.services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    user = await db[settings.USER_COLLECTION].find_one({"email": payload["sub"]})
    if user is None:
        raise credentials_exception

    return user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires administrator privileges",
        )
    return current_user


async def get_allowed_device_ids(current_user: dict, db) -> "list[str] | None":
    """
    Returns None for admins (meaning: no restriction, they can see everything),
    or the specific list of device_ids a farmer owns (meaning: query results
    must be restricted to just these devices).
    """
    if current_user.get("role") == "admin":
        return None

    cursor = db[settings.DEVICE_COLLECTION].find({"owner_email": current_user["email"]})
    return [d["device_id"] async for d in cursor]
