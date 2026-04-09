"""
VC-LMS — Main Application
===========================
FastAPI application factory with all routers, middleware, and startup events.

Usage:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.middleware.rate_limiter import limiter
from app.middleware.audit_middleware import AuditMiddleware

# Import all models so they're registered with Base.metadata
from app.models import User, Asset, Version, DagEdge, AuditLog  # noqa: F401

from app.routes import auth, files, admin, webhooks


# ── App Factory ──────────────────────────────────────────────

def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Version Control Learning Management System — "
            "Git-inspired versioning with content-addressable storage, "
            "DAG-based history, and RBAC authentication."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ────────────────────────────────────────────

    # CORS (adjust origins for production)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Audit logging middleware
    application.add_middleware(AuditMiddleware)

    # Rate limiting
    application.state.limiter = limiter
    application.add_exception_handler(
        RateLimitExceeded, _rate_limit_exceeded_handler
    )

    # ── Routers ──────────────────────────────────────────────

    application.include_router(auth.router)
    application.include_router(files.router)
    application.include_router(admin.router)
    application.include_router(webhooks.router)

    # ── Startup Events ───────────────────────────────────────

    @application.on_event("startup")
    def on_startup():
        """Create all database tables on startup."""
        Base.metadata.create_all(bind=engine)

    # ── Root Endpoint ────────────────────────────────────────

    @application.get("/", tags=["Health"])
    def root():
        return {
            "service": settings.APP_NAME,
            "version": "2.0.0",
            "status": "running",
            "docs": "/docs",
            "architecture": "Microservice + Event-Driven + CAS + DAG Version Control",
        }

    @application.get("/health", tags=["Health"])
    def health():
        return {"status": "healthy"}

    return application


# Create the app instance
app = create_app()
