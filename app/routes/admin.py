"""
Admin Routes
=============
Administrative endpoints for managing users, files, and viewing audit logs.
Restricted to admin and teacher roles.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role, get_current_user
from app.models.user import User, UserRole
from app.models.version import Version
from app.models.audit import AuditLog
from app.services import metadata_orchestrator, delta_service, audit_service
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get(
    "/files",
    summary="List all files across all users",
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))],
)
def list_all_files(
    db: Session = Depends(get_db),
):
    """List all files in the system (HEAD versions only). Admin/Teacher only."""
    files = metadata_orchestrator.get_all_files(db=db)
    return {"files": files, "total": len(files)}


@router.get(
    "/users",
    summary="List all registered users",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def list_users(
    db: Session = Depends(get_db),
):
    """List all registered users. Admin only."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": len(users),
    }


@router.get(
    "/audit",
    summary="View audit logs",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """
    Query the audit log with optional filters.
    Returns the most recent entries first. Admin only.
    """
    logs = audit_service.get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.user.username if log.user else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": json.loads(log.details) if log.details else None,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }


@router.get(
    "/student/{username}/timeline",
    summary="View a student's submission timeline with diffs",
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))],
)
def student_timeline(
    username: str,
    filename: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Forensic diff timeline for a specific student.
    Shows all submissions with diffs between consecutive versions.
    Useful for instructors to monitor student work progress.
    """
    # Find student
    student = db.query(User).filter(User.username == username).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{username}' not found",
        )

    # Get all versions by this student
    query = db.query(Version).filter(Version.user_id == student.id)
    if filename:
        query = query.filter(Version.filename == filename)
    versions = query.order_by(Version.created_at.asc()).all()

    timeline = []
    for i, v in enumerate(versions):
        entry = {
            "version_id": v.version_id,
            "filename": v.filename,
            "sha256_hash": v.asset.sha256_hash if v.asset else "",
            "comment": v.comment,
            "is_head": v.is_head,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "diff_from_previous": None,
        }

        # Compute diff with previous version of the same file
        if i > 0 and versions[i - 1].filename == v.filename:
            try:
                diff = delta_service.compute_diff(
                    db, versions[i - 1].version_id, v.version_id
                )
                entry["diff_from_previous"] = {
                    "additions": diff["additions"],
                    "deletions": diff["deletions"],
                    "diff_text": diff["diff_text"],
                }
            except Exception:
                entry["diff_from_previous"] = {"error": "Could not compute diff"}

        timeline.append(entry)

    return {
        "student": username,
        "total_submissions": len(timeline),
        "timeline": timeline,
    }


@router.patch(
    "/users/{user_id}/role",
    summary="Change a user's role",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def change_user_role(
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
):
    """Change a user's role. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        role = UserRole(new_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Choose from: {[r.value for r in UserRole]}",
        )

    user.role = role
    db.commit()
    return {"message": f"User '{user.username}' role updated to '{role.value}'"}


@router.patch(
    "/users/{user_id}/status",
    summary="Activate or deactivate a user",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def toggle_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user account. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = is_active
    db.commit()
    status_str = "activated" if is_active else "deactivated"
    return {"message": f"User '{user.username}' has been {status_str}"}
