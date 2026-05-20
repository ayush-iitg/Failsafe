"""
routers/auth.py — Authentication Endpoints
==========================================
Handles user registration, login, and token validation.

ENDPOINTS:
  POST /api/auth/register  → Create a new faculty/HOD account
  POST /api/auth/login     → Returns JWT access token
  GET  /api/auth/me        → Returns current logged-in user's profile

JWT FLOW (interview explanation):
  1. User sends email + password to /login
  2. We verify password against bcrypt hash in DB
  3. We create a JWT signed with SECRET_KEY → send to client
  4. Client stores JWT in localStorage
  5. On every subsequent request, client sends JWT in Authorization header:
     Authorization: Bearer <token>
  6. Our get_current_user() dependency decodes and validates the JWT
  7. If valid → request proceeds. If invalid/expired → 401 Unauthorized

WHY JWT OVER SESSIONS?
  - Sessions store state on the server (needs DB/Redis lookup per request)
  - JWT is stateless — the token itself contains the user info
  - Better for APIs consumed by frontend SPA (React)
  - Tradeoff: can't invalidate a JWT before it expires (need a blacklist for logout)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import UserCreate, UserResponse, TokenResponse, LoginRequest
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new faculty or HOD account.
    Returns the created user (without password).
    """
    return create_user(db=db, user_data=user_data)


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    Client should store this token and send it in the Authorization header.
    """
    user = authenticate_user(db=db, email=credentials.email, password=credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Requires valid JWT in Authorization header.
    """
    return current_user
