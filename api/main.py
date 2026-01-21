"""
FastAPI Main Application
RESTful API for AI Learning Assistant v2.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Import local modules
from .models import (
    UserCreate, UserLogin, UserResponse, Token,
    CourseCreate, CourseResponse, CourseListResponse, DayPlanResponse,
    MessageRequest, MessageResponse,
    QuizResponse, QuizQuestion, QuizAnswerRequest, QuizResultResponse,
    ProgressResponse, AnalyticsResponse,
    ResourceResponse, YouTubeVideo, GitHubRepo,
    HealthResponse, ErrorResponse
)
from .auth import (
    create_access_token, get_current_user, 
    hash_password, verify_password, TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .database import (
    init_db, get_db,
    create_user, get_user_by_username, get_user_by_id,
    create_course, get_course, get_user_courses, update_course,
    save_message, get_course_messages,
    update_analytics, get_analytics
)

# Import LangGraph app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import create_initial_state
from graph import create_app as create_langgraph_app


# ============================================================
# FastAPI App Configuration
# ============================================================

app = FastAPI(
    title="AI Learning Assistant API",
    description="""
    🎓 **AI-Powered Learning Platform API**
    
    Build personalized learning experiences with:
    - 📚 Custom curriculum generation
    - 🎬 YouTube video recommendations
    - 📖 Wikipedia summaries
    - 💻 GitHub repository suggestions
    - 📝 Knowledge-check quizzes
    - 📊 Progress tracking
    
    **Authentication:** JWT Bearer Token
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "User authentication endpoints"},
        {"name": "Courses", "description": "Course management"},
        {"name": "Chat", "description": "AI conversation"},
        {"name": "Quiz", "description": "Knowledge assessment"},
        {"name": "Progress", "description": "Learning analytics"},
        {"name": "Resources", "description": "External learning materials"},
        {"name": "Health", "description": "API status"}
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup Events
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("🚀 API Server started!")


# LangGraph app instance
langgraph_app = None

def get_langgraph():
    """Get or create LangGraph app instance."""
    global langgraph_app
    if langgraph_app is None:
        langgraph_app = create_langgraph_app("api_learning.db")
    return langgraph_app


# ============================================================
# Health Endpoints
# ============================================================

@app.get("/", tags=["Health"])
async def root():
    """API root - redirects to docs."""
    return {"message": "Welcome to AI Learning Assistant API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow()
    )


@app.get("/api/v1/status", tags=["Health"])
async def api_status():
    """Detailed API status."""
    return {
        "status": "operational",
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not configured",
            "youtube_api": "configured" if os.getenv("YOUTUBE_API_KEY") else "fallback mode",
            "github_api": "configured" if os.getenv("GITHUB_TOKEN") else "rate limited"
        }
    }


# ============================================================
# Authentication Endpoints
# ============================================================

@app.post("/api/v1/auth/register", response_model=UserResponse, tags=["Auth"])
async def register(user: UserCreate):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 chars)
    - **email**: Valid email address
    - **password**: Strong password (8+ chars)
    """
    # Check if user exists
    existing = get_user_by_username(user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    password_hash = hash_password(user.password)
    new_user = create_user(user.username, user.email, password_hash)
    
    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        created_at=datetime.utcnow()
    )


@app.post("/api/v1/auth/login", response_model=Token, tags=["Auth"])
async def login(credentials: UserLogin):
    """
    Login and receive JWT token.
    
    - **username**: Your username
    - **password**: Your password
    """
    user = get_user_by_username(credentials.username)
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create token
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.get("/api/v1/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user info."""
    user = get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
    )


# ============================================================
# Course Endpoints
# ============================================================

@app.post("/api/v1/courses", response_model=CourseResponse, tags=["Courses"])
async def create_new_course(
    course: CourseCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new learning course.
    
    The AI will generate a personalized curriculum based on:
    - **topic**: What you want to learn
    - **duration_days**: How many days (1-30)
    - **skill_level**: beginner, intermediate, or advanced
    """
    # Create course in database
    course_id = create_course(
        user_id=current_user.user_id,
        topic=course.topic,
        duration_days=course.duration_days,
        skill_level=course.skill_level
    )
    
    # Generate curriculum using LangGraph
    lg_app = get_langgraph()
    
    initial_state = create_initial_state(
        topic=course.topic,
        duration=course.duration_days,
        level=course.skill_level,
        user_id=current_user.user_id,
        session_id=course_id
    )
    initial_state["messages"] = [HumanMessage(content=f"Create a curriculum for: {course.topic}")]
    
    config = {"configurable": {"thread_id": course_id}}
    result = lg_app.invoke(initial_state, config)
    
    # Save curriculum
    curriculum = result.get("curriculum", [])
    update_course(course_id, curriculum=json.dumps(curriculum))
    
    return CourseResponse(
        id=course_id,
        topic=course.topic,
        duration_days=course.duration_days,
        skill_level=course.skill_level,
        curriculum=[DayPlanResponse(**day) for day in curriculum],
        current_day=1,
        completed_days=[],
        created_at=datetime.utcnow()
    )


@app.get("/api/v1/courses", response_model=CourseListResponse, tags=["Courses"])
async def list_courses(
    current_user: TokenData = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50)
):
    """List all courses for the current user."""
    courses = get_user_courses(current_user.user_id)
    
    course_responses = []
    for course in courses[skip:skip + limit]:
        curriculum = json.loads(course.get("curriculum", "[]") or "[]")
        completed_days = json.loads(course.get("completed_days", "[]") or "[]")
        
        course_responses.append(CourseResponse(
            id=course["id"],
            topic=course["topic"],
            duration_days=course["duration_days"],
            skill_level=course["skill_level"],
            curriculum=[DayPlanResponse(**day) for day in curriculum],
            current_day=course.get("current_day", 1),
            completed_days=completed_days,
            created_at=datetime.fromisoformat(course["created_at"]) if isinstance(course["created_at"], str) else course["created_at"]
        ))
    
    return CourseListResponse(courses=course_responses, total=len(courses))


@app.get("/api/v1/courses/{course_id}", response_model=CourseResponse, tags=["Courses"])
async def get_course_details(
    course_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get details of a specific course."""
    course = get_course(course_id)
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    curriculum = json.loads(course.get("curriculum", "[]") or "[]")
    completed_days = json.loads(course.get("completed_days", "[]") or "[]")
    
    return CourseResponse(
        id=course["id"],
        topic=course["topic"],
        duration_days=course["duration_days"],
        skill_level=course["skill_level"],
        curriculum=[DayPlanResponse(**day) for day in curriculum],
        current_day=course.get("current_day", 1),
        completed_days=completed_days,
        created_at=datetime.fromisoformat(course["created_at"]) if isinstance(course["created_at"], str) else course["created_at"]
    )


@app.post("/api/v1/courses/{course_id}/complete-day", tags=["Courses"])
async def complete_current_day(
    course_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Mark the current day as complete."""
    course = get_course(course_id)
    
    if not course or course["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    
    current_day = course.get("current_day", 1)
    completed_days = json.loads(course.get("completed_days", "[]") or "[]")
    
    if current_day not in completed_days:
        completed_days.append(current_day)
    
    curriculum = json.loads(course.get("curriculum", "[]") or "[]")
    next_day = current_day + 1 if current_day < len(curriculum) else current_day
    
    update_course(
        course_id,
        current_day=next_day,
        completed_days=json.dumps(completed_days)
    )
    
    return {
        "message": f"Day {current_day} completed!",
        "current_day": next_day,
        "total_completed": len(completed_days),
        "is_course_complete": len(completed_days) >= len(curriculum)
    }


# ============================================================
# Chat Endpoints
# ============================================================

@app.post("/api/v1/chat", response_model=MessageResponse, tags=["Chat"])
async def send_message(
    request: MessageRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Send a message to the AI assistant.
    
    - **message**: Your message or question
    - **course_id**: Optional - context of a specific course
    """
    lg_app = get_langgraph()
    
    # Get or create thread
    thread_id = request.course_id or str(uuid.uuid4())[:8]
    
    # Get existing state if course exists
    if request.course_id:
        course = get_course(request.course_id)
        if course:
            curriculum = json.loads(course.get("curriculum", "[]") or "[]")
            completed_days = json.loads(course.get("completed_days", "[]") or "[]")
            
            state = create_initial_state(
                topic=course["topic"],
                duration=course["duration_days"],
                level=course["skill_level"],
                user_id=current_user.user_id,
                session_id=thread_id
            )
            state["curriculum"] = curriculum
            state["curriculum_confirmed"] = True
            state["current_day"] = course.get("current_day", 1)
            state["completed_days"] = completed_days
        else:
            state = create_initial_state(user_id=current_user.user_id, session_id=thread_id)
    else:
        state = create_initial_state(user_id=current_user.user_id, session_id=thread_id)
    
    # Add user message
    state["messages"] = [HumanMessage(content=request.message)]
    
    # Invoke graph
    config = {"configurable": {"thread_id": thread_id}}
    result = lg_app.invoke(state, config)
    
    # Extract response
    messages = result.get("messages", [])
    response_text = "No response"
    if messages:
        last_msg = messages[-1]
        response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    
    # Save messages
    if request.course_id:
        save_message(request.course_id, current_user.user_id, "user", request.message)
        save_message(request.course_id, current_user.user_id, "assistant", response_text, result.get("next_action"))
    
    return MessageResponse(
        message=response_text,
        action=result.get("next_action", "unknown"),
        timestamp=datetime.utcnow()
    )


@app.get("/api/v1/courses/{course_id}/messages", tags=["Chat"])
async def get_chat_history(
    course_id: str,
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """Get chat history for a course."""
    course = get_course(course_id)
    
    if not course or course["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    
    messages = get_course_messages(course_id, limit)
    
    return {
        "course_id": course_id,
        "messages": messages,
        "total": len(messages)
    }


# ============================================================
# Quiz Endpoints
# ============================================================

@app.post("/api/v1/courses/{course_id}/quiz", response_model=QuizResponse, tags=["Quiz"])
async def generate_quiz(
    course_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Generate a quiz for the current course progress."""
    course = get_course(course_id)
    
    if not course or course["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    
    lg_app = get_langgraph()
    
    # Prepare state
    curriculum = json.loads(course.get("curriculum", "[]") or "[]")
    state = create_initial_state(
        topic=course["topic"],
        duration=course["duration_days"],
        level=course["skill_level"],
        user_id=current_user.user_id,
        session_id=course_id
    )
    state["curriculum"] = curriculum
    state["current_day"] = course.get("current_day", 1)
    state["messages"] = [HumanMessage(content="quiz")]
    
    # Generate quiz
    config = {"configurable": {"thread_id": f"{course_id}_quiz"}}
    result = lg_app.invoke(state, config)
    
    quiz_questions = result.get("quiz_questions", [])
    quiz_id = str(uuid.uuid4())[:8]
    
    # Format response (hide correct answers)
    formatted_questions = []
    for i, q in enumerate(quiz_questions):
        formatted_questions.append(QuizQuestion(
            question_number=i + 1,
            question=q.get("question", ""),
            options=q.get("options", [])
        ))
    
    # Store quiz for grading
    # In production, store in database
    
    return QuizResponse(
        quiz_id=quiz_id,
        questions=formatted_questions,
        total_questions=len(formatted_questions)
    )


@app.post("/api/v1/quiz/{quiz_id}/submit", response_model=QuizResultResponse, tags=["Quiz"])
async def submit_quiz_answers(
    quiz_id: str,
    answers: QuizAnswerRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Submit answers and get quiz results."""
    # In production, retrieve stored quiz questions
    # For now, return mock result
    
    score = 3  # Mock
    total = 5
    
    return QuizResultResponse(
        score=score,
        total=total,
        percentage=(score / total) * 100,
        feedback=[
            {"question": 1, "correct": True, "explanation": "Great!"},
            {"question": 2, "correct": True, "explanation": "Perfect!"},
            {"question": 3, "correct": True, "explanation": "Correct!"},
            {"question": 4, "correct": False, "explanation": "Review this topic."},
            {"question": 5, "correct": False, "explanation": "Try again!"}
        ]
    )


# ============================================================
# Progress Endpoints
# ============================================================

@app.get("/api/v1/courses/{course_id}/progress", response_model=ProgressResponse, tags=["Progress"])
async def get_course_progress(
    course_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get detailed progress for a course."""
    course = get_course(course_id)
    
    if not course or course["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    
    curriculum = json.loads(course.get("curriculum", "[]") or "[]")
    completed_days = json.loads(course.get("completed_days", "[]") or "[]")
    analytics = get_analytics(current_user.user_id)
    
    total_days = len(curriculum)
    days_completed = len(completed_days)
    
    # Calculate achievements
    achievements = []
    if days_completed >= 1:
        achievements.append("🏆 First Day")
    if days_completed >= 3:
        achievements.append("🔥 3-Day Streak")
    if days_completed >= 7:
        achievements.append("⭐ Week Warrior")
    if days_completed == total_days:
        achievements.append("🎓 Course Complete")
    
    return ProgressResponse(
        course_id=course_id,
        topic=course["topic"],
        days_completed=days_completed,
        total_days=total_days,
        completion_percentage=(days_completed / total_days * 100) if total_days > 0 else 0,
        quizzes_taken=analytics.get("quizzes_taken", 0),
        average_quiz_score=analytics.get("average_quiz_score", 0.0),
        questions_asked=analytics.get("questions_asked", 0),
        achievements=achievements
    )


@app.get("/api/v1/analytics", response_model=AnalyticsResponse, tags=["Progress"])
async def get_user_analytics(current_user: TokenData = Depends(get_current_user)):
    """Get overall learning analytics for the user."""
    courses = get_user_courses(current_user.user_id)
    analytics = get_analytics(current_user.user_id)
    
    total_completed = 0
    topics = []
    
    for course in courses:
        completed_days = json.loads(course.get("completed_days", "[]") or "[]")
        total_completed += len(completed_days)
        topics.append(course["topic"])
    
    return AnalyticsResponse(
        total_courses=len(courses),
        total_days_completed=total_completed,
        total_quizzes=analytics.get("quizzes_taken", 0),
        overall_average_score=analytics.get("average_quiz_score", 0.0),
        most_studied_topics=topics[:5],
        learning_streak=min(total_completed, 7)  # Simplified
    )


# ============================================================
# Resources Endpoints
# ============================================================

@app.get("/api/v1/courses/{course_id}/resources", response_model=ResourceResponse, tags=["Resources"])
async def get_course_resources(
    course_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get external learning resources for the current day."""
    course = get_course(course_id)
    
    if not course or course["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="Course not found")
    
    lg_app = get_langgraph()
    
    # Prepare state
    curriculum = json.loads(course.get("curriculum", "[]") or "[]")
    state = create_initial_state(
        topic=course["topic"],
        duration=course["duration_days"],
        level=course["skill_level"],
        user_id=current_user.user_id,
        session_id=course_id
    )
    state["curriculum"] = curriculum
    state["current_day"] = course.get("current_day", 1)
    state["messages"] = [HumanMessage(content="resources")]
    
    # Fetch resources
    config = {"configurable": {"thread_id": f"{course_id}_resources"}}
    result = lg_app.invoke(state, config)
    
    recommendations = result.get("content_recommendations", {})
    
    return ResourceResponse(
        youtube_videos=[
            YouTubeVideo(**v) for v in recommendations.get("youtube_videos", [])[:5]
        ],
        wikipedia_summary=recommendations.get("wikipedia_summary", "No summary available"),
        wikipedia_url=f"https://en.wikipedia.org/wiki/{course['topic'].replace(' ', '_')}",
        github_repos=[
            GitHubRepo(**r) for r in recommendations.get("github_repos", [])[:5]
        ]
    )


# ============================================================
# Error Handlers
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================
# Run with Uvicorn
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
