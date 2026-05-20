"""
routers/explain.py — SHAP Explanation Endpoint
===============================================
Returns SHAP-based explanation for a single student's prediction.

ENDPOINTS:
  GET /api/explain/{student_id}  → Full SHAP explanation with top features

INTERVIEW TALKING POINT:
  "For each prediction, I pre-compute SHAP values at inference time and store
   them as JSON in the predictions table. When the faculty clicks on a student,
   we fetch the stored SHAP values and format them into a human-readable
   explanation — no recomputation needed."
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Student, Prediction
from app.schemas.schemas import ExplanationResponse
from app.services.auth_service import get_current_user
from app.services.shap_service import format_explanation

router = APIRouter(prefix="/api", tags=["Explanations"])


@router.get("/explain/{student_id}", response_model=ExplanationResponse)
def get_explanation(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the SHAP-based explanation for a student's risk prediction.
    Includes top 5 contributing features and a human-readable sentence.
    """
    # Verify student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found."
        )

    # Faculty can only view their own students
    if current_user.role == "faculty" and student.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this student."
        )

    # Get latest prediction
    prediction = (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found for this student. Please run prediction first."
        )

    if not prediction.shap_values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SHAP explanation not available for this prediction."
        )

    # Format SHAP values into structured explanation
    explanation = format_explanation(
        student_id=student_id,
        prediction=prediction,
    )

    return explanation
