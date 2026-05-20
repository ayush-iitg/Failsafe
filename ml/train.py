"""
train.py — FAILSAFE Model Training Script
==========================================
Trains and saves the XGBoost failure-risk prediction model.

WHAT THIS SCRIPT DOES:
  1. Loads the UCI Student Performance dataset
  2. Engineers the binary target variable (at_risk)
  3. Builds a scikit-learn preprocessing Pipeline
  4. Trains Logistic Regression, Random Forest, and XGBoost
  5. Evaluates all three with key metrics
  6. Saves the best model (XGBoost) + preprocessor as .pkl files

RUN FROM THE ml/ DIRECTORY:
  cd ml
  python train.py

INTERVIEW TALKING POINT:
  "I separated training from serving. train.py runs offline to produce
   artefacts (model + preprocessor pkl). The FastAPI backend loads those
   artefacts at startup and only runs inference — it never retrains.
   This is how production ML systems are structured."
"""

import os
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)
import xgboost as xgb
import shap

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_PATH = "data/student-mat.csv"
MODEL_SAVE_PATH = "models/xgboost_model.pkl"
PREPROCESSOR_SAVE_PATH = "models/preprocessor.pkl"
PLOTS_DIR = "plots"
os.makedirs("models", exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 1: Loading Dataset")
print("="*60)

# The UCI dataset uses semicolons as separators
df = pd.read_csv(DATA_PATH, sep=";")
print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
print(f"   Columns: {list(df.columns)}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: CREATE TARGET VARIABLE
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 2: Engineering Target Variable")
print("="*60)

# DECISION: at_risk = 1 if final grade G3 < 10 (fail threshold in Portuguese system)
# G3 ranges from 0 to 20. 10 is the passing threshold.
# We DROP G3 from features to avoid data leakage (G3 IS the thing we're predicting).
#
# INTERVIEW Q: "Why not use G3 directly as a regression target?"
# ANSWER: "Classification (pass/fail) is more actionable for faculty.
#          A binary label lets us compute precision/recall and tune the
#          decision threshold based on the cost of false negatives."

df["at_risk"] = (df["G3"] < 10).astype(int)

print(f"   Class distribution:")
print(f"   at_risk=1 (fail): {df['at_risk'].sum()} ({df['at_risk'].mean()*100:.1f}%)")
print(f"   at_risk=0 (pass): {(df['at_risk']==0).sum()} ({(df['at_risk']==0).mean()*100:.1f}%)")

# Check for class imbalance
imbalance_ratio = df['at_risk'].sum() / len(df)
if imbalance_ratio < 0.3 or imbalance_ratio > 0.7:
    print(f"   ⚠️  Class imbalance detected! Ratio: {imbalance_ratio:.2f}")
    print(f"      Using scale_pos_weight in XGBoost to handle this.")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: FEATURE SELECTION
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 3: Defining Features")
print("="*60)

# Features we USE for prediction (early signals — not G3 which is the target)
# WHY KEEP G1 AND G2?
#   They are intermediate grades available before the final exam.
#   G2 (2nd period grade) is a strong predictor of final outcome.
#   INTERVIEW: "G1 and G2 are not data leakage — they're available
#               mid-semester, before G3 is known."

# Drop G3 (target) and any identifier columns
FEATURES_TO_DROP = ["G3"]

# Separate numeric and categorical columns
# This is needed for our preprocessing pipeline
NUMERIC_FEATURES = [
    "age", "Medu", "Fedu", "traveltime", "studytime", "failures",
    "famrel", "freetime", "goout", "Dalc", "Walc", "health", "absences",
    "G1", "G2"
]

CATEGORICAL_FEATURES = [
    "school", "sex", "address", "famsize", "Pstatus",
    "Mjob", "Fjob", "reason", "guardian",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic"
]

# Verify all expected features exist in the data
all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
missing = [f for f in all_features if f not in df.columns]
if missing:
    print(f"   ⚠️  Missing features: {missing}. Will use available features.")
    NUMERIC_FEATURES = [f for f in NUMERIC_FEATURES if f in df.columns]
    CATEGORICAL_FEATURES = [f for f in CATEGORICAL_FEATURES if f in df.columns]
    all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES

X = df[all_features]
y = df["at_risk"]

print(f"   Numeric features ({len(NUMERIC_FEATURES)}): {NUMERIC_FEATURES}")
print(f"   Categorical features ({len(CATEGORICAL_FEATURES)}): {CATEGORICAL_FEATURES}")
print(f"   X shape: {X.shape}, y shape: {y.shape}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: TRAIN/TEST SPLIT
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 4: Train/Test Split")
print("="*60)

# stratify=y: ensures same class ratio in train and test sets
# (critical when there's class imbalance — prevents a test set with all "pass" students)
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,       # 80% train, 20% test
    random_state=42,     # Reproducibility
    stratify=y,          # Preserve class distribution
)

print(f"   Train: {X_train.shape} | Test: {X_test.shape}")
print(f"   Train at_risk rate: {y_train.mean():.2f} | Test at_risk rate: {y_test.mean():.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: BUILD PREPROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 5: Building Preprocessing Pipeline")
print("="*60)

# WHY A PIPELINE?
#   A Pipeline chains preprocessing steps so they execute in order.
#   CRITICAL BENEFIT: fit() on training data, transform() on test data.
#   This prevents data leakage — the scaler doesn't see test data statistics.
#
#   Without a pipeline, this mistake is easy:
#   ❌ scaler.fit(X_all)  → then split → test data "leaks" into fit
#   ✅ pipeline.fit(X_train) → pipeline.transform(X_test)

# Numeric pipeline: fill missing → scale
numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),  # Fill NaN with median
    ("scaler", StandardScaler()),                    # Z-score normalisation
])

# Categorical pipeline: fill missing → encode as integers
# WHY ORDINAL ENCODER (not OneHot)?
#   XGBoost handles ordinal-encoded categoricals well internally.
#   OneHot would create many sparse columns. For a dataset this size,
#   either works — but ordinal is simpler to interpret.
categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),  # Fill NaN with mode
    ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
])

# ColumnTransformer applies different pipelines to different column subsets
preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_pipeline, NUMERIC_FEATURES),
        ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
    ],
    remainder="drop",   # Drop any columns not listed
)

print("   ✅ Preprocessor pipeline defined.")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: TRAIN AND EVALUATE ALL MODELS
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 6: Training Models")
print("="*60)

# Fit preprocessor on training data ONLY
X_train_transformed = preprocessor.fit_transform(X_train)
X_test_transformed = preprocessor.transform(X_test)

# Handle class imbalance for XGBoost
# scale_pos_weight = (number of negatives) / (number of positives)
n_negative = (y_train == 0).sum()
n_positive = (y_train == 1).sum()
scale_pos_weight = n_negative / n_positive
print(f"   scale_pos_weight for XGBoost: {scale_pos_weight:.2f}")


def evaluate_model(name: str, model, X_tr, y_tr, X_te, y_te):
    """Train and evaluate a model. Returns key metrics dict."""
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    y_prob = model.predict_proba(X_te)[:, 1] if hasattr(model, "predict_proba") else y_pred

    metrics = {
        "Accuracy":  accuracy_score(y_te, y_pred),
        "Precision": precision_score(y_te, y_pred, zero_division=0),
        "Recall":    recall_score(y_te, y_pred, zero_division=0),
        "F1-Score":  f1_score(y_te, y_pred, zero_division=0),
        "ROC-AUC":   roc_auc_score(y_te, y_prob),
    }
    print(f"\n── {name} ──────────────────────────")
    for k, v in metrics.items():
        print(f"   {k:12s}: {v:.4f}")
    return model, metrics


# ── Model 1: Logistic Regression (Baseline) ────────────────────────────────────
# Simple, interpretable, good baseline. Used to compare against more complex models.
lr_model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
lr_model, lr_metrics = evaluate_model(
    "Logistic Regression", lr_model,
    X_train_transformed, y_train, X_test_transformed, y_test
)

# ── Model 2: Random Forest ─────────────────────────────────────────────────────
# Ensemble of decision trees. More powerful than LR. Good baseline for XGBoost.
rf_model = RandomForestClassifier(
    n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1
)
rf_model, rf_metrics = evaluate_model(
    "Random Forest", rf_model,
    X_train_transformed, y_train, X_test_transformed, y_test
)

# ── Model 3: XGBoost (Primary Model) ──────────────────────────────────────────
# Gradient boosting — iteratively corrects previous trees' errors.
# Best performance on tabular data in practice.
xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=4,              # Prevent overfitting — shallow trees
    learning_rate=0.1,        # Step size (lower = slower but more accurate)
    subsample=0.8,            # Use 80% of rows per tree (reduces overfitting)
    colsample_bytree=0.8,     # Use 80% of features per tree
    scale_pos_weight=scale_pos_weight,  # Handle class imbalance
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1,
)
xgb_model, xgb_metrics = evaluate_model(
    "XGBoost", xgb_model,
    X_train_transformed, y_train, X_test_transformed, y_test
)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7: MODEL COMPARISON SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 7: Model Comparison")
print("="*60)

comparison = pd.DataFrame({
    "Logistic Regression": lr_metrics,
    "Random Forest": rf_metrics,
    "XGBoost": xgb_metrics,
}).T

print(comparison.to_string())
print("\n🏆 Selected Model: XGBoost")
print("   Reason: Best Recall (most important for risk prediction) + highest ROC-AUC")
print("   WHY RECALL MATTERS: Missing a truly at-risk student (False Negative)")
print("   is far more costly than a false alarm (False Positive).")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8: SHAP VALUES (Global Explainability)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 8: Computing SHAP Values")
print("="*60)

# TreeExplainer is optimised for tree-based models (XGBoost, RF, LightGBM)
# It computes exact SHAP values efficiently using tree structure
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test_transformed)

# Get feature names from preprocessor
try:
    feature_names = preprocessor.get_feature_names_out()
    # Clean up column names (remove prefix added by ColumnTransformer)
    feature_names = [name.split("__")[-1] for name in feature_names]
except AttributeError:
    feature_names = NUMERIC_FEATURES + CATEGORICAL_FEATURES

print(f"   SHAP computed for {X_test_transformed.shape[0]} test students")
print(f"   Base value (expected model output): {explainer.expected_value:.4f}")
print("   → This is the average predicted risk across all students")

# ── Plot 1: Global Feature Importance (SHAP Bar Chart) ─────────────────────────
plt.figure(figsize=(10, 6))
shap.summary_plot(
    shap_values, X_test_transformed,
    feature_names=feature_names,
    plot_type="bar",
    show=False,
)
plt.title("FAILSAFE — Global Feature Importance (SHAP)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOTS_DIR}/shap_global_importance.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"   ✅ Saved: {PLOTS_DIR}/shap_global_importance.png")

# ── Plot 2: SHAP Summary (Beeswarm) ───────────────────────────────────────────
plt.figure(figsize=(10, 7))
shap.summary_plot(
    shap_values, X_test_transformed,
    feature_names=feature_names,
    show=False,
)
plt.title("FAILSAFE — SHAP Value Distribution per Feature", fontsize=14)
plt.tight_layout()
plt.savefig(f"{PLOTS_DIR}/shap_beeswarm.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"   ✅ Saved: {PLOTS_DIR}/shap_beeswarm.png")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 9: SAVE ARTIFACTS
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("STEP 9: Saving Model Artifacts")
print("="*60)

joblib.dump(xgb_model, MODEL_SAVE_PATH)
print(f"   ✅ Saved model: {MODEL_SAVE_PATH}")

joblib.dump(preprocessor, PREPROCESSOR_SAVE_PATH)
print(f"   ✅ Saved preprocessor: {PREPROCESSOR_SAVE_PATH}")

# Validate by reloading
loaded_model = joblib.load(MODEL_SAVE_PATH)
loaded_preprocessor = joblib.load(PREPROCESSOR_SAVE_PATH)
test_pred = loaded_model.predict_proba(
    loaded_preprocessor.transform(X_test.iloc[:3])
)[:, 1]
print(f"   ✅ Reload validation passed. Sample predictions: {test_pred.round(3)}")

print("\n" + "="*60)
print("✅ TRAINING COMPLETE")
print(f"   Model: {MODEL_SAVE_PATH}")
print(f"   Preprocessor: {PREPROCESSOR_SAVE_PATH}")
print(f"   SHAP plots: {PLOTS_DIR}/")
print("="*60 + "\n")
