"""
Webhook Schemas — CI/CD integration payloads.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class WebhookCommitPayload(BaseModel):
    """Payload sent to CI/CD webhook on each commit."""
    version_id: str
    filename: str
    sha256_hash: str
    user_id: int
    username: str
    timestamp: datetime


class WebhookCheckResult(BaseModel):
    """Result of a CI/CD check (lint, test, etc.)."""
    check_name: str
    passed: bool
    message: str
    details: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response from the CI/CD webhook endpoint."""
    version_id: str
    all_passed: bool
    checks: List[WebhookCheckResult]
