"""
Delta-Encoding Service
=======================
Computes diffs between file versions to enable:
  - Storage optimization (store only deltas)
  - Forensic visibility (instructors can see changes between submissions)
"""

import difflib
from typing import Optional

from sqlalchemy.orm import Session

from app.models.version import Version
from app.services import cas as cas_service


def compute_diff(
    db: Session,
    version_a_id: str,
    version_b_id: str,
) -> dict:
    """
    Compute a unified diff between two versions.

    Args:
        db: Database session
        version_a_id: Public version_id of the 'from' version
        version_b_id: Public version_id of the 'to' version

    Returns:
        Dict with diff_text, additions, deletions, and metadata.
    """
    # Fetch versions
    version_a = (
        db.query(Version)
        .filter(Version.version_id == version_a_id)
        .first()
    )
    version_b = (
        db.query(Version)
        .filter(Version.version_id == version_b_id)
        .first()
    )

    if not version_a or not version_b:
        raise ValueError("One or both version IDs not found")

    # Retrieve content from CAS
    content_a = cas_service.retrieve_blob(version_a.asset.cas_path)
    content_b = cas_service.retrieve_blob(version_b.asset.cas_path)

    # Attempt to decode as text for diff
    try:
        text_a = content_a.decode("utf-8").splitlines(keepends=True)
        text_b = content_b.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        # Binary files — provide a summary instead of line diff
        return {
            "version_a": version_a_id,
            "version_b": version_b_id,
            "filename": version_a.filename,
            "additions": 0,
            "deletions": 0,
            "diff_text": (
                f"Binary files differ.\n"
                f"  Version A: {len(content_a)} bytes (SHA: {version_a.asset.sha256_hash[:12]}…)\n"
                f"  Version B: {len(content_b)} bytes (SHA: {version_b.asset.sha256_hash[:12]}…)"
            ),
        }

    # Compute unified diff
    diff_lines = list(difflib.unified_diff(
        text_a,
        text_b,
        fromfile=f"{version_a.filename} (v: {version_a_id[:8]})",
        tofile=f"{version_b.filename} (v: {version_b_id[:8]})",
        lineterm="",
    ))

    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    return {
        "version_a": version_a_id,
        "version_b": version_b_id,
        "filename": version_a.filename,
        "additions": additions,
        "deletions": deletions,
        "diff_text": "\n".join(diff_lines),
    }


def get_diff_summary(
    db: Session,
    version_a_id: str,
    version_b_id: str,
) -> dict:
    """
    Quick summary of the diff without the full text.
    """
    result = compute_diff(db, version_a_id, version_b_id)
    return {
        "version_a": result["version_a"],
        "version_b": result["version_b"],
        "filename": result["filename"],
        "additions": result["additions"],
        "deletions": result["deletions"],
    }
