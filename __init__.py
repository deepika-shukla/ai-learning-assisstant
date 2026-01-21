"""
AI Learning Assistant v2
Multi-agent learning platform with external API integrations.
"""

from .state import LearningState, DayPlan, create_initial_state
from .graph import build_graph, create_app

__version__ = "2.0.0"
__all__ = ["LearningState", "DayPlan", "create_initial_state", "build_graph", "create_app"]
