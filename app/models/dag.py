"""
DAG Edge Model — Explicit parent→child edges for the version graph.
Supports branching and merging scenarios (a version can have multiple parents).
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint

from app.database import Base


class DagEdge(Base):
    """
    Directed edge in the version DAG.
    Stored separately from Version.parent_version_id to support
    merge commits (multiple parents) and complex branching.
    """
    __tablename__ = "dag_edges"

    id = Column(Integer, primary_key=True, index=True)
    parent_version_id = Column(
        Integer, ForeignKey("versions.id"), nullable=False, index=True
    )
    child_version_id = Column(
        Integer, ForeignKey("versions.id"), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "parent_version_id", "child_version_id",
            name="uq_dag_edge",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DagEdge(parent={self.parent_version_id} → "
            f"child={self.child_version_id})>"
        )
