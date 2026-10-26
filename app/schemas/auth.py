from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated
from app.models.user import UserRole

Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]

class RegisterRequest(BaseModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)]
    email: EmailStr
    password: Password

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    role: UserRole

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class RoleUpdate(BaseModel):
    role: UserRole
