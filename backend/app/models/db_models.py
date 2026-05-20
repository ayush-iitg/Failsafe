"""
db_models.py — SQLAlchemy Database Models (Table Definitions)
=============================================================
Each class here maps directly to one PostgreSQL table.

INTERVIEW CONCEPT — ORM vs Raw SQL:
  ORM (Object Relational Mapper) lets you define tables as Python classes.
  SQLAlchemy translates method calls into SQL queries.
  Benefit: No manual SQL string building, no SQL injection, IDE autocomplete.

TABLE RELATIONSHIPS:
  users ──< predictions  (one faculty user → many predictions)
  students ──< predictions  (one student → many predictions over time)
  predictions ──< interventions  (one prediction → one intervention plan)

SCHEMA OVERVIEW:
  ┌──────────┐     ┌──────────────┐     ┌─────────────────┐     ┌───────────────┐
  │  users   │──<  │   students   │──<  │   predictions   │──<  │ interventions │
  └──────────┘     └──────────────┘     └─────────────────┘     └───────────────┘
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ── Table 1: users ─────────────────────────────────────────────────────────────
class User(Base):
    """
    Faculty and HOD accounts.
    role: 'faculty' can upload + view their own students
          'hod' can view all students across all faculty
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    # Password stored as bcrypt hash — NEVER store plaintext passwords
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="faculty")   # 'faculty' or 'hod'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: one user → many students they uploaded
    students = relationship("Student", back_populates="uploaded_by")


# ── Table 2: students ──────────────────────────────────────────────────────────
class Student(Base):
    """
    Raw student records as uploaded from CSV.
    Stores the original feature values — not preprocessed.
    This is the source of truth for who the student is.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    # Optional student identifier from the institution (e.g., roll number)
    student_name = Column(String(255), nullable=True)
    # Foreign key links student to the faculty who uploaded them
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── UCI Dataset Features (stored as raw values) ──────────────────────────
    school = Column(String(10), nullable=True)
    sex = Column(String(5), nullable=True)
    age = Column(Integer, nullable=True)
    address = Column(String(5), nullable=True)         # 'U' urban / 'R' rural
    famsize = Column(String(5), nullable=True)         # family size
    Pstatus = Column(String(5), nullable=True)         # parent cohabitation
    Medu = Column(Integer, nullable=True)              # mother's education 0-4
    Fedu = Column(Integer, nullable=True)              # father's education 0-4
    Mjob = Column(String(50), nullable=True)
    Fjob = Column(String(50), nullable=True)
    reason = Column(String(50), nullable=True)         # reason for school choice
    guardian = Column(String(50), nullable=True)
    traveltime = Column(Integer, nullable=True)        # 1-4 scale
    studytime = Column(Integer, nullable=True)         # 1-4 scale (weekly study hrs)
    failures = Column(Integer, nullable=True)          # past class failures
    schoolsup = Column(String(5), nullable=True)       # extra educational support
    famsup = Column(String(5), nullable=True)          # family educational support
    paid = Column(String(5), nullable=True)            # extra paid classes
    activities = Column(String(5), nullable=True)      # extracurricular activities
    nursery = Column(String(5), nullable=True)
    higher = Column(String(5), nullable=True)          # wants higher education
    internet = Column(String(5), nullable=True)
    romantic = Column(String(5), nullable=True)
    famrel = Column(Integer, nullable=True)            # family relationship quality 1-5
    freetime = Column(Integer, nullable=True)          # free time after school 1-5
    goout = Column(Integer, nullable=True)             # going out with friends 1-5
    Dalc = Column(Integer, nullable=True)              # workday alcohol 1-5
    Walc = Column(Integer, nullable=True)              # weekend alcohol 1-5
    health = Column(Integer, nullable=True)            # health status 1-5
    absences = Column(Integer, nullable=True)          # number of school absences
    G1 = Column(Float, nullable=True)                  # first period grade
    G2 = Column(Float, nullable=True)                  # second period grade
    # G3 (final grade) intentionally excluded — that's what we're predicting

    # Relationships
    uploaded_by = relationship("User", back_populates="students")
    predictions = relationship("Prediction", back_populates="student")


# ── Table 3: predictions ───────────────────────────────────────────────────────
class Prediction(Base):
    """
    ML model output for each student.
    Stores risk score, risk label, and SHAP explanation as JSON.

    WHY STORE SHAP AS JSON?
      SHAP values are a dictionary {feature: contribution_value}.
      PostgreSQL's JSON column stores this natively — no need for a separate table.
      Tradeoff: can't query inside JSON efficiently; fine for our scale.
    """
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Model outputs
    risk_score = Column(Float, nullable=False)     # Raw probability 0.0 – 1.0
    risk_label = Column(String(20), nullable=False) # 'High', 'Medium', 'Low'

    # SHAP explanation stored as JSON: {"absences": 0.45, "studytime": -0.32, ...}
    shap_values = Column(JSON, nullable=True)
    # Human-readable explanation sentence generated from SHAP
    explanation_text = Column(Text, nullable=True)

    # Model metadata — useful for tracking which model version made this prediction
    model_version = Column(String(50), default="xgboost_v1")

    # Relationships
    student = relationship("Student", back_populates="predictions")
    intervention = relationship("Intervention", back_populates="prediction", uselist=False)


# ── Table 4: interventions ─────────────────────────────────────────────────────
class Intervention(Base):
    """
    Personalised intervention plan generated for a student's prediction.

    uselist=False on the relationship means prediction → ONE intervention (not a list).
    This is a one-to-one relationship at the application level.

    actions is stored as JSON array: ["Attend extra classes", "Counselling referral"]
    """
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False, unique=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # List of recommended actions (stored as JSON array)
    actions = Column(JSON, nullable=False)
    # Priority level of the intervention
    priority = Column(String(20), default="Medium")  # 'High', 'Medium', 'Low'
    # Whether the faculty has acknowledged / applied this intervention
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    faculty_notes = Column(Text, nullable=True)  # Optional notes from faculty

    # Relationship
    prediction = relationship("Prediction", back_populates="intervention")
