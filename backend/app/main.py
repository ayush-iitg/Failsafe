"""
main.py — FastAPI Application Entry Point
==========================================
This is the root of the backend application.

HOW FASTAPI WORKS:
  1. We create an `app = FastAPI()` instance
  2. We register routers (each router = a group of related endpoints)
  3. We add middleware (CORS — allows React frontend to call this API)
  4. Uvicorn runs this as an ASGI server

WHY FASTAPI OVER FLASK/DJANGO?
  - Async-native: handles many concurrent requests efficiently
  - Automatic OpenAPI (Swagger) docs at /docs — great for testing
  - Pydantic integration: automatic request validation + serialisation
  - Much faster than Flask for IO-bound tasks (DB queries, ML inference)
  - Industry adoption: used by Netflix, Uber, Microsoft for ML APIs

RUN THIS APP:
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  --reload: auto-restart on code changes (development only)
  --host 0.0.0.0: accept connections from any network interface
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import engine, Base
from app.routers import auth, upload, dashboard, explain, interventions

# ── Logging configuration ──────────────────────────────────────────────────────
# In production: use structured logging (JSON) and ship logs to a log aggregator
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Create FastAPI app ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "FAILSAFE — Explainable AI Powered Student Failure Risk Prediction System. "
        "Predicts at-risk students using XGBoost + SHAP, and generates "
        "personalised intervention plans."
    ),
    docs_url="/docs",        # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",      # ReDoc UI at http://localhost:8000/redoc
    debug=settings.DEBUG,
)


# ── CORS Middleware ────────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Browsers block JS from calling APIs on different origins by default.
# We must explicitly allow our React frontend's origin.
#
# INTERVIEW Q: "What is CORS and why do you need it?"
# ANSWER: "CORS is a browser security mechanism. Since React runs on
#          localhost:5173 and FastAPI on localhost:8000, they are different
#          'origins'. The browser blocks cross-origin requests unless the
#          server includes the right CORS headers."
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Create React App dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,        # Allow cookies/auth headers
    allow_methods=["*"],           # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],           # Allow all headers (including Authorization)
)


# ── Register Routers ───────────────────────────────────────────────────────────
# Each router handles a group of related endpoints.
# prefix="/api/..." is set inside each router file.
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(explain.router)
app.include_router(interventions.router)


# ── Startup Event ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """
    Runs once when the server starts.
    Creates all DB tables if they don't exist.
    In production: use Alembic migrations instead of create_all.
    """
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Create tables from SQLAlchemy models
    # NOTE: In production, use `alembic upgrade head` instead
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables verified/created.")


# ── Health Check Endpoint ──────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """
    Simple health check endpoint.
    Used by load balancers and monitoring tools to verify the service is running.
    Returns 200 OK if the server is up.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
def root():
    """Root endpoint — directs developers to API docs."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }
