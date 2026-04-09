"""
Webhook Routes
===============
CI/CD integration bridge.
Receives commit notifications and runs automated validation checks.
"""

import hmac
import hashlib
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.version import Version
from app.config import settings
from app.services import cas as cas_service, audit_service
from app.schemas.webhook import (
    WebhookCommitPayload,
    WebhookCheckResult,
    WebhookResponse,
)

router = APIRouter(prefix="/webhooks", tags=["CI/CD Webhooks"])


def _verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verify the HMAC-SHA256 signature of a webhook payload.
    Prevents unauthorized webhook triggers.
    """
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _check_file_type(filename: str) -> WebhookCheckResult:
    """Validate file type against the whitelist."""
    is_valid = cas_service.validate_file_type(filename)
    return WebhookCheckResult(
        check_name="file_type_check",
        passed=is_valid,
        message="File type is allowed" if is_valid else f"File type not in whitelist",
        details=f"Allowed types: {', '.join(settings.allowed_file_types_list)}",
    )


def _check_file_size(size_bytes: int) -> WebhookCheckResult:
    """Validate file size against the limit."""
    is_valid = cas_service.validate_file_size(size_bytes)
    return WebhookCheckResult(
        check_name="file_size_check",
        passed=is_valid,
        message="File size is within limits" if is_valid else "File exceeds size limit",
        details=f"Max: {settings.MAX_FILE_SIZE_MB} MB, Actual: {size_bytes / (1024*1024):.2f} MB",
    )


def _check_hash_integrity(version: Version) -> WebhookCheckResult:
    """Verify that the stored blob matches its recorded hash."""
    try:
        blob = cas_service.retrieve_blob(version.asset.cas_path)
        actual_hash = hashlib.sha256(blob).hexdigest()
        matches = actual_hash == version.asset.sha256_hash
        return WebhookCheckResult(
            check_name="integrity_check",
            passed=matches,
            message="Hash integrity verified" if matches else "HASH MISMATCH — data may be corrupted",
            details=f"Expected: {version.asset.sha256_hash[:16]}…, Got: {actual_hash[:16]}…",
        )
    except FileNotFoundError:
        return WebhookCheckResult(
            check_name="integrity_check",
            passed=False,
            message="Blob not found in CAS",
        )


@router.post(
    "/on-commit",
    response_model=WebhookResponse,
    summary="CI/CD hook triggered on each commit",
)
async def on_commit(
    request: Request,
    payload: WebhookCommitPayload,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint triggered after each file upload ('commit').

    Runs automated checks:
      1. File type validation
      2. File size validation
      3. Hash integrity verification

    Optionally verifies the webhook signature (HMAC-SHA256).
    """
    # Verify signature if provided
    if x_webhook_signature:
        body = await request.body()
        if not _verify_webhook_signature(body, x_webhook_signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature",
            )

    # Look up the version
    version = (
        db.query(Version)
        .filter(Version.version_id == payload.version_id)
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{payload.version_id}' not found",
        )

    # Run checks
    checks = [
        _check_file_type(version.filename),
        _check_file_size(version.asset.size_bytes),
        _check_hash_integrity(version),
    ]

    all_passed = all(c.passed for c in checks)

    # Audit the CI/CD result
    audit_service.log_action(
        db=db,
        action="webhook.on_commit",
        user_id=payload.user_id,
        resource_type="version",
        resource_id=payload.version_id,
        details={
            "all_passed": all_passed,
            "checks": [
                {"name": c.check_name, "passed": c.passed, "message": c.message}
                for c in checks
            ],
        },
        ip_address=request.client.host if request.client else None,
    )

    return WebhookResponse(
        version_id=payload.version_id,
        all_passed=all_passed,
        checks=checks,
    )
