"""
Asset Model — Content-Addressable Storage Reference
Each row maps to one unique blob in the CAS (de-duplicated by SHA-256 hash).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, BigInteger, DateTime

from app.database import Base


class Asset(Base):
    """
    An immutable content-addressed blob.
    The sha256_hash is the unique content identifier; duplicate uploads
    point to the same Asset row.
    """
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    sha256_hash = Column(String(64), unique=True, nullable=False, index=True)
    size_bytes = Column(BigInteger, nullable=False)
    content_type = Column(String(255), nullable=True)
    cas_path = Column(String(512), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, hash='{self.sha256_hash[:12]}…')>"
