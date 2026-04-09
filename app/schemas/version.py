"""
Version Schemas — Request/Response models for versioning endpoints.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class VersionResponse(BaseModel):
    """Single version (commit) record."""
    id: int
    version_id: str
    filename: str
    sha256_hash: str
    size_bytes: int
    user_id: int
    username: str
    comment: Optional[str] = None
    is_head: bool
    created_at: datetime


class VersionHistoryResponse(BaseModel):
    """Version history for a file."""
    filename: str
    total_versions: int
    versions: List[VersionResponse]


class UploadResponse(BaseModel):
    """Response after a successful file upload."""
    version_id: str
    filename: str
    sha256_hash: str
    size_bytes: int
    version_number: int
    is_duplicate_content: bool
    message: str


class DiffLine(BaseModel):
    """A single line in a unified diff."""
    line_number_old: Optional[int] = None
    line_number_new: Optional[int] = None
    content: str
    change_type: str  # "add", "remove", "context"


class DiffResponse(BaseModel):
    """Diff between two versions."""
    version_a: str
    version_b: str
    filename: str
    additions: int
    deletions: int
    diff_text: str


class DagNodeResponse(BaseModel):
    """A node in the DAG tree representation."""
    version_id: str
    filename: str
    sha256_hash: str
    comment: Optional[str] = None
    is_head: bool
    created_at: datetime
    children: List["DagNodeResponse"] = []

    model_config = {"from_attributes": True}
