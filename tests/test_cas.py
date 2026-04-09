"""
Tests for Content-Addressable Storage (CAS) Service
"""

import os
import shutil
import pytest

from app.services import cas as cas_service
from app.config import settings


# Use a temp CAS directory for tests
TEST_CAS_PATH = os.path.join(os.path.dirname(__file__), "_test_cas")


@pytest.fixture(autouse=True)
def setup_cas(monkeypatch):
    """Use a temporary CAS directory for each test."""
    monkeypatch.setattr(settings, "CAS_STORAGE_PATH", TEST_CAS_PATH)
    os.makedirs(TEST_CAS_PATH, exist_ok=True)
    yield
    if os.path.exists(TEST_CAS_PATH):
        shutil.rmtree(TEST_CAS_PATH)


class TestSHA256:
    def test_compute_hash(self):
        import io
        stream = io.BytesIO(b"hello world")
        hash_hex, data = cas_service.compute_sha256(stream)
        assert len(hash_hex) == 64
        assert data == b"hello world"

    def test_same_content_same_hash(self):
        import io
        hash1, _ = cas_service.compute_sha256(io.BytesIO(b"identical"))
        hash2, _ = cas_service.compute_sha256(io.BytesIO(b"identical"))
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        import io
        hash1, _ = cas_service.compute_sha256(io.BytesIO(b"content A"))
        hash2, _ = cas_service.compute_sha256(io.BytesIO(b"content B"))
        assert hash1 != hash2


class TestBlobStorage:
    def test_store_and_retrieve(self):
        data = b"test blob data"
        import io
        sha, _ = cas_service.compute_sha256(io.BytesIO(data))

        path = cas_service.store_blob(sha, data)
        assert os.path.isfile(path)

        retrieved = cas_service.retrieve_blob(path)
        assert retrieved == data

    def test_deduplication(self):
        data = b"duplicate content"
        import io
        sha, _ = cas_service.compute_sha256(io.BytesIO(data))

        path1 = cas_service.store_blob(sha, data)
        path2 = cas_service.store_blob(sha, data)
        assert path1 == path2

    def test_blob_exists(self):
        data = b"exists test"
        import io
        sha, _ = cas_service.compute_sha256(io.BytesIO(data))

        assert cas_service.blob_exists(sha) is False
        cas_service.store_blob(sha, data)
        assert cas_service.blob_exists(sha) is True

    def test_delete_blob(self):
        data = b"delete me"
        import io
        sha, _ = cas_service.compute_sha256(io.BytesIO(data))

        cas_service.store_blob(sha, data)
        assert cas_service.blob_exists(sha) is True

        cas_service.delete_blob(sha)
        assert cas_service.blob_exists(sha) is False

    def test_tiered_path_structure(self):
        data = b"path test"
        import io
        sha, _ = cas_service.compute_sha256(io.BytesIO(data))

        path = cas_service.store_blob(sha, data)
        # Should follow /xx/yy/full_hash pattern
        parts = path.replace(TEST_CAS_PATH + os.sep, "").split(os.sep)
        assert len(parts) == 3
        assert parts[0] == sha[:2]
        assert parts[1] == sha[2:4]
        assert parts[2] == sha


class TestValidation:
    def test_valid_file_type(self):
        assert cas_service.validate_file_type("hello.py") is True
        assert cas_service.validate_file_type("doc.pdf") is True

    def test_invalid_file_type(self):
        assert cas_service.validate_file_type("virus.exe") is False
        assert cas_service.validate_file_type("script.bat") is False

    def test_file_size_within_limit(self):
        assert cas_service.validate_file_size(1024) is True  # 1 KB

    def test_file_size_exceeds_limit(self):
        huge = settings.max_file_size_bytes + 1
        assert cas_service.validate_file_size(huge) is False
