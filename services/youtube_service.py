"""
YouTube Data API v3 Integration
Fetches relevant tutorial videos for learning topics.
"""

import os
import httpx
from typing import Optional


class YouTubeService:
    """
    Service for fetching YouTube videos related to learning topics.
    Uses YouTube Data API v3.
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with YouTube API key.
        Get yours at: https://console.cloud.google.com/
        """
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        
    def is_configured(self) -> bool:
        """Check if the API key is set."""
        return bool(self.api_key)
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 5,
        video_type: str = "tutorial"
    ) -> list[dict]:
        """
        Search for YouTube videos.
        
        Args:
            query: Search query (e.g., "Python basics for beginners")
            max_results: Number of videos to return (1-10)
            video_type: Type hint to add to query
            
        Returns:
            List of video dictionaries with title, url, thumbnail, channel
        """
        if not self.is_configured():
            return self._get_fallback_videos(query)
        
        try:
            params = {
                "part": "snippet",
                "q": f"{query} {video_type}",
                "type": "video",
                "maxResults": min(max_results, 10),
                "order": "relevance",
                "videoDuration": "medium",  # 4-20 minutes
                "key": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
            return self._parse_response(data)
            
        except Exception as e:
            print(f"YouTube API error: {e}")
            return self._get_fallback_videos(query)
    
    def _parse_response(self, data: dict) -> list[dict]:
        """Parse YouTube API response into clean format."""
        videos = []
        
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            
            videos.append({
                "title": snippet.get("title", "Untitled"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "channel": snippet.get("channelTitle", "Unknown"),
                "description": snippet.get("description", "")[:200],
                "published_at": snippet.get("publishedAt", "")
            })
            
        return videos
    
    def _get_fallback_videos(self, query: str) -> list[dict]:
        """
        Return curated fallback videos when API is not available.
        These are real, quality programming tutorials.
        """
        fallback_channels = {
            "python": [
                {
                    "title": "Python Tutorial - Full Course for Beginners",
                    "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
                    "thumbnail": "https://img.youtube.com/vi/_uQrJ0TkZlc/mqdefault.jpg",
                    "channel": "Programming with Mosh",
                    "description": "Comprehensive Python tutorial for beginners"
                },
                {
                    "title": "Python for Beginners - Full Course",
                    "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
                    "thumbnail": "https://img.youtube.com/vi/rfscVS0vtbw/mqdefault.jpg",
                    "channel": "freeCodeCamp",
                    "description": "Learn Python from scratch"
                }
            ],
            "javascript": [
                {
                    "title": "JavaScript Tutorial for Beginners",
                    "url": "https://www.youtube.com/watch?v=W6NZfCO5SIk",
                    "thumbnail": "https://img.youtube.com/vi/W6NZfCO5SIk/mqdefault.jpg",
                    "channel": "Programming with Mosh",
                    "description": "Master JavaScript basics"
                }
            ],
            "default": [
                {
                    "title": f"Search YouTube for: {query}",
                    "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+tutorial",
                    "thumbnail": "",
                    "channel": "YouTube Search",
                    "description": "Click to search for tutorials on YouTube"
                }
            ]
        }
        
        # Match by keyword
        query_lower = query.lower()
        for keyword, videos in fallback_channels.items():
            if keyword in query_lower:
                return videos
                
        return fallback_channels["default"]


# Synchronous wrapper for non-async contexts
def get_youtube_videos(query: str, max_results: int = 5) -> list[dict]:
    """Synchronous wrapper using httpx sync client."""
    import asyncio
    service = YouTubeService()
    return asyncio.run(service.search_videos(query, max_results))
