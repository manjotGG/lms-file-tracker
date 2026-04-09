"""
VC-LMS Database Initializer
=============================
Creates all tables from the new app models.

Usage:
    python init_db_new.py
"""

from app.database import engine
from app.models import Base

# Import all models so they register with Base.metadata
from app.models import User, Asset, Version, DagEdge, AuditLog  # noqa: F401


def init():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ VC-LMS database tables created successfully!")
    print("   Tables: users, assets, versions, dag_edges, audit_logs")


if __name__ == "__main__":
    init()
