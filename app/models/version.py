"""
Version Model — A single 'commit' node in the DAG.
Each version links to an Asset (the actual content) and optionally to a parent version.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DateTime, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _generate_version_id() -> str:
    """Generate a unique version identifier."""
    return uuid.uuid4().hex


class Version(Base):
    """
    A versioned snapshot ('commit') of a file.
    Forms the nodes of the Directed Acyclic Graph.
    """
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(
        String(32),
        unique=True,
        nullable=False,
        default=_generate_version_id,
        index=True,
    )
    filename = Column(String(512), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_version_id = Column(
        Integer, ForeignKey("versions.id"), nullable=True
    )
    comment = Column(Text, nullable=True)
    is_head = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    asset = relationship("Asset", lazy="joined")
    user = relationship("User", lazy="joined")
    parent = relationship("Version", remote_side=[id], lazy="select")

    def __repr__(self) -> str:
        return (
            f"<Version(id={self.id}, version_id='{self.version_id[:8]}…', "
            f"file='{self.filename}', head={self.is_head})>"
        )
