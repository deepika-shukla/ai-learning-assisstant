"""
Wikipedia API Integration
Fetches summaries and related topics for learning concepts.
"""

import httpx
from typing import Optional


class WikipediaService:
    """
    Service for fetching Wikipedia content.
    Uses the free Wikipedia REST API (no auth needed!).
    """
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    
    # Required headers for Wikipedia API
    HEADERS = {
        "User-Agent": "AILearningAssistant/1.0 (https://github.com/example; learning-assistant@example.com)"
    }
    
    async def get_summary(self, topic: str) -> dict:
        """
        Get a summary of a Wikipedia article.
        
        Args:
            topic: The topic to look up (e.g., "Machine Learning")
            
        Returns:
            Dictionary with title, summary, url, and related links
        """
        if not topic or not topic.strip():
            return self._get_fallback_summary("programming")
            
        try:
            # Clean topic for URL
            clean_topic = topic.strip().replace(" ", "_")
            url = f"{self.BASE_URL}/page/summary/{clean_topic}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.HEADERS, follow_redirects=True)
                
                if response.status_code == 404:
                    # Try search instead
                    return await self._search_and_get_summary(topic)
                    
                response.raise_for_status()
                data = response.json()
                
            return self._parse_summary(data)
            
        except Exception as e:
            print(f"Wikipedia API error: {e}")
            return self._get_fallback_summary(topic)
    
    async def _search_and_get_summary(self, query: str) -> dict:
        """Search Wikipedia and return the top result's summary."""
        search_url = f"https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params, headers=self.HEADERS)
            data = response.json()
            
        results = data.get("query", {}).get("search", [])
        if results:
            title = results[0]["title"]
            return await self.get_summary(title)
            
        return self._get_fallback_summary(query)
    
    async def get_related_topics(self, topic: str, limit: int = 5) -> list[str]:
        """
        Get related topics from a Wikipedia article.
        
        Args:
            topic: The main topic
            limit: Number of related topics to return
            
        Returns:
            List of related topic names
        """
        try:
            clean_topic = topic.replace(" ", "_")
            url = f"https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "titles": clean_topic,
                "prop": "links",
                "pllimit": limit * 2,  # Get extra, we'll filter
                "format": "json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, follow_redirects=True)
                data = response.json()
                
            pages = data.get("query", {}).get("pages", {})
            related = []
            
            for page_data in pages.values():
                links = page_data.get("links", [])
                for link in links:
                    title = link.get("title", "")
                    # Filter out meta pages
                    if not title.startswith(("Wikipedia:", "Help:", "Category:", "Template:")):
                        related.append(title)
                        if len(related) >= limit:
                            break
                            
            return related
            
        except Exception as e:
            print(f"Wikipedia related topics error: {e}")
            return []
    
    def _parse_summary(self, data: dict) -> dict:
        """Parse Wikipedia API response."""
        return {
            "title": data.get("title", "Unknown"),
            "summary": data.get("extract", "No summary available."),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "thumbnail": data.get("thumbnail", {}).get("source", ""),
            "description": data.get("description", "")
        }
    
    def _get_fallback_summary(self, topic: str) -> dict:
        """Return a fallback when API fails."""
        return {
            "title": topic,
            "summary": f"Learn about {topic} - a concept worth exploring in depth.",
            "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
            "thumbnail": "",
            "description": f"Search Wikipedia for more information about {topic}"
        }


# Synchronous wrapper
def get_wikipedia_summary(topic: str) -> dict:
    """Synchronous wrapper for the Wikipedia service."""
    import asyncio
    service = WikipediaService()
    return asyncio.run(service.get_summary(topic))


def get_related_topics(topic: str, limit: int = 5) -> list[str]:
    """Synchronous wrapper for related topics."""
    import asyncio
    service = WikipediaService()
    return asyncio.run(service.get_related_topics(topic, limit))
