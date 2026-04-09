"""
FastAPI Dependencies
====================
Shared dependency injection functions for DB sessions,
authentication, and role-based access control.
"""

from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services import auth_service


# ── Security Scheme ──────────────────────────────────────────

security = HTTPBearer()


# ── Database Dependency ──────────────────────────────────────

def get_db():
    """Yield a database session, auto-close on request end."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Authentication Dependency ────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT bearer token and return the authenticated user.
    Raises HTTP 401 if the token is invalid or the user doesn't exist.
    """
    token = credentials.credentials
    payload = auth_service.decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — use an access token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = auth_service.get_user_by_id(db, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return user


# ── RBAC Dependency Factory ──────────────────────────────────

def require_role(allowed_roles: List[UserRole]):
    """
    Factory that returns a dependency enforcing role-based access.

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role([UserRole.ADMIN]))])
    """
    def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return _role_checker
