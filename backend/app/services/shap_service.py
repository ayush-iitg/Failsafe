"""
services/shap_service.py — SHAP Explanation Formatting
=======================================================
Formats raw SHAP values into structured, human-readable explanations.

WHAT IS SHAP? (Interview-ready explanation)
  SHAP = SHapley Additive exPlanations
  Based on Shapley values from cooperative game theory.

  For each student, SHAP answers:
  "How much did each feature CONTRIBUTE to pushing the prediction
   above or below the average prediction?"

  - Positive SHAP value → feature INCREASES risk prediction
  - Negative SHAP value → feature DECREASES risk prediction
  - Base value → what the model predicts for an average student

  Example: risk_score = base_value + SHAP(absences) + SHAP(studytime) + ...
           0.72        = 0.35       + 0.28          + (-0.05)         + ...

WHY SHAP OVER FEATURE IMPORTANCE?
  - Regular feature importance (gain/permutation) is GLOBAL — same for all students
  - SHAP is LOCAL — explains why THIS specific student was flagged
  - SHAP satisfies mathematical properties: efficiency, symmetry, dummy, additivity
  - More trustworthy because it has game-theoretic foundations

HUMAN-READABLE SENTENCE GENERATION:
  We take the top 2-3 positive SHAP features (those increasing risk) and
  generate a sentence like:
  "High number of absences (14) and low study time (1 hr/week)
   significantly increased this student's failure risk."

  This makes the system usable by non-technical faculty.
"""

from typing import Dict, List
from app.schemas.schemas import ExplanationResponse, SHAPFeature
from app.models.db_models import Prediction

# ── Feature name → human-readable label mapping ────────────────────────────────
# The preprocessor may rename features (e.g., one-hot encoding adds suffixes).
# This maps common feature names to clean display labels.
FEATURE_DISPLAY_NAMES = {
    "absences": "School Absences",
    "studytime": "Weekly Study Hours",
    "failures": "Past Academic Failures",
    "G1": "First Period Grade",
    "G2": "Second Period Grade",
    "goout": "Going Out Frequency",
    "Dalc": "Workday Alcohol Consumption",
    "Walc": "Weekend Alcohol Consumption",
    "health": "Health Status",
    "freetime": "Free Time After School",
    "famrel": "Family Relationship Quality",
    "age": "Student Age",
    "Medu": "Mother's Education Level",
    "Fedu": "Father's Education Level",
    "traveltime": "Travel Time to School",
    "higher_yes": "Aspires to Higher Education",
    "internet_yes": "Has Internet Access",
    "romantic_yes": "In a Romantic Relationship",
    "schoolsup_yes": "Receives School Support",
    "famsup_yes": "Receives Family Support",
}

# ── Feature → actionable intervention phrase ───────────────────────────────────
# Used to generate the explanation sentence
RISK_PHRASES = {
    "absences": "high number of absences",
    "studytime": "low weekly study hours",
    "failures": "history of past failures",
    "G1": "poor first period grade",
    "G2": "poor second period grade",
    "goout": "frequent socialising reducing study time",
    "Dalc": "elevated weekday alcohol consumption",
    "Walc": "elevated weekend alcohol consumption",
    "health": "poor health status",
    "famrel": "difficult family environment",
}


def get_display_name(feature: str) -> str:
    """Return human-readable name for a feature, or clean up the raw name."""
    return FEATURE_DISPLAY_NAMES.get(feature, feature.replace("_", " ").title())


def generate_explanation_text(shap_dict: Dict[str, float], risk_label: str) -> str:
    """
    Generate a human-readable explanation sentence from SHAP values.

    Takes the top 2 features with highest positive SHAP values (most risk-increasing)
    and formats them into a natural language sentence.

    Example output:
    "High school absences and poor second period grade significantly
     increased this student's failure risk."
    """
    if not shap_dict:
        return f"Student is predicted as {risk_label} risk based on their overall profile."

    # Sort features by SHAP value descending (most impactful first)
    sorted_features = sorted(shap_dict.items(), key=lambda x: x[1], reverse=True)

    # Get top 2 risk-increasing features (positive SHAP = increases risk)
    top_risk_features = [(f, v) for f, v in sorted_features if v > 0][:2]

    if not top_risk_features:
        return f"Student is predicted as {risk_label} risk. No single feature dominates."

    # Build phrase list from top features
    phrases = []
    for feature, _ in top_risk_features:
        # Extract base feature name (remove one-hot encoding suffixes like _yes, _no)
        base_feature = feature.split("__")[-1].split("_")[0] if "__" in feature else feature
        phrase = RISK_PHRASES.get(base_feature, f"the value of {get_display_name(feature)}")
        phrases.append(phrase)

    if len(phrases) == 1:
        sentence = f"{phrases[0].capitalize()} significantly increased this student's failure risk."
    else:
        sentence = f"{phrases[0].capitalize()} and {phrases[1]} significantly increased this student's failure risk."

    return sentence


def format_explanation(student_id: int, prediction: Prediction) -> ExplanationResponse:
    """
    Format a Prediction's stored SHAP values into a structured ExplanationResponse.

    Returns top 5 features sorted by absolute SHAP value (most impactful first).
    Absolute value is used because both high positive AND high negative SHAP values
    are important to understand.
    """
    shap_dict: Dict[str, float] = prediction.shap_values or {}

    # Sort by absolute SHAP value — most impactful features first
    sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    top_5 = sorted_features[:5]

    # Format into SHAPFeature objects
    feature_list: List[SHAPFeature] = []
    for feature_name, shap_val in top_5:
        feature_list.append(SHAPFeature(
            feature=get_display_name(feature_name),
            value=0.0,          # Actual value not stored separately; can be enhanced later
            shap_value=round(shap_val, 4),
            direction="increases_risk" if shap_val > 0 else "decreases_risk",
        ))

    return ExplanationResponse(
        student_id=student_id,
        risk_score=prediction.risk_score,
        risk_label=prediction.risk_label,
        explanation_text=prediction.explanation_text or "Explanation not available.",
        top_features=feature_list,
        base_value=0.35,  # Typical base value (average model output); set dynamically post-training
    )
