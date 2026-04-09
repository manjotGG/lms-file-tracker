"""
Metadata Orchestrator
======================
Manages the DAG structure, HEAD pointers, and version history queries.
"""

from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.version import Version
from app.models.dag import DagEdge
from app.models.asset import Asset


def get_version_history(
    db: Session,
    filename: str,
    user_id: Optional[int] = None,
) -> List[Version]:
    """
    Get the full version history for a file, ordered newest-first.
    Optionally filter by user.
    """
    query = db.query(Version).filter(Version.filename == filename)
    if user_id is not None:
        query = query.filter(Version.user_id == user_id)
    return query.order_by(Version.created_at.desc()).all()


def get_head(
    db: Session,
    filename: str,
    user_id: int,
) -> Optional[Version]:
    """Get the current HEAD version for a file/user pair."""
    return (
        db.query(Version)
        .filter(
            Version.filename == filename,
            Version.user_id == user_id,
            Version.is_head == True,
        )
        .first()
    )


def get_version_by_id(
    db: Session,
    version_id: str,
) -> Optional[Version]:
    """Look up a specific version by its public version_id."""
    return (
        db.query(Version)
        .filter(Version.version_id == version_id)
        .first()
    )


def move_head(
    db: Session,
    filename: str,
    user_id: int,
    target_version_id: str,
) -> Optional[Version]:
    """
    Move the HEAD pointer for a file/user to a specific version ('checkout').
    """
    target = (
        db.query(Version)
        .filter(
            Version.version_id == target_version_id,
            Version.filename == filename,
            Version.user_id == user_id,
        )
        .first()
    )
    if not target:
        return None

    # Demote current HEAD
    db.query(Version).filter(
        Version.filename == filename,
        Version.user_id == user_id,
        Version.is_head == True,
    ).update({"is_head": False})

    # Promote target
    target.is_head = True
    db.commit()
    db.refresh(target)
    return target


def get_dag_tree(
    db: Session,
    filename: str,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Build the full DAG as a list of nodes with children.
    Returns root nodes (versions with no parent).
    """
    query = db.query(Version).filter(Version.filename == filename)
    if user_id is not None:
        query = query.filter(Version.user_id == user_id)
    versions = query.order_by(Version.created_at.asc()).all()

    # Build adjacency map
    id_to_version = {v.id: v for v in versions}
    children_map: Dict[int, List[int]] = {v.id: [] for v in versions}
    roots = []

    edges = db.query(DagEdge).filter(
        DagEdge.child_version_id.in_([v.id for v in versions])
    ).all()

    child_ids_with_parents = set()
    for edge in edges:
        if edge.parent_version_id in children_map:
            children_map[edge.parent_version_id].append(edge.child_version_id)
            child_ids_with_parents.add(edge.child_version_id)

    # Roots: versions that are not children of any edge
    for v in versions:
        if v.id not in child_ids_with_parents:
            roots.append(v.id)

    def _build_node(vid: int) -> Dict[str, Any]:
        v = id_to_version[vid]
        return {
            "version_id": v.version_id,
            "filename": v.filename,
            "sha256_hash": v.asset.sha256_hash if v.asset else "",
            "comment": v.comment,
            "is_head": v.is_head,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "children": [_build_node(cid) for cid in children_map.get(vid, [])],
        }

    return [_build_node(rid) for rid in roots]


def get_all_files(
    db: Session,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    List all unique filenames with their latest version info.
    """
    query = db.query(Version).filter(Version.is_head == True)
    if user_id is not None:
        query = query.filter(Version.user_id == user_id)
    heads = query.order_by(Version.filename).all()

    return [
        {
            "filename": v.filename,
            "version_id": v.version_id,
            "sha256_hash": v.asset.sha256_hash if v.asset else "",
            "size_bytes": v.asset.size_bytes if v.asset else 0,
            "username": v.user.username if v.user else "",
            "comment": v.comment,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in heads
    ]
