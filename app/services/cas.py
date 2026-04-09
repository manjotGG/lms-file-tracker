"""
Content-Addressable Storage (CAS) Service
==========================================
Stores files using their SHA-256 hash as the address.
Uses a tiered directory structure: /ab/cd/abcdef1234...
to prevent filesystem performance degradation.

Abstracted so the backend can be swapped from local FS to MinIO/S3.
"""

import hashlib
import os
import shutil
from typing import BinaryIO, Tuple

from app.config import settings


# ── Hash Computation ─────────────────────────────────────────

def compute_sha256(stream: BinaryIO) -> Tuple[str, bytes]:
    """
    Compute the SHA-256 hash of a binary stream.
    Returns (hex_digest, raw_bytes) — the stream is consumed and
    the full content is returned for subsequent storage.
    """
    sha = hashlib.sha256()
    chunks = []
    while True:
        chunk = stream.read(8192)
        if not chunk:
            break
        sha.update(chunk)
        chunks.append(chunk)
    return sha.hexdigest(), b"".join(chunks)


# ── Path Helpers ─────────────────────────────────────────────

def _hash_to_path(sha256_hash: str) -> str:
    """
    Convert a hex hash to a tiered filesystem path.
    Example: 'af2c30de...' → '<CAS_ROOT>/af/2c/af2c30de...'
    """
    tier1 = sha256_hash[:2]
    tier2 = sha256_hash[2:4]
    return os.path.join(settings.CAS_STORAGE_PATH, tier1, tier2, sha256_hash)


# ── Storage Operations ───────────────────────────────────────

def blob_exists(sha256_hash: str) -> bool:
    """Check if a blob with this hash already exists in the CAS."""
    return os.path.isfile(_hash_to_path(sha256_hash))


def store_blob(sha256_hash: str, data: bytes) -> str:
    """
    Write raw bytes to the CAS under the hash-derived path.
    Returns the relative CAS path for database storage.

    If the blob already exists (de-duplication), this is a no-op
    and the existing path is returned.
    """
    cas_path = _hash_to_path(sha256_hash)
    if os.path.isfile(cas_path):
        return cas_path

    os.makedirs(os.path.dirname(cas_path), exist_ok=True)
    with open(cas_path, "wb") as f:
        f.write(data)
    return cas_path


def retrieve_blob(cas_path: str) -> bytes:
    """Read raw bytes from the CAS."""
    if not os.path.isfile(cas_path):
        raise FileNotFoundError(f"Blob not found at {cas_path}")
    with open(cas_path, "rb") as f:
        return f.read()


def delete_blob(sha256_hash: str) -> bool:
    """
    Remove a blob from the CAS (used during rollback).
    Returns True if the blob was deleted, False if it didn't exist.
    """
    cas_path = _hash_to_path(sha256_hash)
    if os.path.isfile(cas_path):
        os.remove(cas_path)
        return True
    return False


# ── Validation ───────────────────────────────────────────────

def validate_file_type(filename: str) -> bool:
    """Check if the file extension is in the allowed list."""
    _, ext = os.path.splitext(filename.lower())
    return ext in settings.allowed_file_types_list


def validate_file_size(size_bytes: int) -> bool:
    """Check if the file size is within the configured limit."""
    return size_bytes <= settings.max_file_size_bytes
