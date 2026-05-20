"""
services/ml_service.py — ML Inference Service
===============================================
Loads the trained XGBoost model + preprocessor and runs predictions.

DESIGN DECISION — Load models at startup, not per-request:
  Loading a .pkl file from disk takes ~100-500ms.
  If we loaded on every request, a 100-student batch would be very slow.
  Instead, we load once at module import time (when the server starts).
  The loaded objects live in memory for the lifetime of the process.

  Interview Q: "How do you serve ML models efficiently?"
  Answer: "Pre-load model into memory at startup. For high traffic,
           use model servers like TorchServe or Triton, or cache with Redis."

RISK THRESHOLDS:
  risk_score ≥ 0.6  → "High"   (needs immediate intervention)
  risk_score ≥ 0.3  → "Medium" (monitor closely)
  risk_score < 0.3  → "Low"    (no immediate action needed)

  WHY THESE THRESHOLDS?
  We can tune thresholds post-training to optimise recall for the "High" class.
  In a risk prediction system, we prefer false positives (over-alerting) over
  false negatives (missing truly at-risk students).
"""

import logging
import os
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
import shap
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db_models import Student, Prediction
from app.services.shap_service import compute_shap_values, generate_explanation_text

logger = logging.getLogger(__name__)

# ── Load model artifacts at module import time ─────────────────────────────────
# These variables are module-level → loaded once when the server starts.
_model = None
_preprocessor = None
_shap_explainer = None


def _load_artifacts():
    """
    Load model and preprocessor from disk.
    Called lazily on first prediction request.
    """
    global _model, _preprocessor, _shap_explainer

    model_path = os.path.abspath(settings.MODEL_PATH)
    preprocessor_path = os.path.abspath(settings.PREPROCESSOR_PATH)

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found at: {model_path}\n"
            "Please run 'python ml/train.py' first to train and save the model."
        )
    if not os.path.exists(preprocessor_path):
        raise FileNotFoundError(
            f"Preprocessor file not found at: {preprocessor_path}\n"
            "Please run 'python ml/train.py' first."
        )

    logger.info(f"Loading model from: {model_path}")
    _model = joblib.load(model_path)

    logger.info(f"Loading preprocessor from: {preprocessor_path}")
    _preprocessor = joblib.load(preprocessor_path)

    # Create SHAP TreeExplainer for XGBoost
    # TreeExplainer is optimised for tree-based models (exact SHAP values, fast)
    _shap_explainer = shap.TreeExplainer(_model)

    logger.info("✅ ML artifacts loaded successfully.")


def get_model():
    """Returns loaded model, loading from disk if necessary."""
    if _model is None:
        _load_artifacts()
    return _model


def get_preprocessor():
    """Returns loaded preprocessor pipeline."""
    if _preprocessor is None:
        _load_artifacts()
    return _preprocessor


def get_shap_explainer():
    """Returns SHAP TreeExplainer."""
    if _shap_explainer is None:
        _load_artifacts()
    return _shap_explainer


def _score_to_label(score: float) -> str:
    """Convert raw probability to human-readable risk label."""
    if score >= 0.6:
        return "High"
    elif score >= 0.3:
        return "Medium"
    else:
        return "Low"


def run_batch_prediction(
    df: pd.DataFrame,
    db: Session,
    uploaded_by_id: int,
) -> Dict[str, Any]:
    """
    Process a DataFrame of student records:
    1. Save each row as a Student record
    2. Run ML inference on all rows
    3. Save Prediction records with SHAP values
    4. Return summary counts

    Returns dict: {total, high, medium, low, prediction_ids}
    """
    model = get_model()
    preprocessor = get_preprocessor()
    explainer = get_shap_explainer()

    prediction_ids = []
    counts = {"total": len(df), "high": 0, "medium": 0, "low": 0}

    # Preprocess the entire DataFrame at once (vectorised — much faster than row-by-row)
    try:
        X_transformed = preprocessor.transform(df)
    except Exception as e:
        raise ValueError(f"Preprocessing failed: {str(e)}")

    # Get predicted probabilities for all students
    # predict_proba returns [[prob_class_0, prob_class_1], ...]
    # We take column 1 = probability of being at-risk
    risk_scores = model.predict_proba(X_transformed)[:, 1]

    # Compute SHAP values for all students at once (efficient batch computation)
    shap_values_matrix = explainer.shap_values(X_transformed)
    # shap_values_matrix shape: (n_students, n_features)
    # Each row = SHAP contributions for one student

    # Get feature names from the preprocessor for SHAP labeling
    try:
        feature_names = preprocessor.get_feature_names_out()
    except AttributeError:
        # Fallback: use column names from original DataFrame
        feature_names = df.columns.tolist()

    # Process each student row
    for idx, row in df.iterrows():
        # ── Save Student record ───────────────────────────────────────────────
        student = Student(
            student_name=row.get("student_name", f"Student_{idx+1}"),
            uploaded_by_id=uploaded_by_id,
            # Map each CSV column to its DB field
            age=row.get("age"),
            sex=row.get("sex"),
            school=row.get("school"),
            address=row.get("address"),
            famsize=row.get("famsize"),
            Pstatus=row.get("Pstatus"),
            Medu=row.get("Medu"),
            Fedu=row.get("Fedu"),
            Mjob=row.get("Mjob"),
            Fjob=row.get("Fjob"),
            reason=row.get("reason"),
            guardian=row.get("guardian"),
            traveltime=row.get("traveltime"),
            studytime=row.get("studytime"),
            failures=row.get("failures"),
            schoolsup=row.get("schoolsup"),
            famsup=row.get("famsup"),
            paid=row.get("paid"),
            activities=row.get("activities"),
            nursery=row.get("nursery"),
            higher=row.get("higher"),
            internet=row.get("internet"),
            romantic=row.get("romantic"),
            famrel=row.get("famrel"),
            freetime=row.get("freetime"),
            goout=row.get("goout"),
            Dalc=row.get("Dalc"),
            Walc=row.get("Walc"),
            health=row.get("health"),
            absences=row.get("absences"),
            G1=row.get("G1"),
            G2=row.get("G2"),
        )
        db.add(student)
        db.flush()  # flush to get student.id without committing transaction yet

        # ── Compute SHAP for this student ─────────────────────────────────────
        student_shap = shap_values_matrix[idx]  # 1D array of SHAP values
        # Map feature names → SHAP values dict
        shap_dict = {
            str(feature_names[i]): float(student_shap[i])
            for i in range(len(feature_names))
        }

        score = float(risk_scores[idx])
        label = _score_to_label(score)
        explanation_text = generate_explanation_text(shap_dict, label)

        # ── Save Prediction record ────────────────────────────────────────────
        prediction = Prediction(
            student_id=student.id,
            risk_score=score,
            risk_label=label,
            shap_values=shap_dict,
            explanation_text=explanation_text,
            model_version="xgboost_v1",
        )
        db.add(prediction)
        db.flush()  # Get prediction.id

        prediction_ids.append(prediction.id)
        counts[label.lower()] += 1

    # Commit all students + predictions in a single transaction
    # This is atomic — either all succeed or all fail (ACID property)
    db.commit()
    counts["prediction_ids"] = prediction_ids
    logger.info(f"Batch prediction complete: {counts}")
    return counts
