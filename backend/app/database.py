"""
database.py — Database Connection & Session Management
=======================================================
Sets up SQLAlchemy to connect to PostgreSQL.

KEY CONCEPTS (interview-ready):

1. ENGINE:
   The engine is the "connection pool" — it manages N simultaneous connections
   to PostgreSQL. We don't connect per-request; we reuse pooled connections.

2. SESSION:
   A session is a "unit of work" — one request gets one session, performs its
   DB operations, then the session is closed. This follows the
   "session-per-request" pattern.

3. get_db() — DEPENDENCY INJECTION:
   FastAPI's Depends(get_db) injects a fresh DB session into each route handler.
   The `finally` block guarantees the session is closed even if an exception occurs.
   This prevents connection leaks — a common production bug.

WHY SQLALCHEMY OVER RAW SQL?
   - ORM maps Python classes to DB tables — no manual SQL string building
   - Prevents SQL injection by default (parameterised queries)
   - Easy to swap databases (SQLite for testing, PostgreSQL for production)
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────
# pool_pre_ping=True: tests connections before use — handles stale connections
# (e.g., PostgreSQL restarted, or idle connection timed out)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,        # Max 10 persistent connections in pool
    max_overflow=20,     # Allow up to 20 extra connections under load
)

# ── Session Factory ────────────────────────────────────────────────────────────
# autocommit=False: we manually commit transactions (safer, explicit)
# autoflush=False:  we control when changes are flushed to DB
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Base Class ─────────────────────────────────────────────────────────────────
# All SQLAlchemy ORM models inherit from this Base.
# It keeps a registry of all model classes → used by Base.metadata.create_all()
Base = declarative_base()


# ── Dependency: get_db() ───────────────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Usage in a route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The `yield` makes this a "generator dependency" — code after yield runs
    on cleanup (like a context manager). This guarantees db.close() always runs.
    """
    db = SessionLocal()
    try:
        yield db          # Hand session to the route handler
    finally:
        db.close()        # Always close — even if an exception was raised
