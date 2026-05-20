"""
services/intervention_service.py — Rule-Based Intervention Engine
==================================================================
Generates personalised intervention plans based on SHAP-identified risk factors.

DESIGN PHILOSOPHY:
  This is a SIMPLE rule-based system — NOT a recommendation engine.
  Rules are written by domain experts (education specialists) and map
  specific risk factors → specific actions.

  WHY RULE-BASED AND NOT ML-BASED?
  - Transparent: faculty can understand and trust the recommendations
  - Maintainable: domain experts can update rules without retraining
  - Reliable: no risk of a model recommending inappropriate interventions
  - Explainable: "Student has 14 absences → attendance mentoring" is clear

  Interview Q: "Why didn't you use a recommendation engine here?"
  Answer: "In high-stakes domains like education, rule-based systems are preferred
           for intervention recommendations because they're transparent, auditable,
           and don't require labelled intervention outcome data to train."

RULE STRUCTURE:
  Each rule checks whether a SHAP feature is in the top risk contributors.
  If the feature's SHAP value exceeds a threshold, its intervention is added.

  Multiple rules can fire for one student → they receive a combined plan.
  Priority is set to "High" if risk_label is High, else "Medium".
"""

import logging
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models.db_models import Prediction, Intervention

logger = logging.getLogger(__name__)

# ── Intervention Rules ─────────────────────────────────────────────────────────
# Format: {feature_keyword: (shap_threshold, intervention_text)}
# If a feature's SHAP value > threshold, add the intervention.
#
# SHAP threshold of 0.05 means: "this feature contributes meaningfully to risk"
# (avoids noise from near-zero SHAP values)

INTERVENTION_RULES = [
    {
        "feature_keywords": ["absences"],
        "shap_threshold": 0.05,
        "action": "Schedule weekly attendance check-ins with the student.",
        "category": "attendance",
    },
    {
        "feature_keywords": ["absences"],
        "shap_threshold": 0.15,  # Higher threshold → more severe intervention
        "action": "Issue formal attendance warning and notify parents/guardian.",
        "category": "attendance",
    },
    {
        "feature_keywords": ["studytime"],
        "shap_threshold": 0.05,
        "action": "Connect student with a peer study group or study buddy program.",
        "category": "study_support",
    },
    {
        "feature_keywords": ["studytime", "failures"],
        "shap_threshold": 0.08,
        "action": "Assign a faculty mentor for structured weekly study planning sessions.",
        "category": "study_support",
    },
    {
        "feature_keywords": ["failures"],
        "shap_threshold": 0.05,
        "action": "Enrol student in subject-specific remedial/extra classes.",
        "category": "academic_support",
    },
    {
        "feature_keywords": ["G1", "G2"],
        "shap_threshold": 0.05,
        "action": "Review previous exam papers with student; identify specific weak topics.",
        "category": "academic_support",
    },
    {
        "feature_keywords": ["goout", "Dalc", "Walc", "romantic"],
        "shap_threshold": 0.05,
        "action": "Refer student to counsellor for a lifestyle and time-management discussion.",
        "category": "counselling",
    },
    {
        "feature_keywords": ["health"],
        "shap_threshold": 0.05,
        "action": "Refer student to campus health services for a well-being check.",
        "category": "health",
    },
    {
        "feature_keywords": ["famrel", "famsup"],
        "shap_threshold": 0.05,
        "action": "Arrange a parent-teacher meeting to discuss home environment support.",
        "category": "family_support",
    },
    {
        "feature_keywords": ["higher", "internet"],
        "shap_threshold": 0.05,
        "action": "Provide motivational counselling on career paths and educational goals.",
        "category": "motivation",
    },
]


def _get_triggered_interventions(shap_dict: Dict[str, float]) -> List[str]:
    """
    Apply all intervention rules against a student's SHAP values.
    Returns list of triggered intervention action strings.

    Rules fire based on:
    1. Whether the feature keyword appears in any SHAP feature name
    2. Whether the SHAP value exceeds the rule's threshold
    """
    triggered_actions = []
    seen_actions = set()  # Prevent duplicate actions

    for rule in INTERVENTION_RULES:
        for feature_key in rule["feature_keywords"]:
            # Find matching SHAP features (handles preprocessed feature names)
            matching_shap = {
                k: v for k, v in shap_dict.items()
                if feature_key.lower() in k.lower() and v > rule["shap_threshold"]
            }

            if matching_shap:
                action = rule["action"]
                if action not in seen_actions:
                    triggered_actions.append(action)
                    seen_actions.add(action)
                break  # Avoid adding same action for multiple matching features

    return triggered_actions


def generate_intervention(
    db: Session,
    prediction: Prediction,
) -> Intervention:
    """
    Generate and save an intervention plan for a single prediction.
    Only creates interventions for High and Medium risk students.
    """
    if prediction.risk_label == "Low":
        # Low-risk students don't need intervention plans
        return None

    shap_dict = prediction.shap_values or {}
    actions = _get_triggered_interventions(shap_dict)

    # Fallback: if no specific rules fired, add a generic action
    if not actions:
        actions = ["Monitor student progress closely over the next 2 weeks."]

    # Always add a check-in action for high-risk students
    if prediction.risk_label == "High":
        actions.append("Schedule an urgent one-on-one meeting with the student.")

    # Priority mirrors risk label
    priority = prediction.risk_label  # "High" or "Medium"

    intervention = Intervention(
        prediction_id=prediction.id,
        actions=actions,
        priority=priority,
        is_applied=False,
    )
    db.add(intervention)
    return intervention


def generate_interventions_for_batch(
    db: Session,
    prediction_ids: List[int],
) -> None:
    """
    Generate intervention plans for a batch of predictions.
    Called after CSV upload completes.
    """
    predictions = (
        db.query(Prediction)
        .filter(Prediction.id.in_(prediction_ids))
        .filter(Prediction.risk_label.in_(["High", "Medium"]))
        .all()
    )

    for prediction in predictions:
        generate_intervention(db=db, prediction=prediction)

    db.commit()
    logger.info(f"Generated interventions for {len(predictions)} at-risk students.")
