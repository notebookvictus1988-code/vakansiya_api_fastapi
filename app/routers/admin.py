from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import require_roles
from app.models.user import User, UserRole
from app.schemas.auth import RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(user_id: int, payload: RoleUpdate,
                     db: Session = Depends(get_db),
                     admin: User = Depends(require_roles(UserRole.admin))):
    if payload.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Bu endpoint orqali admin roli berilmaydi")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
