"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# ============================================================
# User Models
# ============================================================

class UserCreate(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., example="john@example.com")
    password: str = Field(..., min_length=8, example="securepassword123")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }


class UserLogin(BaseModel):
    """User login request."""
    username: str = Field(..., example="john_doe")
    password: str = Field(..., example="securepassword123")


class UserResponse(BaseModel):
    """User response (without password)."""
    id: str
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


# ============================================================
# Course Models
# ============================================================

class CourseCreate(BaseModel):
    """Course creation request."""
    topic: str = Field(..., min_length=3, max_length=200, example="Python Programming")
    duration_days: int = Field(default=7, ge=1, le=30, example=7)
    skill_level: str = Field(default="beginner", example="beginner")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Python Programming",
                "duration_days": 7,
                "skill_level": "beginner"
            }
        }


class DayPlanResponse(BaseModel):
    """Single day in curriculum."""
    day_number: int
    title: str
    topics: List[str]
    completed: bool


class CourseResponse(BaseModel):
    """Course response with curriculum."""
    id: str
    topic: str
    duration_days: int
    skill_level: str
    curriculum: List[DayPlanResponse]
    current_day: int
    completed_days: List[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """List of courses."""
    courses: List[CourseResponse]
    total: int


# ============================================================
# Message Models
# ============================================================

class MessageRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=2000)
    course_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What should I learn today?",
                "course_id": "abc123"
            }
        }


class MessageResponse(BaseModel):
    """Chat message response."""
    message: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Quiz Models
# ============================================================

class QuizQuestion(BaseModel):
    """Single quiz question."""
    question_number: int
    question: str
    options: List[str]


class QuizResponse(BaseModel):
    """Quiz response."""
    quiz_id: str
    questions: List[QuizQuestion]
    total_questions: int


class QuizAnswerRequest(BaseModel):
    """Quiz answer submission."""
    quiz_id: str
    answers: List[str] = Field(..., example=["a", "b", "c", "d", "a"])


class QuizResultResponse(BaseModel):
    """Quiz grading result."""
    score: int
    total: int
    percentage: float
    feedback: List[dict]


# ============================================================
# Progress Models
# ============================================================

class ProgressResponse(BaseModel):
    """User progress response."""
    course_id: str
    topic: str
    days_completed: int
    total_days: int
    completion_percentage: float
    quizzes_taken: int
    average_quiz_score: float
    questions_asked: int
    achievements: List[str]


class AnalyticsResponse(BaseModel):
    """Detailed analytics response."""
    total_courses: int
    total_days_completed: int
    total_quizzes: int
    overall_average_score: float
    most_studied_topics: List[str]
    learning_streak: int


# ============================================================
# Resource Models
# ============================================================

class YouTubeVideo(BaseModel):
    """YouTube video resource."""
    title: str
    url: str
    thumbnail: str
    channel: str


class GitHubRepo(BaseModel):
    """GitHub repository resource."""
    name: str
    url: str
    stars: int
    description: str


class ResourceResponse(BaseModel):
    """External resources response."""
    youtube_videos: List[YouTubeVideo]
    wikipedia_summary: str
    wikipedia_url: str
    github_repos: List[GitHubRepo]


# ============================================================
# Health & Status
# ============================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "2.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
