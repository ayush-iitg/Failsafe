"""
routers/interventions.py — Intervention Recommendation Endpoints
=================================================================
Returns and manages personalised intervention plans for students.

ENDPOINTS:
  GET   /api/interventions/{student_id}  → Get intervention plan for a student
  PATCH /api/interventions/{id}/apply    → Mark intervention as applied by faculty
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.db_models import Student, Prediction, Intervention
from app.schemas.schemas import InterventionResponse, InterventionUpdate
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/interventions", tags=["Interventions"])


@router.get("/{student_id}", response_model=InterventionResponse)
def get_intervention(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the personalised intervention plan for a student.
    The plan is auto-generated when CSV is uploaded.
    """
    # Verify student exists and access is permitted
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if current_user.role == "faculty" and student.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Get latest prediction → intervention
    prediction = (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )
    if not prediction:
        raise HTTPException(status_code=404, detail="No prediction found for this student.")

    intervention = (
        db.query(Intervention)
        .filter(Intervention.prediction_id == prediction.id)
        .first()
    )
    if not intervention:
        raise HTTPException(
            status_code=404,
            detail="No intervention plan found. Student may be low risk."
        )

    return intervention


@router.patch("/{intervention_id}/apply", response_model=InterventionResponse)
def mark_intervention_applied(
    intervention_id: int,
    update_data: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Faculty marks an intervention as applied and optionally adds notes.
    This tracks progress for the HOD dashboard.
    """
    intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found.")

    intervention.is_applied = update_data.is_applied
    intervention.faculty_notes = update_data.faculty_notes
    if update_data.is_applied:
        intervention.applied_at = datetime.utcnow()

    db.commit()
    db.refresh(intervention)
    return intervention
