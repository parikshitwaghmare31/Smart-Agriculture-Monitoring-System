"""
Routes for user management (admin only).

  GET /api/v1/users -> list every registered user (farmers and admins),
                        each with a count of devices they own
"""

from fastapi import APIRouter, HTTPException, Depends

from app.models.auth_schemas import UserWithDeviceCount
from app.services.auth_deps import require_admin
from app.config.settings import settings
from app.config.database import get_database

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserWithDeviceCount])
async def list_users(admin: dict = Depends(require_admin)):
    """
    Admin-only: view every registered user (farmer or admin), along with
    how many sensor nodes are currently assigned to them. Read-only for
    now — no role changes or deletion, to avoid accidentally locking out
    the only admin account or orphaning a farmer's devices.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    users = []
    async for user in db[settings.USER_COLLECTION].find():
        device_count = await db[settings.DEVICE_COLLECTION].count_documents(
            {"owner_email": user["email"]}
        )
        users.append(
            UserWithDeviceCount(
                email=user["email"],
                full_name=user["full_name"],
                role=user["role"],
                created_at=user["created_at"],
                device_count=device_count,
            )
        )

    return users
