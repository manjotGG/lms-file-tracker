from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import database

load_dotenv()

router = APIRouter()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Pydantic schemas
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class StudentLoginRequest(BaseModel):
    student_name: str
    student_urn: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

# Helper functions
def create_token(data: dict, expires_delta: timedelta = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(authorization: str = None):
    """Get current user from token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        return verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )

# Auth endpoints
@router.post("/admin/login", response_model=TokenResponse)
def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_token({"role": "admin"})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role="admin"
    )

@router.post("/student/login", response_model=TokenResponse)
def student_login(request: StudentLoginRequest):
    """Student login endpoint"""
    student_name = request.student_name.strip().lower()
    student_urn = request.student_urn.strip()
    
    if not student_name or not student_urn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student name and URN required"
        )
    
    token = create_token({
        "role": "student",
        "student_name": student_name,
        "student_urn": student_urn
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role="student"
    )

@router.get("/verify")
def verify_auth(authorization: str = None):
    """Verify token validity"""
    user = get_current_user(authorization)
    return {"status": "valid", "user": user}
