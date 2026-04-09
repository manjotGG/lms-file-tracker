"""
Versioning Engine
==================
Core logic handler for 'commits' — receives files, hashes them,
coordinates with CAS and metadata, and creates new version nodes.
"""

from typing import BinaryIO, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.version import Version
from app.models.dag import DagEdge
from app.services import cas as cas_service
from app.services import audit_service


def create_version(
    db: Session,
    file: UploadFile,
    user_id: int,
    comment: Optional[str] = None,
    parent_version_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict:
    """
    Full version-creation pipeline:
      1. Read stream → compute SHA-256
      2. Validate file type and size
      3. Check Asset table for existing hash (de-duplication)
      4. If unique → write to CAS, create Asset row
      5. Create Version row, update HEAD pointer
      6. Create DagEdge to parent (if any)
      7. Write audit log

    Returns a dict with version metadata for the API response.
    """
    filename = file.filename or "untitled"

    # ── Step 1: Compute SHA-256 ──────────────────────────────
    sha256_hash, file_data = cas_service.compute_sha256(file.file)
    size_bytes = len(file_data)

    # ── Step 2: Validate ────────────────────────────────────
    if not cas_service.validate_file_type(filename):
        raise ValueError(
            f"File type not allowed. Permitted: {', '.join(cas_service.settings.allowed_file_types_list)}"
        )
    if not cas_service.validate_file_size(size_bytes):
        raise ValueError(
            f"File too large. Max: {cas_service.settings.MAX_FILE_SIZE_MB} MB"
        )

    # ── Step 3: De-duplication check ────────────────────────
    is_duplicate = False
    asset = db.query(Asset).filter(Asset.sha256_hash == sha256_hash).first()

    if asset is None:
        # ── Step 4: New content → store in CAS ──────────────
        cas_path = cas_service.store_blob(sha256_hash, file_data)
        asset = Asset(
            sha256_hash=sha256_hash,
            size_bytes=size_bytes,
            content_type=file.content_type,
            cas_path=cas_path,
        )
        db.add(asset)
        db.flush()  # Get asset.id without committing yet
    else:
        is_duplicate = True

    # ── Step 5: Resolve parent version ──────────────────────
    parent_db_id = None
    if parent_version_id:
        parent = (
            db.query(Version)
            .filter(Version.version_id == parent_version_id)
            .first()
        )
        if parent:
            parent_db_id = parent.id
    else:
        # Auto-link to current HEAD for this file/user
        head = (
            db.query(Version)
            .filter(
                Version.filename == filename,
                Version.user_id == user_id,
                Version.is_head == True,
            )
            .first()
        )
        if head:
            parent_db_id = head.id

    # ── Step 6: Demote old HEAD, create new Version ─────────
    if parent_db_id:
        db.query(Version).filter(
            Version.filename == filename,
            Version.user_id == user_id,
            Version.is_head == True,
        ).update({"is_head": False})

    version = Version(
        filename=filename,
        asset_id=asset.id,
        user_id=user_id,
        parent_version_id=parent_db_id,
        comment=comment,
        is_head=True,
    )
    db.add(version)
    db.flush()

    # Count total versions for this file/user
    version_number = (
        db.query(Version)
        .filter(Version.filename == filename, Version.user_id == user_id)
        .count()
    )

    # ── Step 7: Create DAG edge ─────────────────────────────
    if parent_db_id:
        edge = DagEdge(
            parent_version_id=parent_db_id,
            child_version_id=version.id,
        )
        db.add(edge)

    # ── Step 8: Audit log ───────────────────────────────────
    audit_service.log_action(
        db=db,
        action="file.upload",
        user_id=user_id,
        resource_type="version",
        resource_id=version.version_id,
        details={
            "filename": filename,
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
            "is_duplicate_content": is_duplicate,
            "version_number": version_number,
        },
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(version)

    return {
        "version_id": version.version_id,
        "filename": filename,
        "sha256_hash": sha256_hash,
        "size_bytes": size_bytes,
        "version_number": version_number,
        "is_duplicate_content": is_duplicate,
        "message": (
            "Content already exists (de-duplicated)" if is_duplicate
            else "New version created successfully"
        ),
    }
