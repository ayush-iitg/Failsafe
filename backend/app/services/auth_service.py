"""
services/auth_service.py — Authentication Business Logic
=========================================================
Handles password hashing, JWT creation/validation, and user operations.

SECURITY CONCEPTS:
  - Passwords are NEVER stored in plaintext. We use bcrypt, which:
    1. Adds a random "salt" to each password → same password hashes differently each time
    2. Is intentionally slow (cost factor) → brute force attacks take much longer
    3. Is the industry standard for password storage

  - JWT (JSON Web Token) structure: header.payload.signature
    payload contains: {"sub": "user_id", "role": "faculty", "exp": timestamp}
    signature is HMAC-SHA256 of header+payload using SECRET_KEY
    → If anyone tampers with the payload, signature verification fails → 401

INTERVIEW Q: "How would you handle JWT logout?"
  ANSWER: JWTs can't be truly invalidated before expiry. Options:
  1. Short expiry (15 min) + refresh tokens
  2. Maintain a token blacklist in Redis (add token to blacklist on logout)
  3. Use sessions instead (simpler but stateful)
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.db_models import User
from app.schemas.schemas import UserCreate

# ── Password hashing context ───────────────────────────────────────────────────
# bcrypt is the recommended scheme. deprecated="auto" upgrades old hashes automatically.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Bearer token extractor (reads Authorization: Bearer <token> header) ────────
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.
    data should include: {"sub": user_id_str, "role": role_str}
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # Add expiry claim

    # Sign the token with our secret key
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises HTTPException if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing user identifier.",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user in the database.
    Checks for duplicate email before creating.
    """
    # Check if email already registered
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # Refresh to get the auto-generated id from DB
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verify email + password combination.
    Returns User if valid, None if invalid.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — extracts and validates JWT from request header.
    Use as: current_user = Depends(get_current_user)

    This is injected into every protected route. If JWT is invalid → 401.
    """
    payload = decode_token(credentials.credentials)
    user_id = int(payload.get("sub"))

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )
    return user
