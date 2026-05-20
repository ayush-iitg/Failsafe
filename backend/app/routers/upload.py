"""
routers/upload.py — CSV Upload Endpoint
========================================
Faculty upload a CSV file containing student data.
The backend parses it, saves students to DB, and runs predictions.

ENDPOINT:
  POST /api/upload  → multipart/form-data with CSV file

FLOW:
  1. Receive CSV file via multipart upload
  2. Parse with pandas — validate required columns exist
  3. Save each row as a Student record in PostgreSQL
  4. Run ML inference (preprocessor + XGBoost) on all rows
  5. Save Prediction records for each student
  6. Generate and save Intervention plans for high/medium risk students
  7. Return summary: how many students processed + risk breakdown

ERROR HANDLING:
  - Missing required columns → 400 Bad Request with clear message
  - Empty CSV → 400 Bad Request
  - CSV parsing error → 400 Bad Request
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
import pandas as pd
import io
import logging

from app.database import get_db
from app.schemas.schemas import UploadResponse
from app.services.auth_service import get_current_user
from app.services.ml_service import run_batch_prediction
from app.services.intervention_service import generate_interventions_for_batch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Upload"])

# Required columns that must exist in the uploaded CSV
REQUIRED_COLUMNS = [
    "studytime", "failures", "absences", "G1", "G2",
    "higher", "internet", "schoolsup", "famsup", "paid",
    "activities", "romantic", "goout", "Dalc", "Walc",
    "health", "famrel", "freetime", "age", "Medu", "Fedu"
]


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload a CSV of student data.
    Triggers ML prediction and intervention generation for all students.
    """
    # ── Validate file type ─────────────────────────────────────────────────────
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted."
        )

    # ── Read file contents ─────────────────────────────────────────────────────
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV file: {str(e)}"
        )

    # ── Validate not empty ─────────────────────────────────────────────────────
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV is empty."
        )

    # ── Validate required columns ──────────────────────────────────────────────
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required columns: {missing_cols}"
        )

    logger.info(f"User {current_user.id} uploading {len(df)} students.")

    # ── Run batch prediction and save to DB ────────────────────────────────────
    result = run_batch_prediction(
        df=df,
        db=db,
        uploaded_by_id=current_user.id
    )

    # ── Generate interventions for at-risk students ────────────────────────────
    generate_interventions_for_batch(db=db, prediction_ids=result["prediction_ids"])

    return UploadResponse(
        message="Upload successful. Predictions generated.",
        students_processed=result["total"],
        high_risk=result["high"],
        medium_risk=result["medium"],
        low_risk=result["low"],
    )
