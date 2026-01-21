"""
API endpoint tests.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_root_endpoint(self, api_client):
        """Root endpoint should return welcome message."""
        response = api_client.get("/")
        
        assert response.status_code == 200
        assert "Welcome" in response.json()["message"]
    
    def test_health_endpoint(self, api_client):
        """Health endpoint should return healthy status."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_status_endpoint(self, api_client):
        """Status endpoint should return service status."""
        response = api_client.get("/api/v1/status")
        
        assert response.status_code == 200
        assert "services" in response.json()


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_register_success(self, api_client):
        """Should register new user successfully."""
        response = api_client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepassword123"
        })
        
        assert response.status_code == 200
        assert "id" in response.json()
        assert response.json()["username"] == "newuser"
    
    def test_register_duplicate_username(self, api_client):
        """Should reject duplicate username."""
        # First registration
        api_client.post("/api/v1/auth/register", json={
            "username": "duplicate",
            "email": "first@example.com",
            "password": "password123"
        })
        
        # Duplicate registration
        response = api_client.post("/api/v1/auth/register", json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 400
    
    def test_login_success(self, api_client):
        """Should login successfully."""
        # Register first
        api_client.post("/api/v1/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123"
        })
        
        # Login
        response = api_client.post("/api/v1/auth/login", json={
            "username": "loginuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_wrong_password(self, api_client):
        """Should reject wrong password."""
        # Register first
        api_client.post("/api/v1/auth/register", json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "correctpassword"
        })
        
        # Login with wrong password
        response = api_client.post("/api/v1/auth/login", json={
            "username": "wrongpass",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401


class TestCourseEndpoints:
    """Tests for course management endpoints."""
    
    def test_create_course_unauthorized(self, api_client):
        """Should reject unauthenticated course creation."""
        response = api_client.post("/api/v1/courses", json={
            "topic": "Python",
            "duration_days": 7,
            "skill_level": "beginner"
        })
        
        assert response.status_code == 401  # No auth header
    
    def test_list_courses_empty(self, api_client, auth_headers):
        """Should return empty list for new user."""
        response = api_client.get("/api/v1/courses", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestProtectedEndpoints:
    """Tests for protected endpoints."""
    
    def test_me_endpoint_authenticated(self, api_client, auth_headers):
        """Should return user info when authenticated."""
        response = api_client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        assert "username" in response.json()
    
    def test_me_endpoint_unauthenticated(self, api_client):
        """Should reject unauthenticated request."""
        response = api_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401


class TestValidation:
    """Tests for request validation."""
    
    def test_register_invalid_email(self, api_client):
        """Should reject invalid email."""
        response = api_client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "not-an-email",
            "password": "password123"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self, api_client):
        """Should reject short password."""
        response = api_client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "short"
        })
        
        assert response.status_code == 422
    
    def test_register_short_username(self, api_client):
        """Should reject short username."""
        response = api_client.post("/api/v1/auth/register", json={
            "username": "ab",
            "email": "valid@example.com",
            "password": "validpassword123"
        })
        
        assert response.status_code == 422
