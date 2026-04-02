from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    user: "UserResponse"
    access_token: str
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str


class MessageResponse(BaseModel):
    message: str


# Avoid circular import
from app.schemas.user import UserResponse  # noqa: E402

AuthResponse.model_rebuild()
