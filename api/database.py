"""
Database setup for the API.
Uses SQLite for simplicity (can be swapped for PostgreSQL).
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
import uuid
from datetime import datetime


# ============================================================
# Database Configuration
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL", "api_database.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Database connection context manager.
    
    Usage:
        with get_db() as db:
            db.execute("SELECT * FROM users")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# Schema Initialization
# ============================================================

def init_db():
    """Initialize the database schema."""
    with get_db() as db:
        # Users table
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Courses table
        db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                skill_level TEXT NOT NULL,
                curriculum TEXT,  -- JSON
                current_day INTEGER DEFAULT 1,
                completed_days TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Chat messages table
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,  -- 'user' or 'assistant'
                content TEXT NOT NULL,
                action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Quiz attempts table
        db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                questions TEXT,  -- JSON
                answers TEXT,  -- JSON
                score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # User analytics table
        db.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                total_time_spent INTEGER DEFAULT 0,
                questions_asked INTEGER DEFAULT 0,
                quizzes_taken INTEGER DEFAULT 0,
                average_quiz_score REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes
        db.execute("CREATE INDEX IF NOT EXISTS idx_courses_user ON courses(user_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_messages_course ON messages(course_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_quiz_course ON quiz_attempts(course_id)")
        
        print("✅ Database initialized successfully")


# ============================================================
# User CRUD Operations
# ============================================================

def create_user(username: str, email: str, password_hash: str) -> dict:
    """Create a new user."""
    user_id = str(uuid.uuid4())
    
    with get_db() as db:
        db.execute(
            "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, username, email, password_hash)
        )
    
    return {"id": user_id, "username": username, "email": email}


def get_user_by_username(username: str) -> dict:
    """Get user by username."""
    with get_db() as db:
        cursor = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
    if row:
        return dict(row)
    return None


def get_user_by_id(user_id: str) -> dict:
    """Get user by ID."""
    with get_db() as db:
        cursor = db.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
    if row:
        return dict(row)
    return None


# ============================================================
# Course CRUD Operations
# ============================================================

def create_course(user_id: str, topic: str, duration_days: int, skill_level: str) -> str:
    """Create a new course."""
    course_id = str(uuid.uuid4())[:8]
    
    with get_db() as db:
        db.execute(
            """INSERT INTO courses 
               (id, user_id, topic, duration_days, skill_level, completed_days) 
               VALUES (?, ?, ?, ?, ?, '[]')""",
            (course_id, user_id, topic, duration_days, skill_level)
        )
    
    return course_id


def get_course(course_id: str) -> dict:
    """Get course by ID."""
    with get_db() as db:
        cursor = db.execute(
            "SELECT * FROM courses WHERE id = ?",
            (course_id,)
        )
        row = cursor.fetchone()
        
    if row:
        return dict(row)
    return None


def get_user_courses(user_id: str) -> list:
    """Get all courses for a user."""
    with get_db() as db:
        cursor = db.execute(
            "SELECT * FROM courses WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        
    return [dict(row) for row in rows]


def update_course(course_id: str, **kwargs) -> bool:
    """Update course fields."""
    if not kwargs:
        return False
    
    set_clauses = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [course_id]
    
    with get_db() as db:
        db.execute(
            f"UPDATE courses SET {set_clauses}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
    
    return True


# ============================================================
# Message CRUD Operations
# ============================================================

def save_message(course_id: str, user_id: str, role: str, content: str, action: str = None):
    """Save a chat message."""
    msg_id = str(uuid.uuid4())
    
    with get_db() as db:
        db.execute(
            "INSERT INTO messages (id, course_id, user_id, role, content, action) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, course_id, user_id, role, content, action)
        )
    
    return msg_id


def get_course_messages(course_id: str, limit: int = 50) -> list:
    """Get messages for a course."""
    with get_db() as db:
        cursor = db.execute(
            "SELECT * FROM messages WHERE course_id = ? ORDER BY created_at DESC LIMIT ?",
            (course_id, limit)
        )
        rows = cursor.fetchall()
        
    return [dict(row) for row in reversed(rows)]


# ============================================================
# Analytics Operations
# ============================================================

def update_analytics(user_id: str, **kwargs):
    """Update user analytics."""
    with get_db() as db:
        # Check if exists
        cursor = db.execute("SELECT id FROM analytics WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            if kwargs:
                set_clauses = ", ".join([f"{k} = {k} + ?" if k != "average_quiz_score" else f"{k} = ?" for k in kwargs.keys()])
                db.execute(
                    f"UPDATE analytics SET {set_clauses}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    list(kwargs.values()) + [user_id]
                )
        else:
            analytics_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO analytics (id, user_id) VALUES (?, ?)",
                (analytics_id, user_id)
            )


def get_analytics(user_id: str) -> dict:
    """Get user analytics."""
    with get_db() as db:
        cursor = db.execute(
            "SELECT * FROM analytics WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
    if row:
        return dict(row)
    return {
        "total_time_spent": 0,
        "questions_asked": 0,
        "quizzes_taken": 0,
        "average_quiz_score": 0.0
    }


if __name__ == "__main__":
    init_db()
