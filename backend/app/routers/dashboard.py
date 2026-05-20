"""
routers/dashboard.py — Dashboard Analytics Endpoints
=====================================================
Aggregates data for the faculty/HOD dashboard KPI cards and charts.

ENDPOINTS:
  GET /api/dashboard/stats        → KPI card numbers (total, high/medium/low risk)
  GET /api/dashboard/students     → Paginated student list with predictions
  GET /api/dashboard/risk-distribution → Data for risk breakdown chart
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.db_models import Student, Prediction, Intervention
from app.schemas.schemas import DashboardStats, RiskDistribution, StudentWithPrediction
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns KPI card data for the dashboard:
    - Total students uploaded by this faculty
    - Count of High / Medium / Low risk students
    - Percentage at high risk
    - Number of interventions applied
    """
    # HOD sees all students; faculty sees only their own uploads
    base_query = db.query(Student)
    if current_user.role == "faculty":
        base_query = base_query.filter(Student.uploaded_by_id == current_user.id)

    total = base_query.count()

    # Join students → latest prediction to get risk labels
    # Using a subquery to get only the most recent prediction per student
    def count_risk(label: str) -> int:
        return (
            db.query(Prediction)
            .join(Student, Prediction.student_id == Student.id)
            .filter(Prediction.risk_label == label)
            .filter(
                Student.uploaded_by_id == current_user.id
                if current_user.role == "faculty"
                else True
            )
            .count()
        )

    high = count_risk("High")
    medium = count_risk("Medium")
    low = count_risk("Low")

    interventions_applied = (
        db.query(Intervention)
        .filter(Intervention.is_applied == True)
        .count()
    )

    return DashboardStats(
        total_students=total,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        high_risk_percentage=round((high / total * 100) if total > 0 else 0, 1),
        interventions_applied=interventions_applied,
    )


@router.get("/risk-distribution", response_model=List[RiskDistribution])
def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Returns data for the risk breakdown pie/bar chart."""
    total_query = db.query(func.count(Prediction.id))
    if current_user.role == "faculty":
        total_query = total_query.join(Student).filter(
            Student.uploaded_by_id == current_user.id
        )
    total = total_query.scalar() or 0

    distribution = []
    for label in ["High", "Medium", "Low"]:
        q = db.query(func.count(Prediction.id)).filter(Prediction.risk_label == label)
        if current_user.role == "faculty":
            q = q.join(Student).filter(Student.uploaded_by_id == current_user.id)
        count = q.scalar() or 0
        distribution.append(RiskDistribution(
            label=label,
            count=count,
            percentage=round((count / total * 100) if total > 0 else 0, 1),
        ))

    return distribution


@router.get("/students")
def get_students_list(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    risk_filter: str = Query(default=None, pattern="^(High|Medium|Low)$"),
):
    """
    Returns paginated student list with their latest prediction.
    Supports filtering by risk label.
    """
    offset = (page - 1) * page_size

    query = db.query(Student)
    if current_user.role == "faculty":
        query = query.filter(Student.uploaded_by_id == current_user.id)

    if risk_filter:
        query = query.join(Prediction).filter(Prediction.risk_label == risk_filter)

    students = query.offset(offset).limit(page_size).all()
    total = query.count()

    result = []
    for student in students:
        latest_pred = (
            db.query(Prediction)
            .filter(Prediction.student_id == student.id)
            .order_by(Prediction.predicted_at.desc())
            .first()
        )
        result.append({
            "student": student,
            "prediction": latest_pred,
        })

    return {
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }
