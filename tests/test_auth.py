"""
Tests for Authentication Service & Routes
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import engine, Base, SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestRegistration:
    def test_register_success(self):
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "student"

    def test_register_duplicate_username(self):
        client.post("/auth/register", json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "securepass123",
        })
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 409

    def test_register_duplicate_email(self):
        client.post("/auth/register", json={
            "username": "user1",
            "email": "same@example.com",
            "password": "securepass123",
        })
        response = client.post("/auth/register", json={
            "username": "user2",
            "email": "same@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 409


class TestLogin:
    def test_login_success(self):
        client.post("/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "mypassword",
        })
        response = client.post("/auth/login", json={
            "username": "loginuser",
            "password": "mypassword",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        client.post("/auth/register", json={
            "username": "loginuser2",
            "email": "login2@example.com",
            "password": "correctpass",
        })
        response = client.post("/auth/login", json={
            "username": "loginuser2",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        response = client.post("/auth/login", json={
            "username": "ghost",
            "password": "anything",
        })
        assert response.status_code == 401


class TestTokenRefresh:
    def test_refresh_token(self):
        client.post("/auth/register", json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "mypassword",
        })
        login_resp = client.post("/auth/login", json={
            "username": "refreshuser",
            "password": "mypassword",
        })
        refresh_token = login_resp.json()["refresh_token"]

        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestProtectedEndpoints:
    def test_access_without_token(self):
        response = client.get("/files/list")
        assert response.status_code == 403  # No bearer token

    def test_access_with_valid_token(self):
        client.post("/auth/register", json={
            "username": "protecteduser",
            "email": "protected@example.com",
            "password": "mypassword",
        })
        login_resp = client.post("/auth/login", json={
            "username": "protecteduser",
            "password": "mypassword",
        })
        token = login_resp.json()["access_token"]

        response = client.get(
            "/files/list",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_me_endpoint(self):
        client.post("/auth/register", json={
            "username": "meuser",
            "email": "me@example.com",
            "password": "mypassword",
        })
        login_resp = client.post("/auth/login", json={
            "username": "meuser",
            "password": "mypassword",
        })
        token = login_resp.json()["access_token"]

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == "meuser"
