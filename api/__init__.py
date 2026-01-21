"""
FastAPI Backend for AI Learning Assistant v2
RESTful API with JWT authentication and versioning.
"""

from .main import app
from .auth import create_access_token, get_current_user, hash_password, verify_password
from .database import get_db, init_db
from .models import (
    UserCreate, UserLogin, UserResponse, Token,
    CourseCreate, CourseResponse,
    MessageRequest, MessageResponse,
    QuizResponse, ProgressResponse
)

__all__ = [
    "app",
    "create_access_token", "get_current_user",
    "get_db", "init_db"
]
