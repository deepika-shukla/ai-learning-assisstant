"""
LangGraph Workflow Definition (v2)
Enhanced with 12 agents and external API integration.
"""

import os
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

try:
    from .state import LearningState, VALID_ACTIONS
    from .agents import (
        router_agent,
        curriculum_agent,
        confirm_curriculum_agent,
        todo_agent,
        progress_agent,
        complete_day_agent,
        qa_agent,
        quiz_agent,
        quiz_grader_agent,
        resources_agent,
        analytics_agent,
        unknown_agent
    )
except ImportError:
    from state import LearningState, VALID_ACTIONS
    from agents import (
        router_agent,
        curriculum_agent,
        confirm_curriculum_agent,
        todo_agent,
        progress_agent,
        complete_day_agent,
        qa_agent,
        quiz_agent,
        quiz_grader_agent,
        resources_agent,
        analytics_agent,
        unknown_agent
    )


# ============================================================
# Routing Logic
# ============================================================

def route_to_agent(state: LearningState) -> str:
    """
    Routes to appropriate agent based on next_action.
    This is the conditional edge function.
    
    INTERVIEW TIP: Node names must NOT match state keys in LangGraph v0.2+
    That's why we use "_node" suffix (e.g., "todos_node" not "todos")
    """
    action = state.get("next_action", "unknown")
    
    # Map actions to node names (with _node suffix to avoid state key conflicts)
    action_map = {
        "create_curriculum": "curriculum_node",
        "confirm_curriculum": "confirm_node",
        "show_todos": "todos_node",
        "mark_complete": "complete_node",
        "show_progress": "progress_node",
        "ask_question": "qa_node",
        "take_quiz": "quiz_node",
        "check_quiz": "grader_node",
        "get_resources": "resources_node",
        "show_analytics": "analytics_node",
        "unknown": "unknown_node"
    }
    
    return action_map.get(action, "unknown_node")


def should_continue(state: LearningState) -> Literal["router", "__end__"]:
    """
    Determines if conversation should continue.
    After each agent response, we end to wait for user input.
    """
    # Always end after processing to wait for next user input
    return END


# ============================================================
# Graph Builder
# ============================================================

def build_graph(checkpointer=None) -> StateGraph:
    """
    Builds the complete LangGraph workflow.
    
    Flow:
    START → router → [appropriate agent] → END
    
    Agents:
    1. curriculum - Creates learning plans
    2. confirm - Human-in-the-loop confirmation
    3. todos - Daily task breakdown
    4. complete - Marks days done
    5. progress - Shows stats
    6. qa - Answers questions
    7. quiz - Generates quizzes
    8. grader - Grades answers
    9. resources - External APIs (YouTube, Wiki, GitHub)
    10. analytics - Detailed analytics
    11. unknown - Fallback handler
    """
    
    # Initialize StateGraph with our state schema
    workflow = StateGraph(LearningState)
    
    # ========== Add Nodes ==========
    # INTERVIEW TIP: Node names use "_node" suffix to avoid conflicts with state keys
    # LangGraph v0.2+ doesn't allow node names that match TypedDict keys
    workflow.add_node("router_node", router_agent)
    workflow.add_node("curriculum_node", curriculum_agent)
    workflow.add_node("confirm_node", confirm_curriculum_agent)
    workflow.add_node("todos_node", todo_agent)
    workflow.add_node("complete_node", complete_day_agent)
    workflow.add_node("progress_node", progress_agent)
    workflow.add_node("qa_node", qa_agent)
    workflow.add_node("quiz_node", quiz_agent)
    workflow.add_node("grader_node", quiz_grader_agent)
    workflow.add_node("resources_node", resources_agent)
    workflow.add_node("analytics_node", analytics_agent)
    workflow.add_node("unknown_node", unknown_agent)
    
    # ========== Add Edges ==========
    
    # Entry point: START → router
    workflow.add_edge(START, "router_node")
    
    # Router → conditional routing to appropriate agent
    workflow.add_conditional_edges(
        "router_node",
        route_to_agent
    )
    
    # All agents → END (wait for next user input)
    for node in ["curriculum_node", "confirm_node", "todos_node", "complete_node", 
                 "progress_node", "qa_node", "quiz_node", "grader_node", "resources_node", 
                 "analytics_node", "unknown_node"]:
        workflow.add_edge(node, END)
    
    # ========== Compile ==========
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()


# ============================================================
# Persistence Setup
# ============================================================

def get_sqlite_checkpointer(db_path: str = "learning_assistant.db") -> SqliteSaver:
    """
    Creates SQLite-based checkpointer for state persistence.
    
    This enables:
    - Session restoration across restarts
    - Multiple user sessions
    - Complete state history
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def create_app(db_path: str = "learning_assistant.db"):
    """
    Creates the full application with persistence.
    
    Returns:
        Compiled LangGraph application with SQLite checkpointing
    """
    checkpointer = get_sqlite_checkpointer(db_path)
    return build_graph(checkpointer=checkpointer)


# ============================================================
# Graph Visualization
# ============================================================

def get_graph_diagram():
    """
    Returns ASCII representation of the graph for documentation.
    """
    return """
    ┌─────────────────────────────────────────────────────────────┐
    │                   AI Learning Assistant v2                   │
    │                    LangGraph Architecture                    │
    └─────────────────────────────────────────────────────────────┘
    
                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                              ┌─────────┐
                              │ ROUTER  │◄────── NLP Intent Classification
                              └────┬────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │ curriculum  │         │   confirm   │         │    todos    │
    │  (create)   │         │   (HITL)    │         │   (daily)   │
    └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
           │                       │                       │
           │     ┌─────────────────┼─────────────────┐     │
           │     │                 │                 │     │
           │     ▼                 ▼                 ▼     │
           │ ┌────────┐     ┌──────────┐     ┌──────────┐ │
           │ │  quiz  │     │ resources│     │ analytics│ │
           │ │        │     │  (APIs)  │     │          │ │
           │ └────┬───┘     └────┬─────┘     └────┬─────┘ │
           │      │              │                │       │
           │      ▼              │                │       │
           │ ┌────────┐          │                │       │
           │ │ grader │          │                │       │
           │ └────┬───┘          │                │       │
           │      │              │                │       │
           └──────┴──────────────┴────────────────┴───────┘
                                   │
                                   ▼
                              ┌─────────┐
                              │   END   │
                              └─────────┘
    
    ═══════════════════════════════════════════════════════════════
    
    Agents:
    ───────
    • router     - LLM-based intent classification
    • curriculum - Generates personalized learning plans
    • confirm    - Human-in-the-loop gate for curriculum
    • todos      - Creates daily task breakdowns
    • complete   - Marks days complete, advances progress
    • progress   - Shows learning progress & achievements
    • qa         - Answers topic questions with context
    • quiz       - Generates knowledge-check quizzes
    • grader     - Grades quiz answers with explanations
    • resources  - Fetches YouTube, Wikipedia, GitHub content
    • analytics  - Detailed learning statistics
    • unknown    - Fallback handler for unrecognized input
    
    External APIs:
    ──────────────
    • YouTube Data API v3 - Tutorial videos
    • Wikipedia REST API  - Topic summaries
    • GitHub REST API     - Code repositories
    """


if __name__ == "__main__":
    print(get_graph_diagram())
