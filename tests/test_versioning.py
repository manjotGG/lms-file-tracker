"""
Tests for Versioning Engine & File Routes
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import engine, Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _get_auth_token(username="testuser", email="test@example.com"):
    """Helper: register + login, return access token."""
    client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": "testpass123",
    })
    resp = client.post("/auth/login", json={
        "username": username,
        "password": "testpass123",
    })
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestFileUpload:
    def test_upload_file(self):
        token = _get_auth_token()
        file_content = b"print('hello world')"
        response = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("hello.py", io.BytesIO(file_content), "text/plain")},
            data={"comment": "Initial upload"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "hello.py"
        assert data["version_number"] == 1
        assert data["is_duplicate_content"] is False
        assert len(data["sha256_hash"]) == 64

    def test_upload_duplicate_content(self):
        token = _get_auth_token()
        file_content = b"same content"

        # First upload
        resp1 = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("file1.txt", io.BytesIO(file_content), "text/plain")},
        )
        assert resp1.status_code == 201

        # Same content, different filename (should de-duplicate)
        resp2 = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("file2.txt", io.BytesIO(file_content), "text/plain")},
        )
        assert resp2.status_code == 201
        assert resp2.json()["is_duplicate_content"] is True
        assert resp2.json()["sha256_hash"] == resp1.json()["sha256_hash"]

    def test_upload_new_version(self):
        token = _get_auth_token()

        # Version 1
        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("test.py", io.BytesIO(b"v1 content"), "text/plain")},
            data={"comment": "Version 1"},
        )

        # Version 2
        resp = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("test.py", io.BytesIO(b"v2 content"), "text/plain")},
            data={"comment": "Version 2"},
        )
        assert resp.status_code == 201
        assert resp.json()["version_number"] == 2


class TestVersionHistory:
    def test_get_versions(self):
        token = _get_auth_token()

        # Upload two versions
        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("test.py", io.BytesIO(b"v1"), "text/plain")},
            data={"comment": "First"},
        )
        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("test.py", io.BytesIO(b"v2"), "text/plain")},
            data={"comment": "Second"},
        )

        response = client.get(
            "/files/versions/test.py",
            headers=_auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_versions"] == 2
        assert data["versions"][0]["is_head"] is True  # newest first


class TestFileDownload:
    def test_download_file(self):
        token = _get_auth_token()
        content = b"download me"

        upload_resp = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("dl.txt", io.BytesIO(content), "text/plain")},
        )
        version_id = upload_resp.json()["version_id"]

        dl_resp = client.get(
            f"/files/download/{version_id}",
            headers=_auth_headers(token),
        )
        assert dl_resp.status_code == 200
        assert dl_resp.content == content


class TestDiff:
    def test_diff_between_versions(self):
        token = _get_auth_token()

        resp1 = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("diff.txt", io.BytesIO(b"line 1\nline 2\n"), "text/plain")},
        )
        resp2 = client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("diff.txt", io.BytesIO(b"line 1\nline 2 modified\nline 3\n"), "text/plain")},
        )

        v1 = resp1.json()["version_id"]
        v2 = resp2.json()["version_id"]

        diff_resp = client.get(
            f"/files/diff/{v1}/{v2}",
            headers=_auth_headers(token),
        )
        assert diff_resp.status_code == 200
        data = diff_resp.json()
        assert data["additions"] > 0 or data["deletions"] > 0


class TestDAG:
    def test_dag_structure(self):
        token = _get_auth_token()

        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("dag.py", io.BytesIO(b"v1"), "text/plain")},
        )
        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("dag.py", io.BytesIO(b"v2"), "text/plain")},
        )

        resp = client.get(
            "/files/dag/dag.py",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        dag = resp.json()["dag"]
        assert len(dag) == 1  # One root
        assert len(dag[0]["children"]) == 1  # One child


class TestFileList:
    def test_list_files(self):
        token = _get_auth_token()

        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("a.py", io.BytesIO(b"a"), "text/plain")},
        )
        client.post(
            "/files/upload",
            headers=_auth_headers(token),
            files={"file": ("b.py", io.BytesIO(b"b"), "text/plain")},
        )

        resp = client.get("/files/list", headers=_auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
