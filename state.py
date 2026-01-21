"""
State definitions for AI Learning Assistant v2
Enhanced with external content and user management
"""

from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph.message import add_messages


# ============================================================
# Data Structures
# ============================================================

class DayPlan(TypedDict):
    """Represents one day in the learning curriculum."""
    day_number: int
    title: str
    topics: list[str]
    completed: bool


class ContentRecommendation(TypedDict):
    """External content for a topic."""
    youtube_videos: list[dict]    # [{title, url, thumbnail}]
    wikipedia_summary: str         # Topic summary
    github_repos: list[dict]       # [{name, url, stars, description}]


class QuizQuestion(TypedDict):
    """A single quiz question."""
    question: str
    options: list[str]             # ["a) ...", "b) ...", "c) ...", "d) ..."]
    correct_answer: str            # "a", "b", "c", or "d"
    explanation: str               # Why this is correct


# ============================================================
# Main State
# ============================================================

class LearningState(TypedDict):
    """
    Complete state that flows through the LangGraph workflow.
    Enhanced with external content and user tracking.
    """
    
    # ========== User Info ==========
    user_id: str                   # Unique user identifier
    session_id: str                # Current session
    
    # ========== Course Setup ==========
    topic: str
    duration_days: int
    skill_level: str               # "beginner", "intermediate", "advanced"
    
    # ========== Curriculum ==========
    curriculum: list[DayPlan]
    curriculum_confirmed: bool
    current_day: int
    completed_days: list[int]
    
    # ========== Current Session ==========
    todos: list[str]
    
    # ========== Quiz ==========
    quiz_questions: list[QuizQuestion]
    user_answers: list[str]
    quiz_score: int
    quiz_feedback: str
    
    # ========== External Content (NEW!) ==========
    content_recommendations: Optional[ContentRecommendation]
    
    # ========== Conversation ==========
    messages: Annotated[list, add_messages]
    next_action: str
    
    # ========== Analytics (NEW!) ==========
    total_time_spent: int          # Minutes
    questions_asked: int
    quizzes_taken: int
    average_quiz_score: float


# ============================================================
# Valid Actions
# ============================================================

VALID_ACTIONS = [
    "create_curriculum",
    "confirm_curriculum",
    "show_todos",
    "mark_complete",
    "show_progress",
    "ask_question",
    "take_quiz",
    "check_quiz",
    "get_resources",      # NEW: External content
    "show_analytics",     # NEW: User analytics
    "unknown"
]


# ============================================================
# Helper Functions
# ============================================================

def create_initial_state(
    topic: str = "",
    duration: int = 7,
    level: str = "beginner",
    user_id: str = "default",
    session_id: str = "default"
) -> dict:
    """Create a fresh state for a new user session."""
    return {
        "user_id": user_id,
        "session_id": session_id,
        "topic": topic,
        "duration_days": duration,
        "skill_level": level,
        "curriculum": [],
        "curriculum_confirmed": False,
        "current_day": 1,
        "completed_days": [],
        "todos": [],
        "quiz_questions": [],
        "user_answers": [],
        "quiz_score": 0,
        "quiz_feedback": "",
        "content_recommendations": None,
        "messages": [],
        "next_action": "",
        "total_time_spent": 0,
        "questions_asked": 0,
        "quizzes_taken": 0,
        "average_quiz_score": 0.0
    }
