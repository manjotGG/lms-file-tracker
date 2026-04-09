"""
Atomic Transaction Handler
============================
Implements Two-Phase Commit (2PC) for multi-file uploads.

Phase 1 — PREPARE: Validate all files + write to CAS (reversible).
Phase 2 — COMMIT: Write all metadata to DB. On failure → rollback CAS writes.
"""

from typing import List, Optional
from dataclasses import dataclass, field

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.version import Version
from app.models.dag import DagEdge
from app.services import cas as cas_service
from app.services import audit_service


@dataclass
class PreparedFile:
    """Result of the PREPARE phase for a single file."""
    filename: str
    sha256_hash: str
    size_bytes: int
    content_type: Optional[str]
    cas_path: str
    file_data: bytes
    is_duplicate: bool
    asset: Optional[Asset] = None


@dataclass
class TransactionContext:
    """Tracks the 2PC transaction state."""
    user_id: int
    comment: Optional[str] = None
    prepared_files: List[PreparedFile] = field(default_factory=list)
    created_assets: List[str] = field(default_factory=list)  # hashes for rollback
    committed: bool = False


def prepare(
    db: Session,
    files: List[UploadFile],
    user_id: int,
    comment: Optional[str] = None,
) -> TransactionContext:
    """
    PREPARE phase: Validate and write all blobs to CAS.
    Does NOT write any metadata to the database.
    On failure, rolls back any CAS writes already completed.
    """
    ctx = TransactionContext(user_id=user_id, comment=comment)

    try:
        for file in files:
            filename = file.filename or "untitled"

            # Hash the file
            sha256_hash, file_data = cas_service.compute_sha256(file.file)
            size_bytes = len(file_data)

            # Validate
            if not cas_service.validate_file_type(filename):
                raise ValueError(f"File type not allowed: {filename}")
            if not cas_service.validate_file_size(size_bytes):
                raise ValueError(f"File too large: {filename}")

            # Check for existing asset (de-dup)
            existing_asset = (
                db.query(Asset)
                .filter(Asset.sha256_hash == sha256_hash)
                .first()
            )

            if existing_asset:
                cas_path = existing_asset.cas_path
                is_duplicate = True
            else:
                # Write to CAS
                cas_path = cas_service.store_blob(sha256_hash, file_data)
                ctx.created_assets.append(sha256_hash)
                is_duplicate = False

            ctx.prepared_files.append(PreparedFile(
                filename=filename,
                sha256_hash=sha256_hash,
                size_bytes=size_bytes,
                content_type=file.content_type,
                cas_path=cas_path,
                file_data=file_data,
                is_duplicate=is_duplicate,
                asset=existing_asset,
            ))

    except Exception:
        # Rollback: delete any newly written blobs
        _rollback_cas(ctx)
        raise

    return ctx


def commit(
    db: Session,
    ctx: TransactionContext,
    ip_address: Optional[str] = None,
) -> List[dict]:
    """
    COMMIT phase: Write all metadata to the database.
    Only called after a successful PREPARE.
    """
    results = []

    try:
        for pf in ctx.prepared_files:
            # Create or reuse Asset
            if pf.asset is None:
                asset = Asset(
                    sha256_hash=pf.sha256_hash,
                    size_bytes=pf.size_bytes,
                    content_type=pf.content_type,
                    cas_path=pf.cas_path,
                )
                db.add(asset)
                db.flush()
            else:
                asset = pf.asset

            # Find current HEAD
            head = (
                db.query(Version)
                .filter(
                    Version.filename == pf.filename,
                    Version.user_id == ctx.user_id,
                    Version.is_head == True,
                )
                .first()
            )
            parent_db_id = head.id if head else None

            # Demote old HEAD
            if parent_db_id:
                db.query(Version).filter(
                    Version.filename == pf.filename,
                    Version.user_id == ctx.user_id,
                    Version.is_head == True,
                ).update({"is_head": False})

            # Create Version
            version = Version(
                filename=pf.filename,
                asset_id=asset.id,
                user_id=ctx.user_id,
                parent_version_id=parent_db_id,
                comment=ctx.comment,
                is_head=True,
            )
            db.add(version)
            db.flush()

            # Create DAG edge
            if parent_db_id:
                db.add(DagEdge(
                    parent_version_id=parent_db_id,
                    child_version_id=version.id,
                ))

            version_number = (
                db.query(Version)
                .filter(
                    Version.filename == pf.filename,
                    Version.user_id == ctx.user_id,
                )
                .count()
            )

            results.append({
                "version_id": version.version_id,
                "filename": pf.filename,
                "sha256_hash": pf.sha256_hash,
                "size_bytes": pf.size_bytes,
                "version_number": version_number,
                "is_duplicate_content": pf.is_duplicate,
            })

        # Audit log for the batch
        audit_service.log_action(
            db=db,
            action="file.batch_upload",
            user_id=ctx.user_id,
            resource_type="transaction",
            details={
                "file_count": len(ctx.prepared_files),
                "files": [r["filename"] for r in results],
            },
            ip_address=ip_address,
        )

        db.commit()
        ctx.committed = True

    except Exception:
        db.rollback()
        _rollback_cas(ctx)
        raise

    return results


def _rollback_cas(ctx: TransactionContext) -> None:
    """Delete any blobs that were written during the PREPARE phase."""
    for sha256_hash in ctx.created_assets:
        cas_service.delete_blob(sha256_hash)
    ctx.created_assets.clear()
