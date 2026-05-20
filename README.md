# 🛡️ FAILSAFE
### Explainable AI-Powered Student Failure Risk Prediction System

> Built as a placement-ready, production-inspired full-stack ML project for IIT-level DS/ML roles.

---

## 📌 Problem Statement

In educational institutions, student failure often goes undetected until end-of-semester results — leaving no room for meaningful intervention. Faculty lack a proactive, data-driven tool to identify at-risk students early and understand the root causes behind their struggles.

**FAILSAFE** solves this by:
- Predicting failure risk **early** using attendance, assignments, and behavioural data
- Using **SHAP (Explainable AI)** to make every prediction transparent and trustworthy
- **Auto-generating personalised intervention plans** so faculty can act before it's too late
- Providing a **dashboard** for faculty and HODs to track risk trends and monitor improvement

---

## 🎯 Goals

| Goal | Implementation |
|------|---------------|
| Early risk prediction | XGBoost classifier on UCI Student Performance dataset |
| Explainability | SHAP values — global + local (per student) |
| Personalised interventions | Rule-based engine mapping risk features → action plans |
| Faculty/HOD dashboard | React.js with KPI cards, risk charts, student drill-down |

---

## 🧠 Tech Stack

### Machine Learning
- **Python** — core language
- **XGBoost** — primary classifier (gradient boosting, best for tabular data)
- **scikit-learn** — preprocessing pipeline, Logistic Regression, Random Forest baselines
- **SHAP** — Explainable AI (SHapley Additive exPlanations)
- **Pandas** — data manipulation
- **Matplotlib / Seaborn** — EDA visualisations

### Backend
- **FastAPI** — modern Python REST API framework
- **PostgreSQL** — relational database
- **SQLAlchemy** — ORM (Object Relational Mapper)
- **JWT Authentication** — secure login

### Frontend
- **React.js** — component-based UI
- **HTML / CSS** — structure and styling
- **Recharts** — analytics charts
- **Axios** — HTTP client

---

## 🏗️ System Architecture

```
Browser (React.js)
    │  HTTP REST
    ▼
FastAPI Backend
    ├── Auth        → JWT login
    ├── Upload      → CSV ingestion
    ├── Predict     → XGBoost inference
    ├── Explain     → SHAP values
    ├── Intervene   → Rule-based plans
    └── Dashboard   → Analytics aggregation
    │  SQLAlchemy ORM
    ▼
PostgreSQL Database
    ├── users
    ├── students
    ├── predictions
    └── interventions
```

---

## 📁 Folder Structure

```
Failsafe/
├── ml/                        ← ML training, EDA, model artifacts
│   ├── data/                  ← UCI dataset CSV
│   ├── notebooks/             ← Jupyter EDA + modeling notebooks
│   ├── models/                ← Saved .pkl model artifacts
│   ├── train.py               ← Standalone training script
│   └── requirements.txt
│
├── backend/                   ← FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/            ← SQLAlchemy DB models
│   │   ├── schemas/           ← Pydantic schemas
│   │   ├── routers/           ← API route handlers
│   │   └── services/          ← ML inference, SHAP, rule engine
│   └── requirements.txt
│
├── frontend/                  ← React.js dashboard
│   ├── src/
│   │   ├── api/               ← Axios API layer
│   │   ├── components/        ← Reusable UI components
│   │   └── pages/             ← Full page views
│   └── package.json
│
└── README.md
```

---

## 🗺️ Build Roadmap

| Phase | Description |
|-------|-------------|
| **Phase 1** | Problem Understanding & Architecture |
| **Phase 2** | Dataset EDA (UCI Student Performance) |
| **Phase 3** | Data Preprocessing & Pipeline |
| **Phase 4** | ML Modeling (LR → RF → XGBoost) |
| **Phase 5** | Explainable AI with SHAP |
| **Phase 6** | Intervention Rule Engine |
| **Phase 7** | FastAPI Backend |
| **Phase 8** | React.js Frontend Dashboard |
| **Phase 9** | PostgreSQL Schema Design |
| **Phase 10** | Deployment |
| **Phase 11** | Placement Preparation |

---

## 📊 Dataset

**UCI Student Performance Dataset** — by Paulo Cortez & A. Silva (2008)
- **Official UCI source:** https://archive.ics.uci.edu/ml/datasets/student+performance
- **Download on Kaggle:** https://www.kaggle.com/datasets/uciml/student-alcohol-consumption
  > ⚠️ The Kaggle upload has a misleading name ("Student Alcohol Consumption"), but it contains
  > the correct UCI Student Performance files: `student-mat.csv` and `student-por.csv`.
  > We use `student-mat.csv` (Mathematics course, 395 students).
- **Features:** grades (G1, G2), study time, failures, absences, family support, social behaviour
- **Target:** Binary — `at_risk = 1` if final grade G3 < 10 (failing), else 0

---

## 🚀 Quick Start

### ML Training
```bash
cd ml
pip install -r requirements.txt
python train.py
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📝 Interview Talking Points

- **Why XGBoost?** Best performance on tabular data; handles missing values natively; wins Kaggle competitions
- **Why SHAP?** Model-agnostic, theoretically grounded (Shapley values from game theory), more reliable than permutation importance
- **Why Recall > Precision?** Missing a truly at-risk student (False Negative) is far more costly than a false alarm
- **Why FastAPI?** Async support, auto-generates OpenAPI docs, native Pydantic validation — industry standard for ML serving
- **Why PostgreSQL?** ACID compliance, structured schema for user/prediction/intervention relationships

---

## 👨‍💻 Author

Built by a 4th year IIT student as a placement-ready Data Scientist / ML Engineer portfolio project.
