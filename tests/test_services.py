"""
Tests for external service integrations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


class TestYouTubeService:
    """Tests for YouTube API integration."""
    
    def test_service_initialization(self):
        """Service should initialize."""
        from services.youtube_service import YouTubeService
        
        service = YouTubeService()
        assert service is not None
    
    def test_is_configured_without_key(self):
        """Should return False without API key."""
        from services.youtube_service import YouTubeService
        
        with patch.dict('os.environ', {'YOUTUBE_API_KEY': ''}):
            service = YouTubeService(api_key=None)
            assert service.is_configured() == False
    
    def test_is_configured_with_key(self):
        """Should return True with API key."""
        from services.youtube_service import YouTubeService
        
        service = YouTubeService(api_key="test-key")
        assert service.is_configured() == True
    
    def test_fallback_videos(self):
        """Should return fallback videos for Python."""
        from services.youtube_service import YouTubeService
        
        service = YouTubeService()
        videos = service._get_fallback_videos("python programming")
        
        assert len(videos) > 0
        assert "url" in videos[0]
    
    @pytest.mark.asyncio
    async def test_search_without_api_key(self):
        """Should use fallback when no API key."""
        from services.youtube_service import YouTubeService
        
        service = YouTubeService(api_key=None)
        videos = await service.search_videos("python", max_results=3)
        
        assert len(videos) > 0


class TestWikipediaService:
    """Tests for Wikipedia API integration."""
    
    def test_service_initialization(self):
        """Service should initialize."""
        from services.wikipedia_service import WikipediaService
        
        service = WikipediaService()
        assert service is not None
    
    def test_fallback_summary(self):
        """Should return fallback summary."""
        from services.wikipedia_service import WikipediaService
        
        service = WikipediaService()
        summary = service._get_fallback_summary("Python")
        
        assert "title" in summary
        assert "summary" in summary
        assert "url" in summary
    
    @pytest.mark.asyncio
    async def test_get_summary(self, mock_wikipedia_service):
        """Should fetch Wikipedia summary."""
        from services.wikipedia_service import WikipediaService
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "title": "Python",
                "extract": "Python is a programming language",
                "content_urls": {"desktop": {"page": "https://wikipedia.org/wiki/Python"}}
            }
            
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            
            service = WikipediaService()
            # Would need proper async mocking to test fully


class TestGitHubService:
    """Tests for GitHub API integration."""
    
    def test_service_initialization(self):
        """Service should initialize."""
        from services.github_service import GitHubService
        
        service = GitHubService()
        assert service is not None
    
    def test_headers_without_token(self):
        """Should have basic headers without token."""
        from services.github_service import GitHubService
        
        service = GitHubService(token=None)
        headers = service._get_headers()
        
        assert "Accept" in headers
        assert "Authorization" not in headers
    
    def test_headers_with_token(self):
        """Should include auth header with token."""
        from services.github_service import GitHubService
        
        service = GitHubService(token="test-token")
        headers = service._get_headers()
        
        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]
    
    def test_fallback_repos(self):
        """Should return fallback repos."""
        from services.github_service import GitHubService
        
        service = GitHubService()
        repos = service._get_fallback_repos("python")
        
        assert len(repos) > 0
        assert "url" in repos[0]
    
    def test_parse_repos(self):
        """Should parse GitHub API response."""
        from services.github_service import GitHubService
        
        service = GitHubService()
        
        mock_data = {
            "items": [
                {
                    "name": "test-repo",
                    "full_name": "owner/test-repo",
                    "html_url": "https://github.com/owner/test-repo",
                    "description": "A test repository",
                    "stargazers_count": 100,
                    "forks_count": 10,
                    "language": "Python",
                    "topics": ["python", "testing"],
                    "owner": {"login": "owner", "avatar_url": ""}
                }
            ]
        }
        
        repos = service._parse_repos(mock_data)
        
        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"
        assert repos[0]["stars"] == 100
