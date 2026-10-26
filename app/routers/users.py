from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_my_profile(user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's safe public profile."""
    return user
