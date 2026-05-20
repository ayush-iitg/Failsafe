"""
schemas.py — Pydantic Request/Response Schemas
===============================================
Pydantic schemas define the shape of data coming IN (request body) and
going OUT (response body) through the API.

WHY PYDANTIC SCHEMAS SEPARATE FROM DB MODELS?

  DB Model (SQLAlchemy) = how data is stored in the database
  Schema (Pydantic)     = how data travels over the HTTP API

  This separation (called DTO — Data Transfer Object pattern) means:
  - You control exactly what fields are exposed in the API (e.g., never expose hashed_password)
  - You can have different shapes for "create" vs "read" operations
  - FastAPI auto-generates OpenAPI (Swagger) docs from these schemas

NAMING CONVENTION:
  UserCreate    → incoming data to CREATE a user
  UserResponse  → outgoing data when READING a user
  UserInDB      → includes DB-only fields (like hashed_password) — never sent to client
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    """Data required to register a new faculty/HOD account."""
    email: EmailStr                           # Pydantic validates email format
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)  # Enforce minimum password length
    role: str = Field(default="faculty", pattern="^(faculty|hod)$")  # Only valid roles


class UserResponse(BaseModel):
    """What we send back when a user is fetched — no password field."""
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Allows creating this from a SQLAlchemy model instance


class TokenResponse(BaseModel):
    """JWT token returned after successful login."""
    access_token: str
    token_type: str = "bearer"  # OAuth2 convention

class LoginRequest(BaseModel):
    """Credentials sent to the login endpoint."""
    email: EmailStr
    password: str


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class StudentResponse(BaseModel):
    """Student record as returned by the API."""
    id: int
    student_name: Optional[str]
    age: Optional[int]
    studytime: Optional[int]
    absences: Optional[int]
    failures: Optional[int]
    G1: Optional[float]
    G2: Optional[float]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# PREDICTION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class PredictionResponse(BaseModel):
    """ML model output for a single student."""
    id: int
    student_id: int
    risk_score: float = Field(..., ge=0.0, le=1.0)  # Must be between 0 and 1
    risk_label: str                                   # 'High', 'Medium', 'Low'
    shap_values: Optional[Dict[str, float]]           # {feature_name: shap_value}
    explanation_text: Optional[str]
    model_version: str
    predicted_at: datetime

    class Config:
        from_attributes = True


class StudentWithPrediction(BaseModel):
    """Combined student + latest prediction — used in the dashboard table."""
    student: StudentResponse
    prediction: Optional[PredictionResponse]


# ═══════════════════════════════════════════════════════════════════════════════
# INTERVENTION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class InterventionResponse(BaseModel):
    """Personalised intervention plan for a student."""
    id: int
    prediction_id: int
    actions: List[str]        # ["Attend extra classes", "Counselling referral"]
    priority: str             # 'High', 'Medium', 'Low'
    is_applied: bool
    applied_at: Optional[datetime]
    faculty_notes: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


class InterventionUpdate(BaseModel):
    """Payload when faculty marks an intervention as applied."""
    is_applied: bool
    faculty_notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD / ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    """Aggregated KPI data for the main dashboard cards."""
    total_students: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    high_risk_percentage: float
    interventions_applied: int


class RiskDistribution(BaseModel):
    """Data for the risk distribution pie/bar chart."""
    label: str    # 'High', 'Medium', 'Low'
    count: int
    percentage: float


class UploadResponse(BaseModel):
    """Response after a successful CSV upload + prediction batch."""
    message: str
    students_processed: int
    high_risk: int
    medium_risk: int
    low_risk: int


# ═══════════════════════════════════════════════════════════════════════════════
# EXPLANATION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class SHAPFeature(BaseModel):
    """A single SHAP feature contribution for a student."""
    feature: str        # e.g., "absences"
    value: float        # Actual feature value, e.g., 14
    shap_value: float   # Contribution to prediction, e.g., +0.45 (increases risk)
    direction: str      # 'increases_risk' or 'decreases_risk'


class ExplanationResponse(BaseModel):
    """Full SHAP explanation for a single student."""
    student_id: int
    risk_score: float
    risk_label: str
    explanation_text: str           # "High absences and low study time increased risk."
    top_features: List[SHAPFeature] # Top 5 contributing features
    base_value: float               # Model's average prediction (SHAP baseline)
