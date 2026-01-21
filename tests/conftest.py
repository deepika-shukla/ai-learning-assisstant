"""
Pytest configuration and fixtures.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# Environment Setup
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set up test environment variables."""
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["DATABASE_URL"] = ":memory:"
    yield


# ============================================================
# Mock LLM Fixture
# ============================================================

@pytest.fixture
def mock_llm():
    """Mock LLM to avoid API calls during tests."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Test response")
    return mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI ChatCompletion."""
    with patch("langchain_openai.ChatOpenAI") as mock:
        instance = MagicMock()
        instance.invoke.return_value = MagicMock(content="create_curriculum")
        mock.return_value = instance
        yield mock


# ============================================================
# State Fixtures
# ============================================================

@pytest.fixture
def empty_state():
    """Create empty initial state."""
    from state import create_initial_state
    return create_initial_state()


@pytest.fixture
def state_with_curriculum():
    """Create state with curriculum."""
    from state import create_initial_state
    state = create_initial_state(
        topic="Python",
        duration=7,
        level="beginner"
    )
    state["curriculum"] = [
        {"day_number": 1, "title": "Day 1: Introduction", "topics": ["Variables", "Types"], "completed": False},
        {"day_number": 2, "title": "Day 2: Control Flow", "topics": ["If/Else", "Loops"], "completed": False},
    ]
    state["curriculum_confirmed"] = True
    return state


@pytest.fixture
def state_with_quiz():
    """Create state with active quiz."""
    from state import create_initial_state
    state = create_initial_state()
    state["quiz_questions"] = [
        {"question": "What is Python?", "options": ["a) Snake", "b) Language", "c) Tool", "d) Game"], "correct_answer": "b", "explanation": "Python is a programming language"},
        {"question": "What is 2+2?", "options": ["a) 3", "b) 4", "c) 5", "d) 6"], "correct_answer": "b", "explanation": "Basic math"}
    ]
    return state


# ============================================================
# API Test Fixtures
# ============================================================

@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    import os
    # Set test database before importing modules
    os.environ["DATABASE_URL"] = "test_api.db"
    
    from fastapi.testclient import TestClient
    from api.main import app
    from api.database import init_db
    
    # Initialize database
    init_db()
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    if os.path.exists("test_api.db"):
        os.remove("test_api.db")


@pytest.fixture
def auth_headers(api_client):
    """Get authentication headers for a test user."""
    # Register user
    api_client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    })
    
    # Login
    response = api_client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpassword123"
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    return {}


# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture
def test_db():
    """Create test database."""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Create tables
    conn.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE courses (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            topic TEXT,
            duration_days INTEGER,
            skill_level TEXT,
            curriculum TEXT,
            current_day INTEGER DEFAULT 1,
            completed_days TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    yield conn
    conn.close()


# ============================================================
# Service Fixtures
# ============================================================

@pytest.fixture
def mock_youtube_service():
    """Mock YouTube service."""
    with patch("services.youtube_service.YouTubeService") as mock:
        instance = MagicMock()
        instance.search_videos.return_value = [
            {"title": "Test Video", "url": "https://youtube.com/watch?v=test", "thumbnail": "", "channel": "Test"}
        ]
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_wikipedia_service():
    """Mock Wikipedia service."""
    with patch("services.wikipedia_service.WikipediaService") as mock:
        instance = MagicMock()
        instance.get_summary.return_value = {
            "title": "Test",
            "summary": "Test summary",
            "url": "https://wikipedia.org/wiki/Test"
        }
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_github_service():
    """Mock GitHub service."""
    with patch("services.github_service.GitHubService") as mock:
        instance = MagicMock()
        instance.search_repositories.return_value = [
            {"name": "test-repo", "url": "https://github.com/test/repo", "stars": 100, "description": "Test"}
        ]
        mock.return_value = instance
        yield mock
