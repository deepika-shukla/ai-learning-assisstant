"""
External API services for content recommendations.
"""

from .youtube_service import YouTubeService
from .wikipedia_service import WikipediaService
from .github_service import GitHubService

__all__ = ["YouTubeService", "WikipediaService", "GitHubService"]
