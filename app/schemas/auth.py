"""
Auth Schemas — Request/Response models for authentication endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """Registration payload."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = Field(default="student", pattern="^(student|teacher|admin)$")


class UserLoginRequest(BaseModel):
    """Login payload."""
    username: str
    password: str


class TokenRefreshRequest(BaseModel):
    """Refresh-token rotation payload."""
    refresh_token: str


# ── Response Schemas ─────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token pair returned on login/refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
