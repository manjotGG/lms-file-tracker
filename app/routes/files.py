"""
File Routes
============
Core versioning endpoints: upload, download, version history, diff.
All endpoints require JWT authentication.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.version import (
    UploadResponse,
    VersionHistoryResponse,
    VersionResponse,
    DiffResponse,
)
from app.services import versioning_engine, metadata_orchestrator, delta_service
from app.services import cas as cas_service

router = APIRouter(prefix="/files", tags=["File Versioning"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file (creates a new version)",
)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    comment: Optional[str] = Form(None),
    parent_version_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file to the VC-LMS system.

    - The file is hashed (SHA-256). If the content already exists, it's de-duplicated.
    - A new version node is created in the DAG.
    - The HEAD pointer is updated to the new version.
    """
    try:
        result = versioning_engine.create_version(
            db=db,
            file=file,
            user_id=current_user.id,
            comment=comment,
            parent_version_id=parent_version_id,
            ip_address=request.client.host if request.client else None,
        )
        return UploadResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/upload/batch",
    summary="Upload multiple files atomically (2PC)",
)
def upload_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    comment: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload multiple files in a single atomic transaction.
    Uses Two-Phase Commit: all files succeed or all are rolled back.
    """
    from app.services import transaction_handler

    try:
        # Phase 1: PREPARE
        ctx = transaction_handler.prepare(
            db=db,
            files=files,
            user_id=current_user.id,
            comment=comment,
        )
        # Phase 2: COMMIT
        results = transaction_handler.commit(
            db=db,
            ctx=ctx,
            ip_address=request.client.host if request.client else None,
        )
        return {
            "message": f"Successfully uploaded {len(results)} files",
            "versions": results,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/versions/{filename:path}",
    response_model=VersionHistoryResponse,
    summary="Get version history for a file",
)
def get_versions(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the full version history (commit log) for a file.
    Shows all versions ordered by creation time (newest first).
    """
    versions = metadata_orchestrator.get_version_history(
        db=db, filename=filename, user_id=current_user.id
    )

    return VersionHistoryResponse(
        filename=filename,
        total_versions=len(versions),
        versions=[
            VersionResponse(
                id=v.id,
                version_id=v.version_id,
                filename=v.filename,
                sha256_hash=v.asset.sha256_hash,
                size_bytes=v.asset.size_bytes,
                user_id=v.user_id,
                username=v.user.username,
                comment=v.comment,
                is_head=v.is_head,
                created_at=v.created_at,
            )
            for v in versions
        ],
    )


@router.get(
    "/download/{version_id}",
    summary="Download a specific version of a file",
)
def download_file(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the content of a specific version.
    Retrieves the blob from CAS and streams it to the client.
    """
    version = metadata_orchestrator.get_version_by_id(db, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_id}' not found",
        )

    try:
        content = cas_service.retrieve_blob(version.asset.cas_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blob not found in CAS — data integrity error",
        )

    return StreamingResponse(
        io.BytesIO(content),
        media_type=version.asset.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{version.filename}"',
            "X-SHA256": version.asset.sha256_hash,
            "X-Version-ID": version.version_id,
        },
    )


@router.get(
    "/diff/{version_a_id}/{version_b_id}",
    response_model=DiffResponse,
    summary="Compute diff between two versions",
)
def get_diff(
    version_a_id: str,
    version_b_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute and return a unified diff between two file versions.
    Useful for instructors to monitor student progress.
    """
    try:
        result = delta_service.compute_diff(db, version_a_id, version_b_id)
        return DiffResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/dag/{filename:path}",
    summary="Get the DAG tree for a file",
)
def get_dag(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the full Directed Acyclic Graph for a file's version history.
    Returns a tree structure showing parent-child relationships.
    """
    tree = metadata_orchestrator.get_dag_tree(
        db=db, filename=filename, user_id=current_user.id
    )
    return {"filename": filename, "dag": tree}


@router.get(
    "/head/{filename:path}",
    summary="Get the HEAD version of a file",
)
def get_head(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current HEAD version for a file."""
    head = metadata_orchestrator.get_head(
        db=db, filename=filename, user_id=current_user.id
    )
    if not head:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No versions found for '{filename}'",
        )
    return VersionResponse(
        id=head.id,
        version_id=head.version_id,
        filename=head.filename,
        sha256_hash=head.asset.sha256_hash,
        size_bytes=head.asset.size_bytes,
        user_id=head.user_id,
        username=head.user.username,
        comment=head.comment,
        is_head=head.is_head,
        created_at=head.created_at,
    )


@router.put(
    "/checkout/{filename:path}",
    summary="Move HEAD to a specific version (checkout)",
)
def checkout(
    filename: str,
    target_version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move the HEAD pointer for a file to a specific version."""
    version = metadata_orchestrator.move_head(
        db=db,
        filename=filename,
        user_id=current_user.id,
        target_version_id=target_version_id,
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found or doesn't belong to this file/user",
        )
    return {"message": f"HEAD moved to {target_version_id}", "version_id": version.version_id}


@router.get(
    "/list",
    summary="List all files (HEAD versions)",
)
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all files the current user has uploaded (shows HEAD versions only)."""
    files = metadata_orchestrator.get_all_files(db=db, user_id=current_user.id)
    return {"files": files, "total": len(files)}
